# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Payroll Payment",
    "summary": "Salary advances and the payment lists of Vietnamese payroll runs",
    "version": "18.0.1.1.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Human Resources/Payroll",
    "countries": ["vn"],
    "depends": ["l10n_vn_payroll", "excel_import_export"],
    "data": [
        "security/l10n_vn_payroll_payment_security.xml",
        "security/ir.model.access.csv",
        "views/l10n_vn_payroll_advance_views.xml",
        "views/l10n_vn_payroll_advance_batch_views.xml",
        "views/l10n_vn_payroll_payment_views.xml",
        "wizards/l10n_vn_payroll_payment_pay_views.xml",
        "report/l10n_vn_payroll_cash_list.xml",
        "data/l10n_vn_payroll_payment_templates.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
