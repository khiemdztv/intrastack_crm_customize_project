from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCrmPipeline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({
            "name": "Pipeline Import Customer",
            "company_type": "company",
            "email": "pipeline@example.com",
        })

    def test_import_style_create_routes_by_classification(self):
        lead = self.env["crm.lead"].create({
            "name": "Imported opportunity",
            "type": "opportunity",
            "partner_id": self.customer.id,
            "x_deal_classification": "consulting",
            "x_service_category": "cloud",
            "x_urgency_flag": "short_term",
            "x_source_tracking": "other",
            "x_expected_value": 25000.0,
        })
        team = self.env.ref("intrastack_crm.team_p2_consulting")
        self.assertEqual(lead.team_id, team)
        self.assertEqual(lead.stage_id.team_id, team)
        self.assertEqual(lead.expected_revenue, 25000.0)

    def test_quick_create_without_custom_fields_remains_possible(self):
        lead = self.env["crm.lead"].create({
            "name": "Quick CRM lead",
            "type": "lead",
        })
        self.assertTrue(lead)

    def test_won_stage_requires_commercial_readiness(self):
        team = self.env.ref("intrastack_crm.team_p1_staffing")
        won_stage = self.env["crm.stage"].search([
            ("team_id", "=", team.id),
            ("is_won", "=", True),
        ], order="sequence", limit=1)
        with self.assertRaises(ValidationError):
            self.env["crm.lead"].create({
                "name": "Incomplete won opportunity",
                "type": "opportunity",
                "team_id": team.id,
                "stage_id": won_stage.id,
            })
