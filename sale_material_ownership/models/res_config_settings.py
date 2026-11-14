# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    material_ownership_start = fields.Date(
        related="company_id.material_ownership_start", readonly=False
    )
    material_owner_partner_id = fields.Many2one(
        related="company_id.material_owner_partner_id", readonly=False
    )
    material_fiscal_position_id = fields.Many2one(
        related="company_id.material_fiscal_position_id",
        readonly=False,
        domain="[('company_id', '=', company_id)]",
    )
