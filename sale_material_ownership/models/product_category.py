# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    material_ownership = fields.Boolean(
        string="Counts as Material",
        help="Products of this category are materials for ownership between the garment "
        "company and the trading company: owned through vendor bills, used by the sales "
        "orders that contain them. Not inherited by sub-categories.",
    )
