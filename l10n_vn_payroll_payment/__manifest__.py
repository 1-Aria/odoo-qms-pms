# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Payroll Payment",
    "summary": "Salary advances and the payment lists of Vietnamese payroll runs",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Human Resources/Payroll",
    "countries": ["vn"],
    "depends": ["l10n_vn_payroll"],
    "data": [
        "security/l10n_vn_payroll_payment_security.xml",
        "security/ir.model.access.csv",
        "views/l10n_vn_payroll_advance_views.xml",
        "views/l10n_vn_payroll_advance_batch_views.xml",
        "wizards/l10n_vn_payroll_advance_pay_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
