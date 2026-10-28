# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_vn_einvoice_ids = fields.One2many(
        comodel_name="l10n_vn.einvoice",
        inverse_name="move_id",
        string="E-Invoices",
        copy=False,
    )
    l10n_vn_einvoice_id = fields.Many2one(
        comodel_name="l10n_vn.einvoice",
        string="E-Invoice",
        compute="_compute_l10n_vn_einvoice_id",
    )

    @api.depends("l10n_vn_einvoice_ids")
    def _compute_l10n_vn_einvoice_id(self):
        for move in self:
            move.l10n_vn_einvoice_id = move.l10n_vn_einvoice_ids[:1]

    def action_l10n_vn_einvoice_attach(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_vn_einvoice.l10n_vn_einvoice_attach_action"
        )
        action["context"] = {"default_move_id": self.id}
        return action

    def action_l10n_vn_einvoice_open(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_vn.einvoice",
            "res_id": self.l10n_vn_einvoice_id.id,
            "views": [(False, "form")],
            "view_mode": "form",
        }
