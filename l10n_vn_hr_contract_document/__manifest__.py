# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Labour Contract Documents",
    "summary": "Labour, probation and training contracts printed from the Odoo contract",
    "version": "18.0.1.2.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Human Resources/Contracts",
    "countries": ["vn"],
    "depends": [
        "l10n_vn_payroll",
    ],
    "external_dependencies": {"python": ["num2words"]},
    "data": [
        "security/l10n_vn_contract_document_security.xml",
        "security/ir.model.access.csv",
        "data/report_paperformat.xml",
        "report/l10n_vn_contract_document_templates.xml",
        "report/l10n_vn_contract_annex_templates.xml",
        "report/l10n_vn_contract_document_reports.xml",
        "data/l10n_vn_contract_actions.xml",
        "wizards/l10n_vn_contract_wizard_views.xml",
        "views/res_company_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_contract_type_views.xml",
        "views/hr_contract_views.xml",
        "views/l10n_vn_payroll_component_views.xml",
        "views/l10n_vn_contract_wording_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "l10n_vn_hr_contract_document/static/src/scss/l10n_vn_contract_document.scss",
        ],
    },
    "installable": True,
}
