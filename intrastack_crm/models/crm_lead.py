from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_deal_classification = fields.Selection(
        string='Deal Classification',
        selection=[
            ('staffing', 'Staffing'),
            ('consulting', 'Consulting'),
            ('subcontracting', 'Subcontracting'),
            ('managed_services', 'Managed Services'),
        ],
        tracking=True,
        help='Primary business line classification for this deal.',
    )

    x_service_category = fields.Selection(
        string='Service Category',
        selection=[
            ('cloud', 'Cloud'),
            ('ai_ml', 'AI/ML'),
            ('cybersecurity', 'Cybersecurity'),
            ('devops', 'DevOps'),
            ('data_engineering', 'Data Engineering'),
            ('app_modernization', 'App Modernization'),
        ],
        tracking=True,
        help='Technology domain for this engagement.',
    )

    x_urgency_flag = fields.Selection(
        string='Urgency Flag',
        selection=[
            ('immediate', 'Immediate (0-30 days)'),
            ('short_term', 'Short-term (30-90 days)'),
            ('long_term', 'Long-term (90+ days)'),
        ],
        tracking=True,
        help='Expected timeline for deal closure.',
    )

    x_source_tracking = fields.Selection(
        string='Source Tracking',
        selection=[
            ('linkedin', 'LinkedIn'),
            ('msp_outreach', 'MSP Outreach'),
            ('prime_contractor', 'Prime Contractor'),
            ('referral', 'Referral'),
            ('vendor_portal', 'Vendor Portal'),
            ('website', 'Website'),
            ('email', 'Email'),
            ('other', 'Other'),
        ],
        tracking=True,
        help='Lead acquisition channel.',
    )

    # Keep the BRD field name while using Odoo's native revenue field as the
    # single source of truth for forecasts, reports, imports, and quotations.
    x_expected_value = fields.Monetary(
        string='Expected Value',
        related='expected_revenue',
        currency_field='company_currency',
        readonly=False,
        store=True,
    )

    x_decision_maker = fields.Boolean(
        string='Decision Maker?',
        default=False,
        tracking=True,
        help='Check if the primary contact is the decision maker.',
    )

    CLASSIFICATION_TEAM_MAP = {
        'staffing': 'intrastack_crm.team_p1_staffing',
        'consulting': 'intrastack_crm.team_p2_consulting',
        'subcontracting': 'intrastack_crm.team_p3_subcontracting',
        'managed_services': 'intrastack_crm.team_p4_managed_services',
    }

    def _team_for_classification(self, classification):
        xml_id = self.CLASSIFICATION_TEAM_MAP.get(classification)
        return self.env.ref(xml_id, raise_if_not_found=False) if xml_id else False

    def _first_stage_for_team(self, team):
        if not team:
            return self.env['crm.stage']
        return self.env['crm.stage'].search(
            [('team_id', '=', team.id)],
            order='sequence, id',
            limit=1,
        )

    def _prepare_pipeline_values(self, values):
        values = dict(values)
        classification = values.get('x_deal_classification')
        if not classification:
            return values

        team = self._team_for_classification(classification)
        if not team:
            return values

        values['team_id'] = team.id
        stage = self.env['crm.stage'].browse(values.get('stage_id')).exists()
        if not stage or stage.team_id != team:
            first_stage = self._first_stage_for_team(team)
            values['stage_id'] = first_stage.id if first_stage else False
        return values

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = [self._prepare_pipeline_values(vals) for vals in vals_list]
        return super().create(prepared_vals)

    def write(self, values):
        if 'x_deal_classification' not in values:
            return super().write(values)

        for lead in self:
            prepared_values = lead._prepare_pipeline_values(values)
            super(CrmLead, lead).write(prepared_values)
        return True

    @api.onchange('x_deal_classification')
    def _onchange_deal_classification(self):
        for lead in self:
            team = lead._team_for_classification(lead.x_deal_classification)
            if team:
                lead.team_id = team
                lead.stage_id = lead._first_stage_for_team(team)

    @api.constrains(
        'type',
        'stage_id',
        'partner_id',
        'user_id',
        'expected_revenue',
        'x_deal_classification',
        'x_service_category',
        'x_urgency_flag',
        'x_source_tracking',
    )
    def _check_won_deal_readiness(self):
        labels = {
            'partner_id': _('Customer'),
            'user_id': _('Salesperson'),
            'x_deal_classification': _('Deal Classification'),
            'x_service_category': _('Service Category'),
            'x_urgency_flag': _('Urgency Flag'),
            'x_source_tracking': _('Source Tracking'),
        }
        for lead in self.filtered(lambda item: item.type == 'opportunity' and item.stage_id.is_won):
            missing = [label for field_name, label in labels.items() if not lead[field_name]]
            if lead.expected_revenue <= 0:
                missing.append(_('Expected Revenue'))
            if missing:
                raise ValidationError(_(
                    'The opportunity cannot be marked won until these fields are completed: %s',
                    ', '.join(missing),
                ))

    @api.constrains('x_deal_classification', 'team_id', 'stage_id')
    def _check_pipeline_consistency(self):
        for lead in self.filtered('x_deal_classification'):
            expected_team = lead._team_for_classification(lead.x_deal_classification)
            if expected_team and lead.team_id != expected_team:
                raise ValidationError(_(
                    'Deal Classification and Sales Team must use the same IntraStack pipeline.'
                ))
            if lead.stage_id.team_id and lead.stage_id.team_id != lead.team_id:
                raise ValidationError(_(
                    'The selected stage does not belong to the opportunity Sales Team.'
                ))
