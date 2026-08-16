import os

from odoo.tools.misc import file_path
from odoo.tests.common import TransactionCase


class TestImportTemplates(TransactionCase):

    EXPECTED_TEMPLATES = {
        "res.partner": (
            "crm_companies_import.csv",
            "crm_contacts_import.csv",
            "crm_candidates_import.csv",
            "crm_recruiter_vendors_import.csv",
        ),
        "crm.lead": ("crm_opportunities_import.csv",),
        "hr.employee": ("employees_import.csv",),
        "intrastack.staffing.requirement": ("staffing_requirements_import.csv",),
        "intrastack.staffing.submission": ("staffing_candidate_submissions_import.csv",),
        "intrastack.staffing.interview": ("staffing_interviews_import.csv",),
        "intrastack.staffing.placement": ("staffing_placements_import.csv",),
        "res.bank": ("banks_import.csv",),
        "res.partner.bank": ("contact_bank_accounts_import.csv",),
    }

    def test_import_templates_are_exposed_for_operational_models(self):
        for model_name, filenames in self.EXPECTED_TEMPLATES.items():
            with self.subTest(model=model_name):
                templates = self.env[model_name].get_import_templates()
                urls = {item["template"] for item in templates}
                for filename in filenames:
                    self.assertIn(
                        "/intrastack_crm/static/xls/%s" % filename,
                        urls,
                        "%s does not expose %s" % (model_name, filename),
                    )

    def test_standard_odoo_templates_are_preserved(self):
        expected_urls = {
            "res.partner": "/base/static/xls/res_partner.xlsx",
            "crm.lead": "/crm/static/xls/crm_lead.xls",
            "hr.employee": "/hr/static/xls/hr_employee.xls",
        }
        for model_name, expected_url in expected_urls.items():
            with self.subTest(model=model_name):
                templates = self.env[model_name].get_import_templates()
                self.assertIn(expected_url, {item["template"] for item in templates})

    def test_downloadable_template_files_exist(self):
        filenames = {
            filename
            for model_filenames in self.EXPECTED_TEMPLATES.values()
            for filename in model_filenames
        }
        for filename in filenames:
            with self.subTest(filename=filename):
                path = file_path("intrastack_crm/static/xls/%s" % filename)
                self.assertTrue(path and os.path.isfile(path), "%s is missing" % filename)
