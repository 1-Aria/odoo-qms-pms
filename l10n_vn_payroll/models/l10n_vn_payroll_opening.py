# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnPayrollOpening(models.Model):
    """Year-to-date figures of the months paid before go-live (D88)."""

    _name = "l10n_vn.payroll.opening"
    _description = "Payroll Opening Data"
    _order = "year desc, employee_id"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    employee_id = fields.Many2one("hr.employee", required=True, check_company=True)
    year = fields.Integer(required=True)
    months = fields.Integer(help="Months paid outside the module.")
    income = fields.Monetary()
    income_exempt = fields.Monetary(string="Exempt Income")
    insurance = fields.Monetary()
    family_deduction = fields.Monetary()
    taxable = fields.Monetary(string="Taxable Income")
    pit = fields.Monetary(string="PIT")
    ot_hours = fields.Float(string="OT Hours", digits=(16, 4))
    note = fields.Char()

    _sql_constraints = [
        (
            "employee_year_unique",
            "unique(company_id, employee_id, year)",
            "An employee has one row of opening data per year.",
        ),
    ]
