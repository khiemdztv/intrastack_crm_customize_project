# -*- coding: utf-8 -*-
"""CRM to commercial and delivery bridges for IntraStack.

The base module intentionally keeps the CRM configuration close to standard
Odoo.  This extension adds the small amount of orchestration needed by the
business workflow:

* a quotation opened from an opportunity receives the appropriate quotation
  template;
* a confirmed quotation linked to an opportunity gets one delivery project;
* the project is cloned from the Community project templates shipped with the
  module (or created as a regular project when no template is configured).

The implementation does not depend on Enterprise models.  ``sale_crm`` is a
required integration dependency at installation time (see the integration
notes), while the optional ``sale_project`` fields are detected at runtime so
the module remains usable on a minimal Community installation.
"""

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class CrmLead(models.Model):
    """Add contract metadata and delivery actions to CRM opportunities."""

    _inherit = "crm.lead"

    # Canonical contract dates live on the opportunity.  Sale orders expose
    # editable related fields below, so changing dates in either document keeps
    # the commercial record in sync.
    intrastack_contract_start_date = fields.Date(
        string="Contract Start",
        tracking=True,
        copy=True,
        help="First day of the service contract or placement.",
    )
    intrastack_contract_end_date = fields.Date(
        string="Contract End",
        tracking=True,
        copy=True,
        help="Last day of the service contract or placement.",
    )
    intrastack_contract_renewal_date = fields.Date(
        string="Renewal Review Date",
        tracking=True,
        copy=True,
        help="Date on which the renewal conversation should be started.",
    )

    intrastack_delivery_project_ids = fields.One2many(
        "project.project",
        "intrastack_opportunity_id",
        string="Delivery Projects",
        copy=False,
    )
    intrastack_delivery_project_count = fields.Integer(
        string="Delivery Project Count",
        compute="_compute_intrastack_delivery_links",
    )
    intrastack_delivery_project_id = fields.Many2one(
        "project.project",
        string="Delivery Project",
        compute="_compute_intrastack_delivery_links",
        help="Primary project created for the won opportunity.",
    )
    intrastack_primary_order_id = fields.Many2one(
        "sale.order",
        string="Primary Quotation / Order",
        compute="_compute_intrastack_commercial_links",
        help="Most recent active quotation, or the latest confirmed order.",
    )
    intrastack_has_confirmed_order = fields.Boolean(
        string="Has Confirmed Order",
        compute="_compute_intrastack_commercial_links",
    )
    intrastack_can_create_delivery_project = fields.Boolean(
        string="Can Create Delivery Project",
        compute="_compute_intrastack_commercial_links",
    )

    QUOTATION_TEMPLATE_XMLIDS = {
        "staffing": "intrastack_crm.sale_template_staffing_rate_card",
        "consulting": "intrastack_crm.sale_template_consulting_sow",
        # Subcontracting follows the same rate-card commercial model as
        # staffing until a dedicated subcontractor SOW is configured.
        "subcontracting": "intrastack_crm.sale_template_staffing_rate_card",
        "managed_services": "intrastack_crm.sale_template_managed_services",
    }
    PROJECT_TEMPLATE_XMLIDS = {
        "staffing": "intrastack_crm.project_template_staffing",
        "consulting": "intrastack_crm.project_template_consulting",
        # There is no separate subcontracting template in the current BRD
        # package.  A regular project is created for that service line.
        "managed_services": "intrastack_crm.project_template_managed_service",
    }

    @api.depends("intrastack_delivery_project_ids")
    def _compute_intrastack_delivery_links(self):
        for lead in self:
            projects = lead.intrastack_delivery_project_ids.sorted("id")
            lead.intrastack_delivery_project_count = len(projects)
            lead.intrastack_delivery_project_id = projects[:1]

    @api.depends("order_ids.state", "order_ids.date_order", "intrastack_delivery_project_ids")
    def _compute_intrastack_commercial_links(self):
        """Expose an idempotent, useful primary commercial document.

        ``order_ids`` is supplied by Odoo's ``sale_crm`` Community module.  A
        confirmed order wins over draft quotations; among documents in the
        same state the newest record is selected.
        """
        for lead in self:
            orders = lead.order_ids.filtered(lambda order: order.state != "cancel")
            confirmed = orders.filtered(lambda order: order.state == "sale")
            primary_pool = confirmed or orders
            lead.intrastack_primary_order_id = primary_pool.sorted("id", reverse=True)[:1]
            lead.intrastack_has_confirmed_order = bool(confirmed)
            lead.intrastack_can_create_delivery_project = bool(
                lead.type == "opportunity"
                and confirmed
                and not lead.intrastack_delivery_project_ids
            )

    @api.constrains(
        "intrastack_contract_start_date",
        "intrastack_contract_end_date",
        "intrastack_contract_renewal_date",
    )
    def _check_intrastack_contract_dates(self):
        for lead in self:
            start = lead.intrastack_contract_start_date
            end = lead.intrastack_contract_end_date
            renewal = lead.intrastack_contract_renewal_date
            if start and end and end < start:
                raise ValidationError(_("Contract end date cannot be before the contract start date."))
            if renewal and end and renewal > end:
                raise ValidationError(_("Renewal review date cannot be after the contract end date."))

    # ------------------------------------------------------------------
    # Quotation helpers
    # ------------------------------------------------------------------

    def _get_intrastack_quotation_template(self):
        """Return the configured Community quotation template for this lead."""
        self.ensure_one()
        xmlid = self.QUOTATION_TEMPLATE_XMLIDS.get(self.x_deal_classification)
        if not xmlid:
            return self.env["sale.order.template"]
        template = self.env.ref(xmlid, raise_if_not_found=False)
        if not template:
            return self.env["sale.order.template"]
        company = self.company_id or self.env.company
        if template.company_id and template.company_id != company:
            return self.env["sale.order.template"]
        return template

    def _prepare_intrastack_quotation_context(self):
        """Extend Odoo's standard opportunity-to-quotation context."""
        self.ensure_one()
        context = dict(super()._prepare_opportunity_quotation_context())
        template = self._get_intrastack_quotation_template()
        if template:
            context["default_sale_order_template_id"] = template.id
        # These are related fields on sale.order.  Supplying defaults makes the
        # values visible immediately in a newly opened quotation form.
        for field_name in (
            "intrastack_contract_start_date",
            "intrastack_contract_end_date",
            "intrastack_contract_renewal_date",
        ):
            value = self[field_name]
            if value:
                context["default_%s" % field_name] = value
        return context

    def action_new_quotation(self):
        """Open the standard quotation form with IntraStack defaults."""
        self.ensure_one()
        action = super().action_new_quotation()
        action["context"] = self._prepare_intrastack_quotation_context()
        action["context"]["search_default_opportunity_id"] = self.id
        return action

    def action_create_intrastack_quotation(self):
        """Create a ready-to-edit quotation using the selected template.

        This is intentionally separate from ``action_new_quotation``.  The
        standard Odoo button can continue to open an unsaved form, while this
        action is useful for a deterministic end-to-end demo and for API use.
        """
        self.ensure_one()
        if self.type != "opportunity":
            raise UserError(_("Convert this lead to an opportunity before creating a quotation."))
        if not self.partner_id:
            # Let the standard partner-selection flow handle missing customer
            # information instead of creating an invalid sale order.
            return self.action_sale_quotations_new()

        SaleOrder = self.env["sale.order"]
        template = self._get_intrastack_quotation_template()
        values = {
            "partner_id": self.partner_id.id,
            "opportunity_id": self.id,
            "company_id": (self.company_id or self.env.company).id,
            "user_id": self.user_id.id or self.env.user.id,
            "team_id": self.team_id.id,
            "origin": self.name,
            "campaign_id": self.campaign_id.id,
            "medium_id": self.medium_id.id,
            "source_id": self.source_id.id,
            "tag_ids": [Command.set(self.tag_ids.ids)],
        }
        if template:
            values["sale_order_template_id"] = template.id
            values["order_line"] = [
                Command.create(line._prepare_order_line_values())
                for line in template.sale_order_template_line_ids
            ]
            if "sale_order_option_ids" in SaleOrder._fields:
                values["sale_order_option_ids"] = [
                    Command.create(option._prepare_option_line_values())
                    for option in template.sale_order_template_option_ids
                ]

        quotation = SaleOrder.create(values)
        return {
            "type": "ir.actions.act_window",
            "name": _("Quotation"),
            "res_model": "sale.order",
            "view_mode": "form",
            "views": [(self.env.ref("sale.view_order_form").id, "form")],
            "res_id": quotation.id,
            "target": "current",
        }

    def action_create_intrastack_delivery_project(self):
        """Retry project creation from the latest confirmed order."""
        self.ensure_one()
        if self.type != "opportunity":
            raise UserError(_("Only opportunities can have a delivery project."))
        confirmed_orders = self.order_ids.filtered(lambda order: order.state == "sale")
        if not confirmed_orders:
            raise UserError(_("Confirm a quotation before creating the delivery project."))
        project = self._ensure_intrastack_delivery_project(
            confirmed_orders.sorted("id", reverse=True)[:1]
        )
        return project._intrastack_open_action()

    def _check_intrastack_commercial_readiness(self, order):
        """Block confirmation until the CRM and contract data are complete."""
        self.ensure_one()
        order.ensure_one()
        if self.type != "opportunity":
            raise UserError(_("The linked CRM record must be an opportunity."))
        if order.opportunity_id != self:
            raise UserError(_("The sales order is not linked to this opportunity."))

        required_fields = (
            "partner_id",
            "x_deal_classification",
            "x_service_category",
            "x_urgency_flag",
            "x_source_tracking",
            "intrastack_contract_start_date",
            "intrastack_contract_end_date",
        )
        missing = [
            self._fields[field_name].string
            for field_name in required_fields
            if not self[field_name]
        ]
        if self.x_expected_value <= 0:
            missing.append(self._fields["x_expected_value"].string)

        commercial_lines = order.order_line.filtered(
            lambda line: not line.display_type and line.product_id
        )
        if not commercial_lines:
            missing.append(_("Order Lines"))
        elif not commercial_lines.filtered(
            lambda line: getattr(line.product_id, "detailed_type", line.product_id.type)
            == "service"
        ):
            missing.append(_("Service Order Line"))

        if missing:
            raise UserError(_(
                "Cannot confirm %(order)s. Complete these commercial fields first: %(fields)s",
                order=order.display_name,
                fields=", ".join(dict.fromkeys(missing)),
            ))

        lead_customer = self.partner_id.commercial_partner_id
        order_customer = order.partner_id.commercial_partner_id
        if lead_customer != order_customer:
            raise UserError(_(
                "The quotation customer must match the customer on opportunity %(opportunity)s.",
                opportunity=self.display_name,
            ))
        return True

    def action_view_intrastack_delivery_project(self):
        self.ensure_one()
        projects = self.intrastack_delivery_project_ids
        if not projects:
            return {"type": "ir.actions.act_window_close"}
        if len(projects) == 1:
            return projects._intrastack_open_action()
        return {
            "type": "ir.actions.act_window",
            "name": _("Delivery Projects"),
            "res_model": "project.project",
            "view_mode": "kanban,tree,form",
            "domain": [("id", "in", projects.ids)],
            "target": "current",
        }

    # ------------------------------------------------------------------
    # Project orchestration
    # ------------------------------------------------------------------

    def _get_intrastack_project_template(self):
        self.ensure_one()
        xmlid = self.PROJECT_TEMPLATE_XMLIDS.get(self.x_deal_classification)
        if not xmlid:
            return self.env["project.project"]
        template = self.env.ref(xmlid, raise_if_not_found=False)
        if not template:
            return self.env["project.project"]
        company = self.company_id or self.env.company
        if template.company_id and template.company_id != company:
            return self.env["project.project"]
        return template

    def _intrastack_standard_projects_for_order(self, order):
        """Find projects generated by Community ``sale_project`` if installed."""
        if "project_ids" not in order._fields:
            return self.env["project.project"]
        try:
            return order.sudo().project_ids.filtered(lambda project: project.active)
        except (AccessError, UserError):
            # A missing optional bridge or a restrictive project rule must not
            # make the opportunity confirmation fail; our own project fallback
            # below remains available.
            return self.env["project.project"]

    def _prepare_intrastack_project_values(self, order, template=False):
        self.ensure_one()
        project_model = self.env["project.project"]
        company = order.company_id or self.company_id or self.env.company
        values = {
            "name": _("%(opportunity)s - Delivery", opportunity=self.name),
            "partner_id": (order.partner_id or self.partner_id).id,
            "company_id": company.id,
            "user_id": (self.user_id or order.user_id or self.env.user).id,
            "date_start": self.intrastack_contract_start_date or False,
            "date": self.intrastack_contract_end_date or False,
            "intrastack_opportunity_id": self.id,
            "intrastack_sale_order_id": order.id,
        }
        if template and template.description:
            values["description"] = template.description
        elif self.description:
            values["description"] = self.description

        # hr_timesheet is a Community dependency of the base module.  Keep the
        # field check so this extension can still be loaded in a minimal test
        # registry where that optional bridge is omitted.
        if "allow_timesheets" in project_model._fields:
            values["allow_timesheets"] = True

        # If sale_project is installed, connect the project to the service line
        # so timesheets and invoices retain the standard Odoo traceability.
        service_line = order.order_line.filtered(
            lambda line: not line.display_type
            and line.product_id
            and getattr(line.product_id, "detailed_type", line.product_id.type) == "service"
        )[:1]
        if service_line and "sale_line_id" in project_model._fields:
            values["sale_line_id"] = service_line.id
        if service_line and "allow_billable" in project_model._fields:
            values["allow_billable"] = True
        return values

    def _link_intrastack_project(self, project, order):
        """Link an existing project without stealing another opportunity's project."""
        self.ensure_one()
        if project.intrastack_opportunity_id and project.intrastack_opportunity_id != self:
            return False
        project_values = {}
        if not project.intrastack_opportunity_id:
            project_values["intrastack_opportunity_id"] = self.id
        if not project.intrastack_sale_order_id:
            project_values["intrastack_sale_order_id"] = order.id
        # A project may have been generated by the standard sale_project
        # bridge before this extension runs.  Carry the CRM contract window to
        # that project as well; project.project clears a partial date range, so
        # update both endpoints together.
        if "date_start" in project._fields and "date" in project._fields:
            project_start = self.intrastack_contract_start_date or project.date_start
            project_end = self.intrastack_contract_end_date or project.date
            if project_start and project_end:
                project_values.update({
                    "date_start": project_start,
                    "date": project_end,
                })
        if project_values:
            project.sudo().write(project_values)
        order.write({"intrastack_delivery_project_id": project.id})
        return project

    def _ensure_intrastack_delivery_project(self, order):
        """Return the one delivery project for this opportunity/order.

        The method is intentionally idempotent.  It is called after every
        confirmation and can also be called by the manual retry button.
        """
        self.ensure_one()
        order.ensure_one()
        if order.opportunity_id != self:
            raise UserError(_("The sales order is not linked to this opportunity."))
        if order.state != "sale":
            raise UserError(_("The quotation must be confirmed before a delivery project is created."))

        if order.intrastack_delivery_project_id:
            return order.intrastack_delivery_project_id

        existing = self.intrastack_delivery_project_ids[:1]
        if existing:
            linked = self._link_intrastack_project(existing, order)
            if linked:
                return linked

        # Respect a project already generated by the standard Community bridge.
        for standard_project in self._intrastack_standard_projects_for_order(order):
            linked = self._link_intrastack_project(standard_project, order)
            if linked:
                return linked

        template = self._get_intrastack_project_template()
        values = self._prepare_intrastack_project_values(order, template=template)
        Project = self.env["project.project"].sudo().with_company(order.company_id)
        if template:
            project = template.sudo().with_company(order.company_id).with_context(
                no_create_folder=True,
            ).copy(values)
        else:
            project = Project.create(values)
        # The custom links are copy=False, but explicitly link after copy as a
        # guard against a future template override that changes copy flags.
        return self._link_intrastack_project(project, order) or project


class SaleOrder(models.Model):
    """Expose contract dates and create/link delivery projects on confirmation."""

    _inherit = "sale.order"

    intrastack_contract_start_date = fields.Date(
        related="opportunity_id.intrastack_contract_start_date",
        string="Contract Start",
        readonly=False,
        store=True,
        copy=False,
        tracking=True,
    )
    intrastack_contract_end_date = fields.Date(
        related="opportunity_id.intrastack_contract_end_date",
        string="Contract End",
        readonly=False,
        store=True,
        copy=False,
        tracking=True,
    )
    intrastack_contract_renewal_date = fields.Date(
        related="opportunity_id.intrastack_contract_renewal_date",
        string="Renewal Review Date",
        readonly=False,
        store=True,
        copy=False,
        tracking=True,
    )
    intrastack_delivery_project_id = fields.Many2one(
        "project.project",
        string="Delivery Project",
        copy=False,
        readonly=True,
        check_company=True,
        ondelete="set null",
    )
    intrastack_can_create_delivery_project = fields.Boolean(
        string="Can Create Delivery Project",
        compute="_compute_intrastack_delivery_project_state",
    )

    @api.depends("state", "opportunity_id", "intrastack_delivery_project_id")
    def _compute_intrastack_delivery_project_state(self):
        for order in self:
            order.intrastack_can_create_delivery_project = bool(
                order.state == "sale"
                and order.opportunity_id
                and not order.intrastack_delivery_project_id
            )

    def action_confirm(self):
        linked_orders = self.filtered("opportunity_id")
        for order in linked_orders:
            order.opportunity_id._check_intrastack_commercial_readiness(order)

        result = super().action_confirm()
        if self.env.context.get("skip_intrastack_delivery_project"):
            return result

        confirmed_orders = self.filtered(
            lambda item: item.state == "sale" and item.opportunity_id
        )
        for order in confirmed_orders:
            order.opportunity_id._ensure_intrastack_delivery_project(order)

        leads_to_win = confirmed_orders.mapped("opportunity_id").filtered(
            lambda lead: lead.probability != 100 or not lead.stage_id.is_won
        )
        if leads_to_win:
            leads_to_win.action_set_won()
        return result

    def action_create_intrastack_delivery_project(self):
        self.ensure_one()
        if not self.opportunity_id:
            raise UserError(_("Link this sales order to a CRM opportunity first."))
        project = self.opportunity_id._ensure_intrastack_delivery_project(self)
        return project._intrastack_open_action()

    def action_view_intrastack_delivery_project(self):
        self.ensure_one()
        project = self.intrastack_delivery_project_id
        if not project:
            return {"type": "ir.actions.act_window_close"}
        return project._intrastack_open_action()


class ProjectProject(models.Model):
    """Traceability links back to CRM and the originating sale order."""

    _inherit = "project.project"

    intrastack_opportunity_id = fields.Many2one(
        "crm.lead",
        string="CRM Opportunity",
        index=True,
        copy=False,
        ondelete="set null",
        check_company=True,
    )
    intrastack_sale_order_id = fields.Many2one(
        "sale.order",
        string="Originating Quotation / Order",
        index=True,
        copy=False,
        ondelete="set null",
        check_company=True,
    )

    _sql_constraints = [
        (
            "intrastack_one_delivery_project_per_opportunity",
            "unique(intrastack_opportunity_id)",
            "An opportunity can have only one IntraStack delivery project.",
        ),
    ]

    def _intrastack_open_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Delivery Project"),
            "res_model": "project.project",
            "view_mode": "form",
            "views": [(self.env.ref("project.edit_project").id, "form")],
            "res_id": self.id,
            "target": "current",
        }

    def action_view_intrastack_opportunity(self):
        self.ensure_one()
        if not self.intrastack_opportunity_id:
            return {"type": "ir.actions.act_window_close"}
        return {
            "type": "ir.actions.act_window",
            "name": _("Opportunity"),
            "res_model": "crm.lead",
            "view_mode": "form",
            "views": [(self.env.ref("crm.crm_lead_view_form").id, "form")],
            "res_id": self.intrastack_opportunity_id.id,
            "target": "current",
        }
