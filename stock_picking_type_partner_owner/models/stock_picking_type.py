# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    owner_from_partner = fields.Boolean(
        string="Partner Owns the Goods",
        help="Transfers of this type assign the goods to their partner as owner, or, "
        "without a partner, to the customer of their sales order. An owner set by "
        "hand is kept.",
    )
