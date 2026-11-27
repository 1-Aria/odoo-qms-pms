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
    production_owned = fields.Boolean(
        string="Products Belong to the Owner",
        default=True,
        copy=True,
        help="The goods produced belong to the order's owner and stay out of valuation. "
        "Off: they remain the company's, valued at its input, for sale on the sales "
        "order (order processing).",
    )

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        # After super(): the operation type may come from its default.
        for production, vals in zip(productions, vals_list):
            updates = {}
            parent = production._get_parent_production()
            if "production_owned" not in vals:
                updates["production_owned"] = (
                    parent.production_owned if parent and "owner_id" not in vals
                    else production.picking_type_id.production_owned
                )
            if "owner_id" not in vals:
                owner = parent.owner_id if parent else production.picking_type_id.owner_partner_id
                if owner:
                    updates["owner_id"] = owner.id
            if updates:
                # write() puts the owner on the finished moves.
                production.write(updates)
            elif production.owner_id:
                # The form sends the owner and the finished moves in the same
                # create, the moves without the owner.
                production._set_finished_owner()
        return productions

    def write(self, vals):
        res = super().write(vals)
        if "owner_id" in vals or "production_owned" in vals:
            self._set_finished_owner()
        return res

    def _set_finished_owner(self):
        for production in self:
            owner = production.owner_id if production.production_owned else self.env["res.partner"]
            moves = production.move_finished_ids.filtered(
                lambda m: m.state not in ("done", "cancel")
            )
            moves.write({"restrict_partner_id": owner.id})
            # Lines created before the owner changed (at confirmation, or when the
            # quantity to produce was set) keep their own owner at validation.
            moves.move_line_ids.filtered(
                lambda line: line.state not in ("done", "cancel") and line.owner_id != owner
            ).write({"owner_id": owner.id})

    def _get_parent_production(self):
        """The order whose component this order makes, as core reads it."""
        self.ensure_one()
        return self.move_dest_ids.raw_material_production_id[:1]

    def _get_sale_owner(self):
        """The commercial partner of the customer of the sales order behind the
        order, when sale_stock links groups to sales orders (read as superuser)."""
        self.ensure_one()
        group = self.procurement_group_id
        if "sale_id" in group._fields:
            customer = group.sudo().sale_id.partner_id.commercial_partner_id
            return self.env["res.partner"].browse(customer.ids)
        return self.env["res.partner"]

    @api.onchange("picking_type_id")
    def _onchange_owner_from_type(self):
        if self.state in ("draft", "confirmed"):
            self.production_owned = self.picking_type_id.production_owned
            owner = self.picking_type_id.owner_partner_id
            if not owner and self.picking_type_id.owner_from_partner:
                owner = self._get_sale_owner()
            self.owner_id = owner

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
        if self.owner_id and self.production_owned:
            values["restrict_partner_id"] = self.owner_id.id
        return values

    def _get_backorder_mo_vals(self):
        values = super()._get_backorder_mo_vals()
        values["owner_id"] = self.owner_id.id
        values["production_owned"] = self.production_owned
        return values
