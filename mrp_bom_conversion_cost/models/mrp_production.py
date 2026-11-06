# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    conversion_rate_id = fields.Many2one(
        "mrp.conversion.cost.rate",
        string="Conversion Cost Rate",
        readonly=True,
        copy=False,
        ondelete="restrict",
        index="btree_not_null",
    )
    conversion_minutes = fields.Float(
        string="Conversion Minutes",
        digits=(16, 4),
        readonly=True,
        copy=False,
        help="The BoM's conversion minutes when the order was valued.",
    )
    conversion_cost_estimate = fields.Float(
        string="Estimated Extra Unit Cost",
        digits="Product Price",
        compute="_compute_conversion_cost_estimate",
    )

    def _conversion_cost_bom(self):
        """The BoM this module values the MO from, or an empty recordset:
        normal BoMs with minutes only. Other MOs are left as they are."""
        self.ensure_one()
        bom = self.bom_id
        if bom.type == "normal" and bom.conversion_minutes > 0:
            return bom
        return self.env["mrp.bom"]

    @api.depends("bom_id", "bom_id.type", "bom_id.conversion_minutes", "company_id")
    def _compute_conversion_cost_estimate(self):
        Rate = self.env["mrp.conversion.cost.rate"]
        for production in self:
            bom = production._conversion_cost_bom()
            rate = Rate
            if bom:
                rate = Rate._rate_on(
                    production.company_id, fields.Date.context_today(production)
                )
            production.conversion_cost_estimate = (
                bom.conversion_minutes * rate.rate if rate else 0.0
            )

    def _cal_price(self, consumed_moves):
        bom = self._conversion_cost_bom()
        if bom:
            # The date stock entries post on (stock_account's stock_move.py).
            date = self.env.context.get(
                "force_period_date"
            ) or fields.Date.context_today(self)
            rate = self.env["mrp.conversion.cost.rate"]._rate_on(self.company_id, date)
            if not rate:
                raise UserError(
                    self.env._(
                        "%(mo)s cannot be valued: no approved conversion cost "
                        "rate for %(company)s is in force on %(date)s. An "
                        "accounting administrator approves one under "
                        "Configuration → Conversion Cost Rates.",
                        mo=self.display_name,
                        company=self.company_id.display_name,
                        date=format_date(self.env, date),
                    )
                )
            self.write(
                {
                    "conversion_rate_id": rate.id,
                    "conversion_minutes": bom.conversion_minutes,
                    "extra_cost": bom.conversion_minutes * rate.rate,
                }
            )
        return super()._cal_price(consumed_moves)
