# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .sale_order import COVERAGE


class StockPicking(models.Model):
    _inherit = "stock.picking"

    material_coverage = fields.Selection(
        selection=COVERAGE,
        string="Material Coverage",
        compute="_compute_material_coverage",
        compute_sudo=True,
    )

    @api.depends("sale_id")
    def _compute_material_coverage(self):
        for picking in self:
            picking.material_coverage = picking.sale_id.material_coverage
