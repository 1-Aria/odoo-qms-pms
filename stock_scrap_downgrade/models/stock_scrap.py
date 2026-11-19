# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    downgrade_categ_id = fields.Many2one(related="scrap_location_id.downgrade_categ_id")
    downgrade_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Downgrade To",
        compute="_compute_downgrade_product_id",
        store=True,
        readonly=False,
        check_company=True,
        domain="[('categ_id', 'child_of', downgrade_categ_id),"
        " ('uom_id.category_id', '=', product_uom_category_id),"
        " ('is_storable', '=', True),"
        " ('tracking', '=', 'none')]",
    )

    @api.depends("product_id", "scrap_location_id")
    def _compute_downgrade_product_id(self):
        for scrap in self:
            if scrap.downgrade_categ_id and scrap.product_id:
                scrap.downgrade_product_id = scrap._last_downgrade_product()
            else:
                scrap.downgrade_product_id = False

    def _last_downgrade_product(self):
        """Return the product of the last downgrade of this variant, else style.

        The domain leaves out ``downgrade_product_id``: this runs inside that
        field's compute, and searching on it would flush the compute itself.
        """
        self.ensure_one()
        domain = [
            ("state", "=", "done"),
            ("scrap_location_id", "=", self.scrap_location_id._origin.id),
        ]
        product = self.product_id._origin
        last = self.search(domain + [("product_id", "=", product.id)], limit=1)
        if not last:
            last = self.search(
                domain + [("product_id.product_tmpl_id", "=", product.product_tmpl_id.id)],
                limit=1,
            )
        return last.downgrade_product_id

    def do_scrap(self):
        downgrades = self.filtered("downgrade_categ_id")
        missing = downgrades.filtered(lambda scrap: not scrap.downgrade_product_id)
        if missing:
            raise UserError(
                self.env._(
                    "Choose the product to downgrade to for: %(products)s",
                    products=", ".join(missing.product_id.mapped("display_name")),
                )
            )
        result = super().do_scrap()
        for scrap in downgrades:
            scrap._receive_downgrade_product()
        return result

    def _receive_downgrade_product(self):
        """Receive the lower-grade product at the value the scrap took out."""
        self.ensure_one()
        product = self.downgrade_product_id
        quantity = self.product_uom_id._compute_quantity(self.scrap_qty, self.product_id.uom_id)
        # Only stock managers may read valuation layers.
        value = -sum(self.move_ids.sudo().stock_valuation_layer_ids.mapped("value"))
        warehouse = self.location_id.warehouse_id or self.env["stock.warehouse"].search(
            [("company_id", "=", self.company_id.id)], limit=1
        )
        destination = warehouse.lot_stock_id
        move = self.env["stock.move"].create(
            {
                "name": self.name,
                "origin": self.origin or self.name,
                "company_id": self.company_id.id,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": quantity,
                "location_id": self.scrap_location_id.id,
                "location_dest_id": destination.id,
                "price_unit": value / quantity,
                "scrap_id": self.id,
                "state": "draft",
                "picked": True,
                "move_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_id": product.uom_id.id,
                            "quantity": quantity,
                            "location_id": self.scrap_location_id.id,
                            "location_dest_id": destination.id,
                        }
                    )
                ],
            }
        )
        move._action_done()
