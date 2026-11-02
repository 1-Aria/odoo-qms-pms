# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vietnam - Payroll",
    "summary": "Vietnamese payroll on OCA payroll: pay components, scales and dated pay lines, "
    "SI, OT and PIT, statutory parameters",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Human Resources/Payroll",
    "countries": ["vn"],
    "depends": [
        "payroll",
        "base_time_parameter_strict",
        "hr_employee_relative",
    ],
    "data": [
        "security/l10n_vn_payroll_security.xml",
        "security/ir.model.access.csv",
        "data/l10n_vn_payroll_parameters.xml",
        "data/l10n_vn_payroll_participant_types.xml",
        "views/l10n_vn_payroll_component_views.xml",
        "views/l10n_vn_payroll_scale_views.xml",
        "views/l10n_vn_payroll_participant_type_views.xml",
        "views/hr_contract_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_employee_relative_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
