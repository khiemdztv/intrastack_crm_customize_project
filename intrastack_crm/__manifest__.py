{
    'name': 'IntraStack CRM Platform',
    'version': '17.0.2.2.0',
    'category': 'Sales/CRM',
    'summary': 'Integrated CRM, sales, staffing and delivery workflows for IntraStack Solutions',
    'description': """
IntraStack CRM Platform
=======================

This module configures IntraStack's CRM platform on Odoo 17 Community Edition.

Capabilities
------------

* Four routed CRM pipelines: Staffing, Consulting, Subcontracting and Managed Services.
* Customer/contact integration and import-compatible opportunity fields.
* Quotation templates, contract dates and CRM-to-project traceability.
* Staffing requirements, candidate submissions, interviews and placements.
* Employee internal-user activation with operational role bundles.
* Automation activities, project templates and CEO saved filters.

Optional demo data is available for non-production databases. Production
installation must use ``--without-demo=all``.
""",
    'author': 'IntraStack Solutions',
    'website': 'https://crm.intrastack.com',
    'license': 'LGPL-3',
    'depends': [
        'crm',
        'sale_management',
        'sale_crm',
        'sale_project',
        'sale_timesheet',
        'project',
        'hr_timesheet',
        'auth_signup',
        'contacts',
        'base_automation',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # Data order matters.
        'data/contact_tags.xml',
        'data/crm_teams.xml',
        'data/crm_stages.xml',
        'data/product_data.xml',
        'data/project_templates.xml',
        'data/service_tracking.xml',
        'data/sale_templates.xml',
        'data/automation_rules.xml',
        'data/ceo_dashboard_filters.xml',
        'views/crm_lead_views.xml',
        'views/crm_delivery_views.xml',
        'views/staffing_views.xml',
        'views/hr_employee_views.xml',
        'views/pipeline_menus.xml',
    ],
    'demo': [
        'demo/demo_contacts.xml',
        'demo/demo_opportunities.xml',
        'demo/demo_projects.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [],
}
