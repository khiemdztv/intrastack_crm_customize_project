"""Downloadable CSV templates shown directly on Odoo import screens."""

from odoo import _, api, models


def _template(label, filename):
    return {
        "label": label,
        "template": "/intrastack_crm/static/xls/%s" % filename,
    }


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_import_templates(self):
        return super().get_import_templates() + [
            _template(_("IntraStack Template - Customer Companies"), "crm_companies_import.csv"),
            _template(_("IntraStack Template - Company Contacts"), "crm_contacts_import.csv"),
            _template(_("IntraStack Template - Candidates"), "crm_candidates_import.csv"),
            _template(_("IntraStack Template - Recruiter Vendors"), "crm_recruiter_vendors_import.csv"),
        ]


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def get_import_templates(self):
        return super().get_import_templates() + [
            _template(_("IntraStack Template - CRM Opportunities"), "crm_opportunities_import.csv"),
        ]


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def get_import_templates(self):
        return super().get_import_templates() + [
            _template(_("IntraStack Template - Employees and Roles"), "employees_import.csv"),
        ]


class StaffingRequirement(models.Model):
    _inherit = "intrastack.staffing.requirement"

    @api.model
    def get_import_templates(self):
        return [
            _template(_("IntraStack Template - Staffing Requirements"), "staffing_requirements_import.csv"),
        ]


class StaffingSubmission(models.Model):
    _inherit = "intrastack.staffing.submission"

    @api.model
    def get_import_templates(self):
        return [
            _template(_("IntraStack Template - Candidate Submissions"), "staffing_candidate_submissions_import.csv"),
        ]


class StaffingInterview(models.Model):
    _inherit = "intrastack.staffing.interview"

    @api.model
    def get_import_templates(self):
        return [
            _template(_("IntraStack Template - Interview Schedule"), "staffing_interviews_import.csv"),
        ]


class StaffingPlacement(models.Model):
    _inherit = "intrastack.staffing.placement"

    @api.model
    def get_import_templates(self):
        return [
            _template(_("IntraStack Template - Staffing Placements"), "staffing_placements_import.csv"),
        ]


class ResBank(models.Model):
    _inherit = "res.bank"

    @api.model
    def get_import_templates(self):
        return [
            _template(_("IntraStack Template - Banks"), "banks_import.csv"),
        ]


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.model
    def get_import_templates(self):
        return [
            _template(_("IntraStack Template - Contact Bank Accounts"), "contact_bank_accounts_import.csv"),
        ]
