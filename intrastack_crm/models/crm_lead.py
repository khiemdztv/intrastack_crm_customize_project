from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # ── Custom Fields (Slide 05) ──────────────────────────────────────────────
    # All 6 fields are mandatory on every CRM opportunity record.

    x_deal_classification = fields.Selection(
        string='Deal Classification',
        selection=[
            ('staffing', 'Staffing'),
            ('consulting', 'Consulting'),
            ('subcontracting', 'Subcontracting'),
            ('managed_services', 'Managed Services'),
        ],
        required=True,
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
        required=True,
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
        required=True,
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
        ],
        required=True,
        tracking=True,
        help='Lead acquisition channel.',
    )

    x_expected_value = fields.Monetary(
        string='Expected Value ($)',
        currency_field='company_currency',
        required=True,
        tracking=True,
        help='Estimated total deal value in USD.',
    )

    x_decision_maker = fields.Boolean(
        string='Decision Maker?',
        default=False,
        tracking=True,
        help='Check if the primary contact is the decision maker.',
    )

    # ── Auto-assign pipeline based on Deal Classification ──────────────────
    CLASSIFICATION_TEAM_MAP = {
        'staffing': 'intrastack_crm.team_p1_staffing',
        'consulting': 'intrastack_crm.team_p2_consulting',
        'subcontracting': 'intrastack_crm.team_p3_subcontracting',
        'managed_services': 'intrastack_crm.team_p4_managed_services',
    }

    @api.onchange('x_deal_classification')
    def _onchange_deal_classification(self):
        """Auto-assign Sales Team + first stage when Deal Classification is selected."""
        if not self.x_deal_classification:
            return
        xml_id = self.CLASSIFICATION_TEAM_MAP.get(self.x_deal_classification)
        if not xml_id:
            return
        team = self.env.ref(xml_id, raise_if_not_found=False)
        if team:
            self.team_id = team
            # Find the first (lowest sequence) stage for this team
            first_stage = self.env['crm.stage'].search(
                [('team_id', '=', team.id)],
                order='sequence asc',
                limit=1,
            )
            if first_stage:
                self.stage_id = first_stage

