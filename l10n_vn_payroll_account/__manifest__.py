# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Payroll Accounting",
    "summary": "Journal entries for Vietnamese payroll runs and their payments, "
    "3341 reconciled per employee",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Human Resources/Payroll",
    "countries": ["vn"],
    "depends": ["l10n_vn_payroll_payment", "payroll_account"],
    "data": [
        "security/l10n_vn_payroll_account_security.xml",
        "security/ir.model.access.csv",
        "data/l10n_vn_payroll_account_checks.xml",
        "views/l10n_vn_payroll_cost_group_views.xml",
        "views/hr_department_views.xml",
        "views/hr_contract_views.xml",
        "views/l10n_vn_payroll_component_views.xml",
        "views/hr_payslip_run_views.xml",
        "views/l10n_vn_payroll_payment_views.xml",
        "views/res_config_settings_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
