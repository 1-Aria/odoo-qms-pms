# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    owner_id = fields.Many2one(
        "res.partner",
        string="Goods Owner",
        index=True,
        copy=True,
        tracking=True,
        help="The partner who owns the components taken first and the goods produced. "
        "Empty: the company's own production, from the company's stock only.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        # After super(): the operation type may come from its default.
        for production, vals in zip(productions, vals_list):
            if "owner_id" not in vals and production.picking_type_id.owner_partner_id:
                # write() puts the owner on the finished moves.
                production.owner_id = production.picking_type_id.owner_partner_id
            elif production.owner_id:
                # The form sends the owner and the finished moves in the same
                # create, the moves without the owner.
                production.move_finished_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                ).write({"restrict_partner_id": production.owner_id.id})
        return productions

    def write(self, vals):
        res = super().write(vals)
        if "owner_id" in vals:
            for production in self:
                production.move_finished_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                ).write({"restrict_partner_id": production.owner_id.id})
        return res

    @api.onchange("picking_type_id")
    def _onchange_owner_from_type(self):
        if self.state in ("draft", "confirmed"):
            self.owner_id = self.picking_type_id.owner_partner_id

    def _get_move_finished_values(
        self,
        product_id,
        product_uom_qty,
        product_uom,
        operation_id=False,
        byproduct_id=False,
        cost_share=0,
    ):
        values = super()._get_move_finished_values(
            product_id,
            product_uom_qty,
            product_uom,
            operation_id=operation_id,
            byproduct_id=byproduct_id,
            cost_share=cost_share,
        )
        if self.owner_id:
            values["restrict_partner_id"] = self.owner_id.id
        return values

    def _get_backorder_mo_vals(self):
        values = super()._get_backorder_mo_vals()
        values["owner_id"] = self.owner_id.id
        return values
