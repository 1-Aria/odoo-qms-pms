# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    l10n_vn_cost_group_id = fields.Many2one(
        "l10n_vn.payroll.cost.group",
        string="Payroll Cost Group",
        help="Overrides the department's.",
        groups="payroll.group_payroll_user",
        check_company=True,
        tracking=True,
    )
