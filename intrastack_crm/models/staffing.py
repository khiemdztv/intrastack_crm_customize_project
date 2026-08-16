"""Staffing delivery models for the IntraStack CRM module.

The models in this file intentionally stay within Odoo Community modules
(crm, contacts, project, sale_management and mail). They provide the minimum
traceable staffing workflow required by the BRD:

    requirement -> candidate submission -> interview -> offer -> placement

A CRM opportunity represents the commercial conversation while a requirement
represents one specific role or slot that recruiters can source and fill.
"""

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class StaffingRequirement(models.Model):
    """A staffing role or requirement opened for a CRM customer."""

    _name = "intrastack.staffing.requirement"
    _description = "Staffing Requirement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "target_fill_date asc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Requirement",
        required=True,
        tracking=True,
        index=True,
        help="Short name for the role or hiring requirement.",
    )
    active = fields.Boolean(default=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("sourcing", "Sourcing"),
            ("interview", "Interview"),
            ("offer", "Offer"),
            ("filled", "Filled"),
            ("on_hold", "On Hold"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    lead_id = fields.Many2one(
        "crm.lead",
        string="CRM Opportunity",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
        domain="[('type', '=', 'opportunity'), ('x_deal_classification', '=', 'staffing')]",
        help="Commercial opportunity that originated this requirement.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
        domain="[('is_company', '=', True)]",
    )
    contact_id = fields.Many2one(
        "res.partner",
        string="Customer Contact",
        ondelete="restrict",
        tracking=True,
        domain="[('commercial_partner_id', '=', partner_id)]",
        help="Operational contact for this specific requirement.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    job_title = fields.Char(string="Role / Job Title", required=True, tracking=True)
    description = fields.Html(string="Job Description", sanitize=True)
    skills = fields.Text(
        string="Required Skills",
        help="Technologies, certifications, clearance and experience required.",
    )
    positions = fields.Integer(
        string="Positions",
        default=1,
        required=True,
        tracking=True,
        help="Number of people required for this role.",
    )
    location = fields.Char(string="Location", tracking=True)
    work_arrangement = fields.Selection(
        [
            ("onsite", "On-site"),
            ("hybrid", "Hybrid"),
            ("remote", "Remote"),
        ],
        string="Work Arrangement",
        default="remote",
        required=True,
        tracking=True,
    )
    engagement_type = fields.Selection(
        [
            ("contract", "Contract"),
            ("contract_to_hire", "Contract to Hire"),
            ("permanent", "Permanent"),
        ],
        string="Engagement Type",
        default="contract",
        required=True,
        tracking=True,
    )
    start_date = fields.Date(string="Expected Start", tracking=True)
    target_fill_date = fields.Date(string="Target Fill Date", tracking=True)
    end_date = fields.Date(string="Expected End", tracking=True)
    recruiter_id = fields.Many2one(
        "res.users",
        string="Recruiter",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )
    bill_rate = fields.Monetary(
        string="Target Bill Rate",
        currency_field="currency_id",
        tracking=True,
        help="Customer-facing rate per billing unit.",
    )
    cost_rate = fields.Monetary(
        string="Target Cost Rate",
        currency_field="currency_id",
        tracking=True,
        help="Expected consultant/vendor cost per billing unit.",
    )
    billing_unit = fields.Selection(
        [
            ("hour", "Hour"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
            ("fixed", "Fixed Fee"),
        ],
        string="Rate Unit",
        default="hour",
        required=True,
        tracking=True,
    )
    margin_amount = fields.Monetary(
        string="Target Margin",
        currency_field="currency_id",
        compute="_compute_margin",
        store=True,
    )
    margin_percent = fields.Float(
        string="Target Margin %",
        compute="_compute_margin",
        store=True,
        digits=(16, 2),
    )
    notes = fields.Html(string="Internal Notes", sanitize=True)

    submission_ids = fields.One2many(
        "intrastack.staffing.submission",
        "requirement_id",
        string="Candidate Submissions",
    )
    interview_ids = fields.One2many(
        "intrastack.staffing.interview",
        "requirement_id",
        string="Requirement Interviews",
        readonly=True,
    )
    placement_ids = fields.One2many(
        "intrastack.staffing.placement",
        "requirement_id",
        string="Requirement Placements",
        readonly=True,
    )
    submission_count = fields.Integer(string="Submissions", compute="_compute_counts")
    interview_count = fields.Integer(string="Interviews", compute="_compute_counts")
    placement_count = fields.Integer(string="Placements", compute="_compute_counts")
    filled_positions = fields.Integer(string="Filled Positions", compute="_compute_counts")
    open_positions = fields.Integer(string="Open Positions", compute="_compute_counts")

    _sql_constraints = [
        (
            "positions_positive",
            "CHECK(positions > 0)",
            "The number of positions must be greater than zero.",
        ),
        (
            "rates_non_negative",
            "CHECK(bill_rate >= 0 AND cost_rate >= 0)",
            "Bill and cost rates cannot be negative.",
        ),
    ]

    @api.model
    def default_get(self, fields_list):
        """Populate customer and company when opened from a CRM opportunity."""
        values = super().default_get(fields_list)
        lead_id = self.env.context.get("default_lead_id")
        if lead_id:
            lead = self.env["crm.lead"].browse(lead_id).exists()
            if lead:
                if "partner_id" in fields_list and lead.partner_id:
                    values.setdefault("partner_id", lead.partner_id.id)
                if "company_id" in fields_list and lead.company_id:
                    values.setdefault("company_id", lead.company_id.id)
        return values

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for incoming in vals_list:
            vals = dict(incoming)
            if vals.get("lead_id"):
                lead = self.env["crm.lead"].browse(vals["lead_id"]).exists()
                if lead:
                    if not vals.get("partner_id") and lead.partner_id:
                        vals["partner_id"] = lead.partner_id.id
                    if not vals.get("company_id") and lead.company_id:
                        vals["company_id"] = lead.company_id.id
                    contract_start = getattr(
                        lead, "intrastack_contract_start_date", False
                    )
                    contract_end = getattr(
                        lead, "intrastack_contract_end_date", False
                    )
                    if contract_start and not vals.get("start_date"):
                        vals["start_date"] = contract_start
                    if contract_end and not vals.get("end_date"):
                        vals["end_date"] = contract_end
            prepared.append(vals)
        records = super().create(prepared)
        records._subscribe_recruiters()
        records._sync_from_placements()
        return records

    def write(self, vals):
        vals = dict(vals)
        if vals.get("lead_id") and "partner_id" not in vals:
            lead = self.env["crm.lead"].browse(vals["lead_id"]).exists()
            if lead and lead.partner_id:
                vals["partner_id"] = lead.partner_id.id
        result = super().write(vals)
        if "recruiter_id" in vals:
            self._subscribe_recruiters()
        return result

    def _subscribe_recruiters(self):
        for record in self:
            if record.recruiter_id.partner_id:
                record.message_subscribe(partner_ids=record.recruiter_id.partner_id.ids)

    @api.depends("bill_rate", "cost_rate")
    def _compute_margin(self):
        for record in self:
            record.margin_amount = (record.bill_rate or 0.0) - (record.cost_rate or 0.0)
            record.margin_percent = (
                record.margin_amount / record.bill_rate * 100.0
                if record.bill_rate
                else 0.0
            )

    @api.depends(
        "submission_ids",
        "interview_ids",
        "placement_ids",
        "placement_ids.state",
        "positions",
    )
    def _compute_counts(self):
        filled_states = {"confirmed", "active", "completed"}
        for record in self:
            placements = record.placement_ids
            filled = len(placements.filtered(lambda placement: placement.state in filled_states))
            record.submission_count = len(record.submission_ids)
            record.interview_count = len(record.interview_ids)
            record.placement_count = len(placements)
            record.filled_positions = filled
            record.open_positions = max(record.positions - filled, 0)

    @api.onchange("lead_id")
    def _onchange_lead_id(self):
        for record in self:
            if record.lead_id:
                if record.lead_id.partner_id:
                    record.partner_id = record.lead_id.partner_id
                if record.lead_id.company_id:
                    record.company_id = record.lead_id.company_id
                if not record.name or record.name == _("New"):
                    record.name = record.lead_id.name
                if not record.job_title:
                    record.job_title = record.lead_id.name
                contract_start = getattr(
                    record.lead_id,
                    "intrastack_contract_start_date",
                    False,
                )
                contract_end = getattr(
                    record.lead_id,
                    "intrastack_contract_end_date",
                    False,
                )
                if contract_start and not record.start_date:
                    record.start_date = contract_start
                if contract_end and not record.end_date:
                    record.end_date = contract_end

    @api.constrains("lead_id", "partner_id", "contact_id", "company_id")
    def _check_customer_link(self):
        for record in self:
            if record.lead_id:
                if record.lead_id.type != "opportunity":
                    raise ValidationError(_("A staffing requirement must link to an opportunity."))
                classification = getattr(record.lead_id, "x_deal_classification", False)
                if classification and classification != "staffing":
                    raise ValidationError(
                        _("The linked CRM opportunity must use the Staffing classification.")
                    )
                if (
                    record.lead_id.company_id
                    and record.company_id != record.lead_id.company_id
                ):
                    raise ValidationError(
                        _("The requirement company must match the opportunity company.")
                    )
                if (
                    record.lead_id.partner_id
                    and record.partner_id
                    and record.lead_id.partner_id.commercial_partner_id
                    != record.partner_id.commercial_partner_id
                ):
                    raise ValidationError(
                        _("The requirement customer must match the opportunity customer.")
                    )
            if (
                record.contact_id
                and record.partner_id
                and record.contact_id.commercial_partner_id
                != record.partner_id.commercial_partner_id
            ):
                raise ValidationError(
                    _("The customer contact must belong to the selected customer.")
                )

    @api.constrains("start_date", "target_fill_date", "end_date")
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.end_date < record.start_date:
                raise ValidationError(_("Expected end date cannot be before expected start date."))
            if (
                record.target_fill_date
                and record.start_date
                and record.target_fill_date > record.start_date
            ):
                raise ValidationError(
                    _("Target fill date should be on or before the expected start date.")
                )

    def _sync_from_placements(self):
        filled_states = ("confirmed", "active", "completed")
        for record in self:
            if record.state in ("cancelled", "on_hold"):
                continue
            filled = self.env["intrastack.staffing.placement"].search_count(
                [
                    ("requirement_id", "=", record.id),
                    ("state", "in", filled_states),
                ]
            )
            if filled >= record.positions:
                target = "filled"
            elif filled:
                target = "offer"
            elif record.state == "filled":
                target = "sourcing"
            else:
                continue
            if record.state != target:
                record.write({"state": target})

    def action_open(self):
        self.write({"state": "open"})
        return True

    def action_start_sourcing(self):
        self.write({"state": "sourcing"})
        return True

    def action_start_interview(self):
        self.write({"state": "interview"})
        return True

    def action_start_offer(self):
        self.write({"state": "offer"})
        return True

    def action_hold(self):
        self.write({"state": "on_hold"})
        return True

    def action_cancel(self):
        for record in self:
            if record.placement_ids.filtered(
                lambda placement: placement.state in ("confirmed", "active")
            ):
                raise UserError(
                    _(
                        "Cancel confirmed or active placements before cancelling this "
                        "requirement."
                    )
                )
        self.write({"state": "cancelled"})
        return True

    def action_reopen(self):
        self.write({"state": "open", "active": True})
        return True

    def _action_for(self, xml_id, domain, context=None):
        action = self.env.ref(xml_id).read()[0]
        action["domain"] = domain
        action["context"] = context or {}
        return action

    def action_view_submissions(self):
        self.ensure_one()
        return self._action_for(
            "intrastack_crm.action_staffing_submission",
            [("requirement_id", "=", self.id)],
            {"default_requirement_id": self.id},
        )

    def action_view_interviews(self):
        self.ensure_one()
        return self._action_for(
            "intrastack_crm.action_staffing_interview",
            [("requirement_id", "=", self.id)],
            {"default_requirement_id": self.id},
        )

    def action_view_placements(self):
        self.ensure_one()
        return self._action_for(
            "intrastack_crm.action_staffing_placement",
            [("requirement_id", "=", self.id)],
            {"default_requirement_id": self.id},
        )


class StaffingSubmission(models.Model):
    """A candidate sent for consideration against one requirement."""

    _name = "intrastack.staffing.submission"
    _description = "Staffing Candidate Submission"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "submitted_on desc, id desc"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True, index=True)
    active = fields.Boolean(default=True)
    requirement_id = fields.Many2one(
        "intrastack.staffing.requirement",
        string="Requirement",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    candidate_id = fields.Many2one(
        "res.partner",
        string="Candidate",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
        domain="[('is_company', '=', False)]",
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="requirement_id.partner_id",
        store=True,
        readonly=True,
    )
    lead_id = fields.Many2one(
        "crm.lead",
        string="CRM Opportunity",
        related="requirement_id.lead_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="requirement_id.company_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="requirement_id.currency_id",
        store=True,
        readonly=True,
    )
    recruiter_id = fields.Many2one(
        "res.users",
        string="Recruiter",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("sourcing", "Sourcing"),
            ("screening", "Screening"),
            ("submitted", "Submitted"),
            ("interview", "Interview"),
            ("offer", "Offer"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
        ],
        string="Status",
        default="sourcing",
        required=True,
        tracking=True,
        index=True,
    )
    source = fields.Selection(
        [
            ("internal", "Internal Talent Pool"),
            ("referral", "Referral"),
            ("vendor", "Recruiter / Vendor"),
            ("linkedin", "LinkedIn"),
            ("job_board", "Job Board"),
            ("other", "Other"),
        ],
        string="Source",
        default="internal",
        required=True,
        tracking=True,
    )
    vendor_id = fields.Many2one(
        "res.partner",
        string="Recruiter Vendor",
        ondelete="restrict",
        domain="[('is_company', '=', True)]",
        tracking=True,
    )
    submitted_on = fields.Date(string="Submitted On", tracking=True)
    availability_date = fields.Date(string="Available From", tracking=True)
    proposed_bill_rate = fields.Monetary(
        string="Proposed Bill Rate",
        currency_field="currency_id",
        tracking=True,
    )
    proposed_cost_rate = fields.Monetary(
        string="Proposed Cost Rate",
        currency_field="currency_id",
        tracking=True,
    )
    margin_amount = fields.Monetary(
        string="Margin",
        currency_field="currency_id",
        compute="_compute_margin",
        store=True,
    )
    margin_percent = fields.Float(
        string="Margin %",
        compute="_compute_margin",
        store=True,
        digits=(16, 2),
    )
    screening_summary = fields.Text(string="Screening Summary")
    notes = fields.Html(string="Internal Notes", sanitize=True)
    resume_file = fields.Binary(
        string="Resume / CV",
        attachment=True,
        help="Candidate resume. Access follows the submission record permissions.",
    )
    resume_filename = fields.Char(string="Resume Filename")
    interview_ids = fields.One2many(
        "intrastack.staffing.interview",
        "submission_id",
        string="Submission Interviews",
        readonly=True,
    )
    placement_ids = fields.One2many(
        "intrastack.staffing.placement",
        "submission_id",
        string="Submission Placements",
        readonly=True,
    )
    interview_count = fields.Integer(compute="_compute_counts", string="Interviews")
    placement_count = fields.Integer(compute="_compute_counts", string="Placements")

    _sql_constraints = [
        (
            "requirement_candidate_unique",
            "UNIQUE(requirement_id, candidate_id)",
            "A candidate can only be submitted once for the same requirement.",
        ),
        (
            "submission_rates_non_negative",
            "CHECK(proposed_bill_rate >= 0 AND proposed_cost_rate >= 0)",
            "Proposed rates cannot be negative.",
        ),
    ]

    @api.depends("candidate_id.name", "requirement_id.name")
    def _compute_name(self):
        for record in self:
            if record.candidate_id and record.requirement_id:
                record.name = _("%s - %s") % (
                    record.candidate_id.display_name,
                    record.requirement_id.display_name,
                )
            elif record.candidate_id:
                record.name = record.candidate_id.display_name
            else:
                record.name = _("Candidate Submission")

    @api.depends("proposed_bill_rate", "proposed_cost_rate")
    def _compute_margin(self):
        for record in self:
            record.margin_amount = (
                record.proposed_bill_rate or 0.0
            ) - (record.proposed_cost_rate or 0.0)
            record.margin_percent = (
                record.margin_amount / record.proposed_bill_rate * 100.0
                if record.proposed_bill_rate
                else 0.0
            )

    @api.depends("interview_ids", "placement_ids")
    def _compute_counts(self):
        for record in self:
            record.interview_count = len(record.interview_ids)
            record.placement_count = len(record.placement_ids)

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for incoming in vals_list:
            vals = dict(incoming)
            if vals.get("requirement_id") and not vals.get("recruiter_id"):
                requirement = self.env["intrastack.staffing.requirement"].browse(
                    vals["requirement_id"]
                )
                if requirement.recruiter_id:
                    vals["recruiter_id"] = requirement.recruiter_id.id
            prepared.append(vals)
        records = super().create(prepared)
        to_source = records.filtered(
            lambda record: record.requirement_id.state in ("draft", "open")
        )
        if to_source:
            to_source.mapped("requirement_id").write({"state": "sourcing"})
        records._subscribe_recruiters()
        return records

    def _subscribe_recruiters(self):
        for record in self:
            if record.recruiter_id.partner_id:
                record.message_subscribe(partner_ids=record.recruiter_id.partner_id.ids)

    @api.onchange("requirement_id")
    def _onchange_requirement_id(self):
        for record in self:
            if record.requirement_id:
                if not record.recruiter_id or record.recruiter_id == self.env.user:
                    record.recruiter_id = record.requirement_id.recruiter_id
                if not record.proposed_bill_rate:
                    record.proposed_bill_rate = record.requirement_id.bill_rate
                if not record.proposed_cost_rate:
                    record.proposed_cost_rate = record.requirement_id.cost_rate

    @api.constrains("requirement_id", "candidate_id")
    def _check_candidate(self):
        for record in self:
            if record.candidate_id and record.candidate_id.company_type != "person":
                raise ValidationError(
                    _("A staffing submission must point to an individual candidate.")
                )
            if record.requirement_id.state == "cancelled":
                raise ValidationError(
                    _("A candidate cannot be submitted to a cancelled requirement.")
                )

    @api.constrains("vendor_id", "source")
    def _check_vendor(self):
        for record in self:
            if record.source == "vendor" and not record.vendor_id:
                raise ValidationError(
                    _("Select a recruiter/vendor when the source is Vendor.")
                )

    @api.constrains("proposed_bill_rate", "proposed_cost_rate")
    def _check_rates(self):
        for record in self:
            if (
                record.proposed_bill_rate
                and record.proposed_cost_rate
                and record.proposed_bill_rate < record.proposed_cost_rate
            ):
                raise ValidationError(
                    _("Proposed bill rate cannot be below proposed cost rate.")
                )

    def action_start_screening(self):
        self.write({"state": "screening"})
        return True

    def action_submit(self):
        for record in self:
            if record.state in ("rejected", "withdrawn"):
                raise UserError(
                    _("Rejected or withdrawn candidates must be reopened first.")
                )
        self.write(
            {"state": "submitted", "submitted_on": fields.Date.context_today(self)}
        )
        self.mapped("requirement_id").filtered(
            lambda requirement: requirement.state in ("draft", "open", "sourcing")
        ).write({"state": "sourcing"})
        return True

    def action_move_to_interview(self):
        self.write({"state": "interview"})
        self.mapped("requirement_id").filtered(
            lambda requirement: requirement.state
            not in ("filled", "cancelled", "on_hold")
        ).write({"state": "interview"})
        return True

    def action_move_to_offer(self):
        self.write({"state": "offer"})
        self.mapped("requirement_id").filtered(
            lambda requirement: requirement.state
            not in ("filled", "cancelled", "on_hold")
        ).write({"state": "offer"})
        return True

    def action_accept(self):
        self.write({"state": "accepted"})
        return True

    def action_reject(self):
        if self.filtered(
            lambda record: record.placement_ids.filtered(
                lambda placement: placement.state in ("confirmed", "active")
            )
        ):
            raise UserError(
                _("A candidate with a confirmed placement cannot be rejected.")
            )
        self.write({"state": "rejected"})
        return True

    def action_withdraw(self):
        if self.filtered(
            lambda record: record.placement_ids.filtered(
                lambda placement: placement.state in ("confirmed", "active")
            )
        ):
            raise UserError(
                _("Cancel the placement before withdrawing this candidate.")
            )
        self.write({"state": "withdrawn"})
        return True

    def action_reopen(self):
        self.write({"state": "screening"})
        return True

    def _action_for(self, xml_id, domain, context=None):
        action = self.env.ref(xml_id).read()[0]
        action["domain"] = domain
        action["context"] = context or {}
        return action

    def action_view_interviews(self):
        self.ensure_one()
        return self._action_for(
            "intrastack_crm.action_staffing_interview",
            [("submission_id", "=", self.id)],
            {
                "default_submission_id": self.id,
                "default_requirement_id": self.requirement_id.id,
            },
        )

    def action_view_placements(self):
        self.ensure_one()
        return self._action_for(
            "intrastack_crm.action_staffing_placement",
            [("submission_id", "=", self.id)],
            {
                "default_submission_id": self.id,
                "default_requirement_id": self.requirement_id.id,
            },
        )


class StaffingInterview(models.Model):
    """A scheduled interview and its structured outcome."""

    _name = "intrastack.staffing.interview"
    _description = "Staffing Interview"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_datetime desc, id desc"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True, index=True)
    active = fields.Boolean(default=True)
    requirement_id = fields.Many2one(
        "intrastack.staffing.requirement",
        string="Requirement",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    submission_id = fields.Many2one(
        "intrastack.staffing.submission",
        string="Candidate Submission",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
        domain="[('requirement_id', '=', requirement_id), ('state', 'not in', ['rejected', 'withdrawn'])]",
    )
    candidate_id = fields.Many2one(
        "res.partner",
        string="Candidate",
        related="submission_id.candidate_id",
        store=True,
        readonly=True,
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="requirement_id.partner_id",
        store=True,
        readonly=True,
    )
    interviewer_ids = fields.Many2many(
        "res.users",
        "intrastack_staffing_interview_user_rel",
        "interview_id",
        "user_id",
        string="Internal Interviewers",
        tracking=True,
    )
    client_interviewer_id = fields.Many2one(
        "res.partner",
        string="Client Interviewer",
        ondelete="restrict",
        domain="[('commercial_partner_id', '=', customer_id)]",
        tracking=True,
    )
    interview_type = fields.Selection(
        [
            ("screening", "Recruiter Screening"),
            ("technical", "Technical"),
            ("client", "Client"),
            ("managerial", "Managerial"),
            ("final", "Final"),
        ],
        string="Interview Round",
        default="screening",
        required=True,
        tracking=True,
    )
    mode = fields.Selection(
        [
            ("video", "Video Call"),
            ("phone", "Phone"),
            ("onsite", "On-site"),
        ],
        string="Mode",
        default="video",
        required=True,
        tracking=True,
    )
    start_datetime = fields.Datetime(string="Start", required=True, tracking=True)
    duration_hours = fields.Float(
        string="Duration (hours)",
        default=1.0,
        required=True,
        tracking=True,
    )
    end_datetime = fields.Datetime(
        string="End",
        compute="_compute_end_datetime",
        store=True,
    )
    meeting_link = fields.Char(string="Meeting Link")
    location = fields.Char(string="Location")
    state = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("no_show", "No Show"),
        ],
        string="Status",
        default="scheduled",
        required=True,
        tracking=True,
        index=True,
    )
    outcome = fields.Selection(
        [
            ("pending", "Pending"),
            ("strong_yes", "Strong Yes"),
            ("yes", "Yes"),
            ("no", "No"),
            ("strong_no", "Strong No"),
        ],
        string="Outcome",
        default="pending",
        required=True,
        tracking=True,
    )
    feedback = fields.Text(string="Interview Feedback")
    notes = fields.Html(string="Internal Notes", sanitize=True)

    @api.depends("candidate_id.name", "interview_type", "start_datetime")
    def _compute_name(self):
        labels = dict(self._fields["interview_type"].selection)
        for record in self:
            candidate = record.candidate_id.display_name or _("Candidate")
            round_name = labels.get(record.interview_type, _("Interview"))
            date_text = (
                fields.Datetime.to_string(record.start_datetime)
                if record.start_datetime
                else _("Unscheduled")
            )
            record.name = _("%s - %s - %s") % (
                candidate,
                round_name,
                date_text,
            )

    @api.depends("start_datetime", "duration_hours")
    def _compute_end_datetime(self):
        for record in self:
            if record.start_datetime:
                start = fields.Datetime.to_datetime(record.start_datetime)
                record.end_datetime = start + timedelta(
                    hours=record.duration_hours or 0.0
                )
            else:
                record.end_datetime = False

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for incoming in vals_list:
            vals = dict(incoming)
            if vals.get("submission_id") and not vals.get("requirement_id"):
                submission = self.env["intrastack.staffing.submission"].browse(
                    vals["submission_id"]
                ).exists()
                if submission:
                    vals["requirement_id"] = submission.requirement_id.id
            prepared.append(vals)
        records = super().create(prepared)
        records.filtered(
            lambda interview: interview.state != "cancelled"
        )._mark_pipeline_interview()
        return records

    def _mark_pipeline_interview(self):
        submissions = self.mapped("submission_id").filtered(
            lambda submission: submission.state
            not in ("rejected", "withdrawn", "accepted")
        )
        if submissions:
            submissions.write({"state": "interview"})
        requirements = self.mapped("requirement_id").filtered(
            lambda requirement: requirement.state
            not in ("filled", "cancelled", "on_hold")
        )
        if requirements:
            requirements.write({"state": "interview"})

    @api.constrains("requirement_id", "submission_id", "client_interviewer_id")
    def _check_links(self):
        for record in self:
            if (
                record.submission_id
                and record.requirement_id != record.submission_id.requirement_id
            ):
                raise ValidationError(
                    _(
                        "The interview requirement must match the candidate "
                        "submission requirement."
                    )
                )
            if (
                record.client_interviewer_id
                and record.customer_id
                and record.client_interviewer_id.commercial_partner_id
                != record.customer_id.commercial_partner_id
            ):
                raise ValidationError(
                    _("The client interviewer must belong to the customer.")
                )

    @api.constrains("duration_hours")
    def _check_duration(self):
        for record in self:
            if record.duration_hours <= 0 or record.duration_hours > 24:
                raise ValidationError(
                    _(
                        "Interview duration must be greater than 0 and no more "
                        "than 24 hours."
                    )
                )

    @api.constrains("state", "outcome")
    def _check_completed_outcome(self):
        for record in self:
            if record.state == "completed" and record.outcome == "pending":
                raise ValidationError(
                    _("Record an interview outcome before marking it completed.")
                )

    @api.onchange("submission_id")
    def _onchange_submission_id(self):
        for record in self:
            if record.submission_id:
                record.requirement_id = record.submission_id.requirement_id

    def action_complete(self):
        for record in self:
            if record.outcome == "pending":
                raise UserError(
                    _("Select an outcome before completing the interview.")
                )
        self.write({"state": "completed"})
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True

    def action_no_show(self):
        self.write({"state": "no_show"})
        return True

    def action_reschedule(self):
        self.write({"state": "scheduled", "outcome": "pending", "active": True})
        return True


class StaffingPlacement(models.Model):
    """Commercially approved placement of a candidate into a requirement."""

    _name = "intrastack.staffing.placement"
    _description = "Staffing Placement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True, index=True)
    active = fields.Boolean(default=True)
    requirement_id = fields.Many2one(
        "intrastack.staffing.requirement",
        string="Requirement",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    submission_id = fields.Many2one(
        "intrastack.staffing.submission",
        string="Candidate Submission",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
        domain="[('requirement_id', '=', requirement_id), ('state', 'not in', ['rejected', 'withdrawn'])]",
    )
    candidate_id = fields.Many2one(
        "res.partner",
        string="Candidate",
        related="submission_id.candidate_id",
        store=True,
        readonly=True,
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="requirement_id.partner_id",
        store=True,
        readonly=True,
    )
    lead_id = fields.Many2one(
        "crm.lead",
        string="CRM Opportunity",
        related="requirement_id.lead_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="requirement_id.company_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="requirement_id.currency_id",
        store=True,
        readonly=True,
    )
    manager_id = fields.Many2one(
        "res.users",
        string="Placement Manager",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_approval", "Pending Approval"),
            ("confirmed", "Confirmed"),
            ("active", "Active"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    contract_reference = fields.Char(
        string="Contract / SOW Reference",
        tracking=True,
    )
    customer_po = fields.Char(string="Customer PO", tracking=True)
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Quotation / Sales Order",
        ondelete="set null",
        tracking=True,
        domain="[('partner_id', 'child_of', customer_id)]",
    )
    project_id = fields.Many2one(
        "project.project",
        string="Delivery Project",
        ondelete="set null",
        tracking=True,
        domain="[('partner_id', 'child_of', customer_id)]",
    )
    start_date = fields.Date(
        string="Placement Start",
        required=True,
        tracking=True,
    )
    end_date = fields.Date(string="Placement End", tracking=True)
    billing_unit = fields.Selection(
        [
            ("hour", "Hour"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
            ("fixed", "Fixed Fee"),
        ],
        string="Rate Unit",
        default="hour",
        required=True,
        tracking=True,
    )
    bill_rate = fields.Monetary(
        string="Bill Rate",
        currency_field="currency_id",
        required=True,
        tracking=True,
    )
    cost_rate = fields.Monetary(
        string="Cost Rate",
        currency_field="currency_id",
        required=True,
        tracking=True,
    )
    hours_per_week = fields.Float(
        string="Hours / Week",
        default=40.0,
        tracking=True,
        help="Used for forecast calculations for hourly placements.",
    )
    margin_amount = fields.Monetary(
        string="Gross Margin",
        currency_field="currency_id",
        compute="_compute_margin",
        store=True,
    )
    margin_percent = fields.Float(
        string="Gross Margin %",
        compute="_compute_margin",
        store=True,
        digits=(16, 2),
    )
    weekly_revenue = fields.Monetary(
        string="Weekly Revenue",
        currency_field="currency_id",
        compute="_compute_margin",
        store=True,
    )
    weekly_margin = fields.Monetary(
        string="Weekly Margin",
        currency_field="currency_id",
        compute="_compute_margin",
        store=True,
    )
    notes = fields.Html(string="Internal Notes", sanitize=True)

    _sql_constraints = [
        (
            "placement_rates_non_negative",
            "CHECK(bill_rate >= 0 AND cost_rate >= 0)",
            "Bill and cost rates cannot be negative.",
        ),
        (
            "hours_non_negative",
            "CHECK(hours_per_week >= 0 AND hours_per_week <= 168)",
            "Hours per week must be between 0 and 168.",
        ),
    ]

    @api.depends("candidate_id.name", "requirement_id.name")
    def _compute_name(self):
        for record in self:
            if record.candidate_id and record.requirement_id:
                record.name = _("%s - %s") % (
                    record.candidate_id.display_name,
                    record.requirement_id.display_name,
                )
            elif record.candidate_id:
                record.name = record.candidate_id.display_name
            else:
                record.name = _("Staffing Placement")

    @api.depends("bill_rate", "cost_rate", "hours_per_week", "billing_unit")
    def _compute_margin(self):
        for record in self:
            record.margin_amount = (record.bill_rate or 0.0) - (
                record.cost_rate or 0.0
            )
            record.margin_percent = (
                record.margin_amount / record.bill_rate * 100.0
                if record.bill_rate
                else 0.0
            )
            if record.billing_unit == "hour":
                record.weekly_revenue = (record.bill_rate or 0.0) * (
                    record.hours_per_week or 0.0
                )
                record.weekly_margin = record.margin_amount * (
                    record.hours_per_week or 0.0
                )
            else:
                record.weekly_revenue = record.bill_rate or 0.0
                record.weekly_margin = record.margin_amount

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for incoming in vals_list:
            vals = dict(incoming)
            if vals.get("submission_id"):
                submission = self.env["intrastack.staffing.submission"].browse(
                    vals["submission_id"]
                ).exists()
                if submission:
                    vals.setdefault("requirement_id", submission.requirement_id.id)
                    vals.setdefault("bill_rate", submission.proposed_bill_rate)
                    vals.setdefault("cost_rate", submission.proposed_cost_rate)
                    vals.setdefault(
                        "billing_unit",
                        submission.requirement_id.billing_unit,
                    )
                    vals.setdefault(
                        "start_date",
                        submission.requirement_id.start_date,
                    )
                    vals.setdefault(
                        "end_date",
                        submission.requirement_id.end_date,
                    )
            prepared.append(vals)
        records = super().create(prepared)
        records._subscribe_managers()
        records._sync_delivery_project_links()
        placed = records.filtered(
            lambda placement: placement.state in ("confirmed", "active", "completed")
        )
        if placed:
            placed.mapped("submission_id").write({"state": "accepted"})
        records.mapped("requirement_id")._sync_from_placements()
        return records

    def write(self, vals):
        vals = dict(vals)
        if vals.get("submission_id") and "requirement_id" not in vals:
            submission = self.env["intrastack.staffing.submission"].browse(
                vals["submission_id"]
            ).exists()
            if submission:
                vals["requirement_id"] = submission.requirement_id.id
        old_requirements = self.mapped("requirement_id")
        result = super().write(vals)
        if "manager_id" in vals:
            self._subscribe_managers()
        if vals.get("state") in ("confirmed", "active", "completed"):
            self.mapped("submission_id").write({"state": "accepted"})
        (old_requirements | self.mapped("requirement_id"))._sync_from_placements()
        return result

    def unlink(self):
        requirements = self.mapped("requirement_id")
        if self.filtered(lambda record: record.state not in ("draft", "cancelled")):
            raise UserError(_("Only draft or cancelled placements can be deleted."))
        result = super().unlink()
        requirements._sync_from_placements()
        return result

    def _subscribe_managers(self):
        for record in self:
            if record.manager_id.partner_id:
                record.message_subscribe(partner_ids=record.manager_id.partner_id.ids)

    def _sync_delivery_project_links(self):
        """Reuse the delivery project created by the confirmed Sales Order."""
        for record in self.filtered(
            lambda placement: placement.sale_order_id and not placement.project_id
        ):
            order = record.sale_order_id
            if "intrastack_delivery_project_id" not in order._fields:
                continue
            project = order.intrastack_delivery_project_id
            if project:
                record.project_id = project

    @api.onchange("submission_id")
    def _onchange_submission_id(self):
        for record in self:
            if record.submission_id:
                record.requirement_id = record.submission_id.requirement_id
                if not record.bill_rate:
                    record.bill_rate = record.submission_id.proposed_bill_rate
                if not record.cost_rate:
                    record.cost_rate = record.submission_id.proposed_cost_rate
                record.billing_unit = record.requirement_id.billing_unit
                if not record.start_date:
                    record.start_date = record.requirement_id.start_date
                if not record.end_date:
                    record.end_date = record.requirement_id.end_date

    @api.onchange("sale_order_id")
    def _onchange_sale_order_id(self):
        for record in self:
            order = record.sale_order_id
            if not order or "intrastack_delivery_project_id" not in order._fields:
                continue
            if order.intrastack_delivery_project_id:
                record.project_id = order.intrastack_delivery_project_id

    @api.constrains(
        "requirement_id",
        "submission_id",
        "sale_order_id",
        "project_id",
    )
    def _check_links(self):
        for record in self:
            if (
                record.submission_id
                and record.requirement_id
                and record.submission_id.requirement_id != record.requirement_id
            ):
                raise ValidationError(
                    _(
                        "The placement requirement must match the candidate "
                        "submission requirement."
                    )
                )
            if (
                record.sale_order_id
                and record.customer_id
                and record.sale_order_id.partner_id.commercial_partner_id
                != record.customer_id.commercial_partner_id
            ):
                raise ValidationError(
                    _("The quotation customer must match the placement customer.")
                )
            if (
                record.project_id
                and record.customer_id
                and record.project_id.partner_id
                and record.project_id.partner_id.commercial_partner_id
                != record.customer_id.commercial_partner_id
            ):
                raise ValidationError(
                    _("The project customer must match the placement customer.")
                )

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for record in self:
            if record.end_date and record.end_date < record.start_date:
                raise ValidationError(
                    _("Placement end date cannot be before the start date.")
                )

    @api.constrains("bill_rate", "cost_rate")
    def _check_rates(self):
        for record in self:
            if record.bill_rate < record.cost_rate:
                raise ValidationError(
                    _(
                        "Bill rate cannot be below cost rate; record an approved "
                        "exception separately."
                    )
                )

    @api.constrains(
        "state",
        "bill_rate",
        "cost_rate",
        "contract_reference",
        "sale_order_id",
    )
    def _check_confirmed_commercial_terms(self):
        confirmed_states = ("confirmed", "active", "completed")
        for record in self:
            if record.state not in confirmed_states:
                continue
            if record.bill_rate <= 0:
                raise ValidationError(
                    _("A confirmed placement must have a positive bill rate.")
                )
            if not record.contract_reference and not record.sale_order_id:
                raise ValidationError(
                    _(
                        "A confirmed placement requires a signed contract reference "
                        "or a confirmed Sales Order."
                    )
                )
            if record.sale_order_id and record.sale_order_id.state != "sale":
                raise ValidationError(
                    _("The linked quotation must be confirmed before placement.")
                )

    @api.constrains("submission_id", "state")
    def _check_one_open_placement(self):
        for record in self:
            if record.state == "cancelled" or not record.submission_id:
                continue
            duplicate = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("submission_id", "=", record.submission_id.id),
                    ("state", "!=", "cancelled"),
                ]
            )
            if duplicate:
                raise ValidationError(
                    _("A candidate submission can have only one open placement.")
                )

    def _ensure_can_confirm(self):
        for record in self:
            if record.submission_id.state in ("rejected", "withdrawn"):
                raise UserError(
                    _("A rejected or withdrawn candidate cannot be placed.")
                )
            if not record.start_date:
                raise UserError(
                    _("Set a placement start date before confirming.")
                )
            if record.bill_rate <= 0:
                raise UserError(
                    _("Bill rate must be greater than zero before confirming.")
                )
            if record.cost_rate < 0:
                raise UserError(_("Cost rate cannot be negative."))
            if not record.contract_reference and not record.sale_order_id:
                raise UserError(
                    _(
                        "Link a confirmed Sales Order or enter the signed contract "
                        "reference before confirming the placement."
                    )
                )
            if record.sale_order_id and record.sale_order_id.state != "sale":
                raise UserError(
                    _("The linked quotation must be confirmed before placement.")
                )

    def action_submit_for_approval(self):
        self._ensure_can_confirm()
        self.write({"state": "pending_approval"})
        return True

    def action_confirm(self):
        self._ensure_can_confirm()
        self._sync_delivery_project_links()
        self.write({"state": "confirmed"})
        self.mapped("submission_id").write({"state": "accepted"})
        self.mapped("requirement_id")._sync_from_placements()
        return True

    def action_activate(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "confirmed":
                raise UserError(
                    _("Only confirmed placements can be activated.")
                )
            if record.start_date and record.start_date > today:
                raise UserError(
                    _("A placement cannot start before its contract start date.")
                )
        self.write({"state": "active"})
        self.mapped("requirement_id")._sync_from_placements()
        return True

    def action_complete(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != "active":
                raise UserError(_("Only active placements can be completed."))
            if not record.end_date:
                record.end_date = today
        self.write({"state": "completed"})
        self.mapped("requirement_id")._sync_from_placements()
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        accepted = self.mapped("submission_id").filtered(
            lambda submission: submission.state == "accepted"
        )
        if accepted:
            accepted.write({"state": "offer"})
        self.mapped("requirement_id")._sync_from_placements()
        return True

    def action_reopen(self):
        for record in self:
            if record.state != "cancelled":
                raise UserError(
                    _("Only cancelled placements can be reopened.")
                )
        self.write({"state": "draft", "active": True})
        return True


class CrmLeadStaffing(models.Model):
    """Expose staffing requirements from the originating opportunity."""

    _inherit = "crm.lead"

    staffing_requirement_ids = fields.One2many(
        "intrastack.staffing.requirement",
        "lead_id",
        string="Staffing Requirements",
    )
    staffing_requirement_count = fields.Integer(
        string="Staffing Requirement Count",
        compute="_compute_staffing_requirement_count",
    )

    @api.depends("staffing_requirement_ids")
    def _compute_staffing_requirement_count(self):
        for lead in self:
            lead.staffing_requirement_count = len(lead.staffing_requirement_ids)

    def action_view_staffing_requirements(self):
        self.ensure_one()
        action = self.env.ref(
            "intrastack_crm.action_staffing_requirement"
        ).read()[0]
        action["domain"] = [("lead_id", "=", self.id)]
        action["context"] = {
            "default_lead_id": self.id,
            "default_partner_id": self.partner_id.id,
        }
        return action
