# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    owner_invoice_fee_product_id = fields.Many2one(
        related="company_id.owner_invoice_fee_product_id", readonly=False
    )
    owner_invoice_material_product_id = fields.Many2one(
        related="company_id.owner_invoice_material_product_id", readonly=False
    )
    owner_invoice_pricelist_id = fields.Many2one(
        related="company_id.owner_invoice_pricelist_id", readonly=False
    )
