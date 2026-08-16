from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStaffingWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Staffing Test Customer",
                "company_type": "company",
                "email": "customer@example.com",
            }
        )
        cls.customer_contact = cls.env["res.partner"].create(
            {
                "name": "Customer Hiring Manager",
                "company_type": "person",
                "parent_id": cls.customer.id,
                "email": "hiring.manager@example.com",
            }
        )
        cls.candidate = cls.env["res.partner"].create(
            {
                "name": "Cloud Engineer Candidate",
                "company_type": "person",
                "email": "candidate@example.com",
            }
        )
        cls.opportunity = cls.env["crm.lead"].create(
            {
                "name": "Staff two cloud engineers",
                "type": "opportunity",
                "partner_id": cls.customer.id,
                "team_id": cls.env.ref("intrastack_crm.team_p1_staffing").id,
                "x_deal_classification": "staffing",
                "x_service_category": "cloud",
                "x_urgency_flag": "immediate",
                "x_source_tracking": "referral",
                "x_expected_value": 200000.0,
            }
        )

    def _create_requirement(self, positions=1):
        return self.env["intrastack.staffing.requirement"].create(
            {
                "name": "Senior Cloud Engineer",
                "job_title": "Senior Cloud Engineer",
                "lead_id": self.opportunity.id,
                "contact_id": self.customer_contact.id,
                "positions": positions,
                "start_date": fields.Date.today() + timedelta(days=30),
                "target_fill_date": fields.Date.today() + timedelta(days=20),
                "bill_rate": 180.0,
                "cost_rate": 120.0,
                "billing_unit": "hour",
            }
        )

    def _create_submission(self, requirement):
        return self.env["intrastack.staffing.submission"].create(
            {
                "requirement_id": requirement.id,
                "candidate_id": self.candidate.id,
                "source": "internal",
                "proposed_bill_rate": 180.0,
                "proposed_cost_rate": 120.0,
            }
        )

    def test_requirement_defaults_customer_and_margin(self):
        requirement = self._create_requirement(positions=2)

        self.assertEqual(requirement.partner_id, self.customer)
        self.assertEqual(requirement.company_id, self.opportunity.company_id)
        self.assertEqual(requirement.margin_amount, 60.0)
        self.assertAlmostEqual(requirement.margin_percent, 33.33, places=2)
        self.assertEqual(requirement.open_positions, 2)
        self.assertEqual(self.opportunity.staffing_requirement_count, 1)

    def test_end_to_end_staffing_flow(self):
        requirement = self._create_requirement()
        requirement.action_open()
        submission = self._create_submission(requirement)

        self.assertEqual(requirement.state, "sourcing")
        submission.action_start_screening()
        submission.action_submit()
        self.assertEqual(submission.state, "submitted")
        self.assertTrue(submission.submitted_on)

        interview = self.env["intrastack.staffing.interview"].create(
            {
                "submission_id": submission.id,
                "start_datetime": fields.Datetime.now() + timedelta(days=1),
                "duration_hours": 1.5,
                "interview_type": "technical",
                "mode": "video",
            }
        )
        self.assertEqual(interview.requirement_id, requirement)
        self.assertEqual(submission.state, "interview")
        self.assertEqual(requirement.state, "interview")

        interview.write(
            {
                "outcome": "strong_yes",
                "feedback": "Strong technical match.",
            }
        )
        interview.action_complete()
        self.assertEqual(interview.state, "completed")

        submission.action_move_to_offer()
        placement = self.env["intrastack.staffing.placement"].create(
            {
                "submission_id": submission.id,
                "start_date": fields.Date.today(),
                "contract_reference": "MSA-STAFF-001",
                "bill_rate": 180.0,
                "cost_rate": 120.0,
                "hours_per_week": 40.0,
            }
        )
        placement.action_confirm()

        self.assertEqual(placement.state, "confirmed")
        self.assertEqual(submission.state, "accepted")
        self.assertEqual(requirement.state, "filled")
        self.assertEqual(requirement.filled_positions, 1)
        self.assertEqual(requirement.open_positions, 0)
        self.assertEqual(placement.margin_amount, 60.0)
        self.assertEqual(placement.weekly_revenue, 7200.0)
        self.assertEqual(placement.weekly_margin, 2400.0)

        placement.action_activate()
        placement.action_complete()
        self.assertEqual(placement.state, "completed")
        self.assertTrue(placement.end_date)

    def test_interview_requires_outcome_before_completion(self):
        requirement = self._create_requirement()
        submission = self._create_submission(requirement)
        interview = self.env["intrastack.staffing.interview"].create(
            {
                "submission_id": submission.id,
                "start_datetime": fields.Datetime.now() + timedelta(days=1),
            }
        )

        with self.assertRaises(UserError):
            interview.action_complete()

    def test_placement_requires_profitable_rates_and_contract(self):
        requirement = self._create_requirement()
        submission = self._create_submission(requirement)

        with self.assertRaises(ValidationError):
            self.env["intrastack.staffing.placement"].create(
                {
                    "submission_id": submission.id,
                    "start_date": fields.Date.today(),
                    "bill_rate": 100.0,
                    "cost_rate": 120.0,
                }
            )

        placement = self.env["intrastack.staffing.placement"].create(
            {
                "submission_id": submission.id,
                "start_date": fields.Date.today(),
                "bill_rate": 180.0,
                "cost_rate": 120.0,
            }
        )
        with self.assertRaises(UserError):
            placement.action_confirm()
