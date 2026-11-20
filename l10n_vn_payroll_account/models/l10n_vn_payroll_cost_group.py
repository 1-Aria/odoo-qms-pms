# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnPayrollCostGroup(models.Model):
    _name = "l10n_vn.payroll.cost.group"
    _description = "Payroll Cost Group"
    _order = "code"
    _check_company_auto = True

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    expense_account_id = fields.Many2one(
        "account.account", string="Expense Account", required=True, check_company=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "code_company_unique",
            "unique(code, company_id)",
            "A cost group code is unique in a company.",
        ),
    ]
