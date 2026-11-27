# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    owner_invoice_fee_product_id = fields.Many2one(
        "product.product", string="Processing Fee Product", domain=[("type", "=", "service")]
    )
    owner_invoice_material_product_id = fields.Many2one(
        "product.product", string="Supplied Material Product", domain=[("type", "=", "service")]
    )
    owner_invoice_pricelist_id = fields.Many2one(
        "product.pricelist", string="Processing Fee Pricelist"
    )
