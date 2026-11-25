# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    def _get_production_owner(self):
        """The order's owner when it holds stock of the product at the scrap's
        location: the owner's goods first, as in reservation."""
        self.ensure_one()
        owner = self.production_id.owner_id
        if not owner or not self.product_id or not self.location_id:
            return self.env["res.partner"]
        quants = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("location_id", "child_of", self.location_id.id),
                ("owner_id", "=", owner.id),
            ]
        )
        if sum(quants.mapped("quantity")) > 0:
            return owner
        return self.env["res.partner"]

    @api.model_create_multi
    def create(self, vals_list):
        scraps = super().create(vals_list)
        for scrap, vals in zip(scraps, vals_list):
            if "owner_id" not in vals:
                owner = scrap._get_production_owner()
                if owner:
                    scrap.owner_id = owner
        return scraps

    @api.onchange("product_id", "production_id", "location_id")
    def _onchange_owner_from_production(self):
        owner = self._get_production_owner()
        if owner:
            self.owner_id = owner
