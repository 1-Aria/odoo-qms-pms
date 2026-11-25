# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    production_owned = fields.Boolean(
        string="Products Belong to the Owner",
        default=True,
        help="Manufacturing orders of this type produce goods owned by their owner, left "
        "out of valuation (contract processing). Off: the goods remain the company's, "
        "valued at its input, for sale on the sales order (order processing).",
    )
    owner_from_partner = fields.Boolean(
        help="Transfers of this type assign the goods to their partner as owner, or, "
        "without a partner, to the customer of their sales order. Manufacturing orders "
        "of this type take the customer of their sales order as owner. An owner set by "
        "hand is kept.",
    )
