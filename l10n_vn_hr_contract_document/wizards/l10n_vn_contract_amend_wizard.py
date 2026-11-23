# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnContractAmendWizard(models.TransientModel):
    """Open an amendment on an approved contract (D39)."""

    _name = "l10n_vn.contract.amend.wizard"
    _description = "Amend Contract"

    contract_id = fields.Many2one("hr.contract", required=True, ondelete="cascade")
    effective_date = fields.Date(required=True, default=fields.Date.context_today)
    reason = fields.Char(required=True)

    def action_open_amendment(self):
        self.ensure_one()
        self.contract_id._l10n_vn_amend(self.effective_date, self.reason)
        return {"type": "ir.actions.act_window_close"}
