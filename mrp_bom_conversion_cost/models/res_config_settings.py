# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    conversion_cost_rate = fields.Float(
        related="company_id.conversion_cost_rate",
        readonly=False,
    )
