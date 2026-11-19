# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    downgrade_categ_id = fields.Many2one(
        comodel_name="product.category",
        string="Downgrade Category",
        help="Scrapping into this location downgrades the goods: a product of this "
        "category is received in their place, at their cost.",
    )
