from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class HrEmployee(models.Model):
    """Role-driven internal user onboarding for IntraStack operations."""

    _inherit = "hr.employee"

    intrastack_role = fields.Selection(
        selection=[
            ("sales_manager", "Sales Manager"),
            ("sales_executive", "Sales Executive"),
            ("recruiter", "Recruiter"),
            ("project_manager", "Project Manager"),
            ("consultant", "Consultant"),
        ],
        string="IntraStack Role",
        tracking=True,
        help="Controls the internal CRM, Sales, Project and Timesheet access bundle.",
    )

    intrastack_user_active = fields.Boolean(
        string="Access Active",
        related="user_id.active",
        readonly=True,
    )
    intrastack_invitation_pending = fields.Boolean(
        string="Invitation Pending",
        compute="_compute_intrastack_invitation_pending",
    )

    ROLE_GROUP_XMLIDS = {
        "sales_manager": "intrastack_crm.group_intrastack_sales_manager",
        "sales_executive": "intrastack_crm.group_intrastack_sales_executive",
        "recruiter": "intrastack_crm.group_intrastack_recruiter",
        "project_manager": "intrastack_crm.group_intrastack_project_manager",
        "consultant": "intrastack_crm.group_intrastack_consultant",
    }
    MANAGED_GROUP_XMLIDS = (
        "intrastack_crm.group_intrastack_sales_manager",
        "intrastack_crm.group_intrastack_sales_executive",
        "intrastack_crm.group_intrastack_recruiter",
        "intrastack_crm.group_intrastack_project_manager",
        "intrastack_crm.group_intrastack_consultant",
        "sales_team.group_sale_manager",
        "sales_team.group_sale_salesman_all_leads",
        "sales_team.group_sale_salesman",
        "sale_management.group_sale_order_template",
        "project.group_project_manager",
        "project.group_project_user",
        "hr_timesheet.group_hr_timesheet_approver",
        "hr_timesheet.group_hr_timesheet_user",
    )

    @api.depends("user_id", "user_id.partner_id.signup_token", "user_id.partner_id.signup_type")
    def _compute_intrastack_invitation_pending(self):
        for employee in self:
            partner = employee.user_id.partner_id
            employee.intrastack_invitation_pending = bool(
                employee.user_id and partner.signup_token and partner.signup_type
            )

    def _intrastack_role_group(self):
        self.ensure_one()
        xmlid = self.ROLE_GROUP_XMLIDS.get(self.intrastack_role)
        return self.env.ref(xmlid, raise_if_not_found=False) if xmlid else self.env["res.groups"]

    def _intrastack_managed_groups(self):
        groups = self.env["res.groups"]
        for xmlid in self.MANAGED_GROUP_XMLIDS:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                groups |= group
        return groups

    def _check_intrastack_onboarding(self):
        self.ensure_one()
        if not self.intrastack_role:
            raise ValidationError(_("Choose an IntraStack Role before activating access."))
        if not self.work_email:
            raise ValidationError(_("A work email is required to invite an internal user."))
        if self.user_id and self.user_id.share:
            raise ValidationError(_("The linked user is a portal user. IntraStack access requires an internal user."))

    def action_create_user(self):
        self.ensure_one()
        self._check_intrastack_onboarding()
        if self.user_id:
            raise ValidationError(_("This employee already has an active user. Use Sync IntraStack Access instead."))
        action = super().action_create_user()
        role_group = self._intrastack_role_group()
        context = dict(action.get("context") or {})
        context.update({
            "default_groups_id": [Command.set([role_group.id])],
            "default_share": False,
            "default_login": self.work_email,
        })
        action["context"] = context
        return action

    def action_sync_intrastack_access(self):
        if not self.env.user.has_group("hr.group_hr_manager") and not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Only an HR manager can activate or change IntraStack employee access."))
        for employee in self:
            employee._check_intrastack_onboarding()
            role_group = employee._intrastack_role_group()
            managed = employee._intrastack_managed_groups()
            user = employee.user_id.sudo()
            preserved = user.groups_id - managed
            user.write({
                "groups_id": [Command.set((preserved | role_group).ids)],
                "share": False,
                "active": True,
            })
        return True

    def action_resend_intrastack_invitation(self):
        for employee in self:
            employee._check_intrastack_onboarding()
            if not employee.user_id:
                raise UserError(_("Create the internal user before sending an invitation."))
            employee.user_id.sudo().action_reset_password()
        return True
