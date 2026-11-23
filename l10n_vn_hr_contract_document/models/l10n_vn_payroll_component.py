# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# natures that never print in a contract (D1)
NOT_PRINTED = (
    "overtime",
    "night",
    "leave_pay",
    "severance",
    "statutory",
    "union",
    "damage",
    "advance",
    "adjustment",
    "total",
)


class L10nVnPayrollComponent(models.Model):
    _inherit = "l10n_vn.payroll.component"

    l10n_vn_contract_print = fields.Selection(
        [
            ("amount", "Amount"),
            ("reference", "By reference to the pay regulation"),
            ("welfare", "Bonus and welfare section"),
            ("none", "Not printed"),
        ],
        string="In the Contract",
        compute="_compute_l10n_vn_contract_print",
        store=True,
        readonly=False,
    )

    @api.depends("kind", "legal_nature", "variable")
    def _compute_l10n_vn_contract_print(self):
        for component in self:
            if component.kind != "earning" or component.legal_nature in NOT_PRINTED:
                component.l10n_vn_contract_print = "none"
            elif component.legal_nature in ("bonus", "welfare"):
                component.l10n_vn_contract_print = "welfare"
            elif component.variable or component.legal_nature == "variable_salary":
                component.l10n_vn_contract_print = "reference"
            else:
                component.l10n_vn_contract_print = "amount"
