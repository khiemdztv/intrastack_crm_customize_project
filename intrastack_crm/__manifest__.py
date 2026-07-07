{
    'name': 'IntraStack CRM Platform',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Complete CRM configuration for IntraStack Solutions — 4 pipelines, custom fields, automation, dashboard',
    'description': """
IntraStack CRM Platform Module
===============================

This module configures the complete IntraStack CRM platform on Odoo 17 Community Edition:

**Phase 1 — Foundation:**
- 4 CRM Pipelines (Staffing, Consulting, Subcontracting, Managed Services) with 26 stages
- 6 Custom Fields on every opportunity (Deal Classification, Service Category, Urgency, Source, Value, Decision Maker)
- 10 Contact Tags for relationship categorization
- 4 Automation Rules (R1-R4) using Activity system
- 3 Project Templates (Staffing, Consulting, Managed Service engagements)
- 3 Sales Quotation Templates (Rate Card, SOW, MSC)
- 7 CEO Dashboard saved filter views

**Demo Data:**
- 15+ sample contacts across all entity types
- 20+ sample opportunities across 4 pipelines
- 5+ sample projects with tasks
    """,
    'author': 'IntraStack Solutions',
    'website': 'https://crm.intrastack.com',
    'license': 'LGPL-3',
    'depends': [
        'crm',
        'sale_management',
        'project',
        'hr_timesheet',
        'contacts',
        'base_automation',
    ],
    'data': [
        # Views
        'views/crm_lead_views.xml',
        'views/pipeline_menus.xml',
        # Data — order matters!
        'data/contact_tags.xml',
        'data/crm_teams.xml',
        'data/crm_stages.xml',
        'data/product_data.xml',
        'data/sale_templates.xml',
        'data/project_templates.xml',
        'data/automation_rules.xml',
    ],
    'demo': [
        'demo/demo_contacts.xml',
        'demo/demo_opportunities.xml',
        'demo/demo_projects.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
}
