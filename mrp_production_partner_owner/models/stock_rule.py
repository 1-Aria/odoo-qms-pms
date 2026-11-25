# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_mo_vals(
        self, product_id, product_qty, product_uom, location_dest_id, name, origin,
        company_id, values, bom,
    ):
        vals = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_dest_id, name, origin,
            company_id, values, bom,
        )
        # The owner must be on the order before the rule confirms it, which
        # reserves its components (mrp/models/stock_rule.py, _run_manufacture);
        # sale_mrp links the sales order to the order only afterwards.
        picking_type = self.picking_type_id
        group = values.get("group_id")
        if (
            "owner_id" not in vals
            and picking_type.owner_from_partner
            and not picking_type.owner_partner_id
            and group
            and "sale_id" in group._fields
            # A child order takes its parent's owner instead (mrp.production.create);
            # from a sales order the destination is its delivery move.
            and not (values.get("move_dest_ids") or self.env["stock.move"]).raw_material_production_id
        ):
            customer = group.sudo().sale_id.partner_id.commercial_partner_id
            if customer:
                vals["owner_id"] = customer.id
        return vals
