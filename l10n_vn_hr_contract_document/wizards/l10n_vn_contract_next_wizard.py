# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models


class L10nVnContractNextWizard(models.TransientModel):
    """The next contract: a renewal, or probation or training followed by a labour contract (D49)."""

    _name = "l10n_vn.contract.next.wizard"
    _description = "Next Contract"

    contract_id = fields.Many2one("hr.contract", required=True, ondelete="cascade")
    date_start = fields.Date(required=True)
    contract_type_id = fields.Many2one("hr.contract.type", required=True)
    date_end = fields.Date()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        contract = self.env["hr.contract"].browse(
            values.get("contract_id") or self.env.context.get("default_contract_id")
        ).sudo()
        if not contract:
            return values
        if "date_start" in fields_list and not values.get("date_start"):
            values["date_start"] = (
                contract.date_end + datetime.timedelta(days=1)
                if contract.date_end
                else fields.Date.context_today(self)
            )
        if "contract_type_id" in fields_list and not values.get("contract_type_id"):
            contract_type = contract.contract_type_id
            if contract._l10n_vn_document_kind_value() == "probation":
                contract_type = self.env["hr.contract.type"].search(
                    [("l10n_vn_document_kind", "=", "labour")], limit=1
                ) or contract_type
            values["contract_type_id"] = contract_type.id
        return values

    def action_create_contract(self):
        self.ensure_one()
        new = self.contract_id._l10n_vn_next_contract(
            self.date_start, self.contract_type_id, self.date_end
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.contract",
            "res_id": new.id,
            "view_mode": "form",
            "target": "current",
        }
