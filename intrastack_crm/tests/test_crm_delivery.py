# -*- coding: utf-8 -*-

from datetime import date

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCrmDelivery(TransactionCase):
    """End-to-end model tests for CRM, Sales and Project orchestration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "IntraStack Delivery Test Customer",
            "email": "delivery-test@example.com",
            "is_company": True,
        })
        cls.staffing_team = cls.env.ref("intrastack_crm.team_p1_staffing")
        cls.staffing_stage = cls.env["crm.stage"].search(
            [("team_id", "=", cls.staffing_team.id)],
            order="sequence, id",
            limit=1,
        )
        cls.lead = cls.env["crm.lead"].create({
            "name": "Staffing Delivery E2E",
            "type": "opportunity",
            "partner_id": cls.partner.id,
            "team_id": cls.staffing_team.id,
            "stage_id": cls.staffing_stage.id,
            "user_id": cls.env.user.id,
            "x_deal_classification": "staffing",
            "x_service_category": "cloud",
            "x_urgency_flag": "immediate",
            "x_source_tracking": "referral",
            "x_expected_value": 25000.0,
            "x_decision_maker": True,
            "intrastack_contract_start_date": date(2026, 9, 1),
            "intrastack_contract_end_date": date(2027, 8, 31),
            "intrastack_contract_renewal_date": date(2027, 7, 1),
        })

    def test_quotation_action_uses_service_template(self):
        template = self.env.ref("intrastack_crm.sale_template_staffing_rate_card")

        action = self.lead.action_new_quotation()

        self.assertEqual(action["context"]["default_opportunity_id"], self.lead.id)
        self.assertEqual(action["context"]["default_partner_id"], self.partner.id)
        self.assertEqual(action["context"]["default_sale_order_template_id"], template.id)
        self.assertEqual(
            action["context"]["default_intrastack_contract_start_date"],
            self.lead.intrastack_contract_start_date,
        )

    def test_ready_quotation_and_confirmation_create_one_project(self):
        template = self.env.ref("intrastack_crm.sale_template_staffing_rate_card")
        project_template = self.env.ref("intrastack_crm.project_template_staffing")

        action = self.lead.action_create_intrastack_quotation()
        quotation = self.env["sale.order"].browse(action["res_id"])

        self.assertEqual(quotation.state, "draft")
        self.assertEqual(quotation.opportunity_id, self.lead)
        self.assertEqual(quotation.sale_order_template_id, template)
        self.assertEqual(len(quotation.order_line), len(template.sale_order_template_line_ids))
        self.assertEqual(
            quotation.intrastack_contract_end_date,
            self.lead.intrastack_contract_end_date,
        )

        quotation.action_confirm()
        project = quotation.intrastack_delivery_project_id

        self.assertTrue(project)
        self.assertEqual(project.intrastack_opportunity_id, self.lead)
        self.assertEqual(project.intrastack_sale_order_id, quotation)
        self.assertEqual(project.partner_id, self.partner)
        self.assertEqual(project.date_start, self.lead.intrastack_contract_start_date)
        self.assertEqual(project.date, self.lead.intrastack_contract_end_date)
        self.assertTrue(project.allow_timesheets)
        self.assertEqual(self.lead.probability, 100)
        self.assertTrue(self.lead.stage_id.is_won)
        self.assertEqual(
            self.env["project.task"].search_count([("project_id", "=", project.id)]),
            self.env["project.task"].search_count([("project_id", "=", project_template.id)]),
        )

        same_project = self.lead._ensure_intrastack_delivery_project(quotation)
        self.assertEqual(same_project, project)
        self.assertEqual(
            self.env["project.project"].search_count([
                ("intrastack_opportunity_id", "=", self.lead.id),
            ]),
            1,
        )

    def test_confirmation_requires_contract_dates(self):
        action = self.lead.action_create_intrastack_quotation()
        quotation = self.env["sale.order"].browse(action["res_id"])
        self.lead.intrastack_contract_start_date = False

        with self.assertRaisesRegex(UserError, "Contract Start"):
            quotation.action_confirm()

        self.assertEqual(quotation.state, "draft")
        self.assertFalse(quotation.intrastack_delivery_project_id)
        self.assertNotEqual(self.lead.probability, 100)

    def test_confirmation_requires_positive_expected_value(self):
        action = self.lead.action_create_intrastack_quotation()
        quotation = self.env["sale.order"].browse(action["res_id"])
        self.lead.x_expected_value = 0

        with self.assertRaisesRegex(UserError, "Expected Value"):
            quotation.action_confirm()

        self.assertEqual(quotation.state, "draft")
        self.assertFalse(quotation.intrastack_delivery_project_id)

    def test_standard_sale_project_is_reused_without_duplicate(self):
        ProductTemplate = self.env["product.template"]
        if "project_template_id" not in ProductTemplate._fields:
            self.skipTest("sale_project is not installed")

        project_template = self.env.ref("intrastack_crm.project_template_staffing")
        product_template = ProductTemplate.create({
            "name": "Delivery Bridge Test Service",
            "type": "service",
            "list_price": 1000.0,
            "service_tracking": "project_only",
            "project_template_id": project_template.id,
        })
        quotation = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "opportunity_id": self.lead.id,
            "order_line": [Command.create({
                "product_id": product_template.product_variant_id.id,
                "product_uom_qty": 1.0,
            })],
        })

        quotation.action_confirm()

        project = quotation.intrastack_delivery_project_id
        self.assertTrue(project)
        self.assertIn(project, quotation.project_ids)
        self.assertEqual(project.intrastack_opportunity_id, self.lead)
        self.assertEqual(
            self.env["project.project"].search_count([
                ("intrastack_opportunity_id", "=", self.lead.id),
            ]),
            1,
        )

    def test_cloud_transformation_consulting_to_sow_to_project(self):
        consulting_team = self.env.ref("intrastack_crm.team_p2_consulting")
        first_stage = self.env["crm.stage"].search(
            [("team_id", "=", consulting_team.id)],
            order="sequence, id",
            limit=1,
        )
        opportunity = self.env["crm.lead"].create({
            "name": "Cloud Transformation Assessment",
            "type": "opportunity",
            "partner_id": self.partner.id,
            "team_id": consulting_team.id,
            "stage_id": first_stage.id,
            "user_id": self.env.user.id,
            "x_deal_classification": "consulting",
            "x_service_category": "cloud",
            "x_urgency_flag": "short_term",
            "x_source_tracking": "referral",
            "x_expected_value": 75000.0,
            "intrastack_contract_start_date": date(2026, 9, 1),
            "intrastack_contract_end_date": date(2027, 2, 28),
            "intrastack_contract_renewal_date": date(2027, 1, 15),
        })
        action = opportunity.action_create_intrastack_quotation()
        order = self.env["sale.order"].browse(action["res_id"])
        self.assertEqual(
            order.sale_order_template_id,
            self.env.ref("intrastack_crm.sale_template_consulting_sow"),
        )
        self.assertTrue(order.order_line)
        order.action_confirm()
        self.assertTrue(order.intrastack_delivery_project_id)
        self.assertEqual(
            order.intrastack_delivery_project_id.intrastack_opportunity_id,
            opportunity,
        )
        self.assertTrue(opportunity.stage_id.is_won)

    def test_contract_date_validation(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.lead.write({
                "intrastack_contract_end_date": date(2026, 8, 31),
            })

        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.lead.write({
                "intrastack_contract_renewal_date": date(2027, 9, 1),
            })
