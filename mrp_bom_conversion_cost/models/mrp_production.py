# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # Core's field (mrp_account), made a stored compute. A value given at
    # create() wins, so splits and backorders keep the figure they copy.
    # The column already exists, so installing recomputes no existing MO.
    extra_cost = fields.Float(
        compute="_compute_extra_cost",
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends("bom_id")
    def _compute_extra_cost(self):
        for production in self:
            bom = production.bom_id
            if bom.type == "normal" and bom.conversion_minutes:
                production.extra_cost = (
                    bom.conversion_minutes
                    * production.company_id.conversion_cost_rate
                )
            else:
                production.extra_cost = 0.0
