# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnPayrollComponent(models.Model):
    _inherit = "l10n_vn.payroll.component"

    # the side follows the component's kind (D2)
    l10n_vn_account_id = fields.Many2one(
        "account.account",
        string="Account",
        check_company=True,
        help="Earnings: the expense account, when not the cost group's. "
        "Deductions and employer contributions: the account credited.",
    )
