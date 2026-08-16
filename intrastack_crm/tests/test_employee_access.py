from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEmployeeAccess(TransactionCase):
    def test_employee_requires_role_and_work_email(self):
        employee = self.env["hr.employee"].create({"name": "Unready Employee"})
        with self.assertRaises(ValidationError):
            employee.action_create_user()

    def test_employee_action_prefills_internal_role(self):
        employee = self.env["hr.employee"].create({
            "name": "Sales Manager",
            "work_email": "sales.manager@example.com",
            "intrastack_role": "sales_manager",
        })
        action = employee.action_create_user()
        self.assertFalse(action["context"]["default_share"])
        self.assertTrue(action["context"]["default_groups_id"])

    def test_sync_replaces_managed_access_with_role_bundle(self):
        employee = self.env["hr.employee"].create({
            "name": "IntraStack Recruiter",
            "work_email": "recruiter@example.com",
            "intrastack_role": "recruiter",
        })
        user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Recruiter User",
            "login": "recruiter@example.com",
            "email": "recruiter@example.com",
            "groups_id": [Command.set([
                self.env.ref("base.group_user").id,
                self.env.ref("sales_team.group_sale_manager").id,
            ])],
        })
        employee.user_id = user
        employee.action_sync_intrastack_access()
        self.assertFalse(user.share)
        self.assertIn(
            self.env.ref("intrastack_crm.group_intrastack_recruiter"),
            user.groups_id,
        )
        self.assertIn(
            self.env.ref("sales_team.group_sale_salesman_all_leads"),
            user.groups_id,
        )
        self.assertNotIn(self.env.ref("sales_team.group_sale_manager"), user.groups_id)
