# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _should_force_price_unit(self):
        """Keep a downgrade receipt at its price, even when that price is zero."""
        self.ensure_one()
        return bool(self.scrap_id and not self.scrapped) or super()._should_force_price_unit()
