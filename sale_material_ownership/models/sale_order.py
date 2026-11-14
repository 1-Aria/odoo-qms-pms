# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare

COVERAGE = [
    ("not_needed", "Not needed"),
    ("not_batched", "Not batched"),
    ("partly", "Partly batched"),
    ("draft", "In a draft batch"),
    ("requested", "Requested"),
    ("covered", "Covered"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    material_batch_ids = fields.Many2many(
        comodel_name="sale.material.batch",
        relation="sale_material_batch_order_rel",
        column1="order_id",
        column2="batch_id",
        string="Transfer Batches",
        readonly=True,
        copy=False,
    )
    material_coverage = fields.Selection(
        selection=COVERAGE,
        string="Material Coverage",
        compute="_compute_material_coverage",
        compute_sudo=True,
        search="_search_material_coverage",
    )

    @api.depends(
        "state",
        "date_order",
        "company_id.material_ownership_start",
        "order_line.material_need_ids.batch_id.state",
    )
    def _compute_material_coverage(self):
        for order in self:
            if order.state != "sale":
                order.material_coverage = False
                continue
            lines = order.order_line._material_lines()
            if not lines or not order._material_in_scope():
                order.material_coverage = "not_needed"
                continue
            states = [line._material_batch_needs()[:1].batch_id.state for line in lines]
            if not any(states):
                coverage = "not_batched"
            elif not all(states):
                coverage = "partly"
            elif "draft" in states:
                coverage = "draft"
            elif "requested" in states:
                coverage = "requested"
            else:
                coverage = "covered"
            order.material_coverage = coverage

    def _material_in_scope(self):
        """Confirmed on or after the company's ownership start, in the user's time zone.
        Without a start date, no order is in scope."""
        self.ensure_one()
        start = self.company_id.material_ownership_start
        if not start or not self.date_order:
            return False
        return fields.Datetime.context_timestamp(self, self.date_order).date() >= start

    def _search_material_coverage(self, operator, value):
        if operator not in ("=", "!=", "in", "not in"):
            raise NotImplementedError(operator)
        values = value if isinstance(value, (list, tuple, set)) else [value]
        orders = self.search([("state", "=", "sale")])
        ids = orders.filtered(lambda o: o.material_coverage in values).ids
        if operator in ("=", "in"):
            return [("id", "in", ids)]
        return [("id", "not in", ids)]


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    material_need_ids = fields.One2many(
        comodel_name="sale.material.batch.need",
        inverse_name="order_line_id",
        readonly=True,
        copy=False,
    )

    def _material_lines(self):
        """The lines whose goods carry materials (spec D2)."""
        return self.filtered(
            lambda line: line.product_id
            and line.product_id.type == "consu"
            and not line.display_type
            and not line.is_downpayment
            and line.product_uom_qty > 0
        )

    def _material_batch_needs(self):
        return self.material_need_ids.filtered(lambda n: n.batch_id.state != "cancel")

    def _material_effective_qty(self, line_qty):
        """The quantity a batched line counts for, in its product's UoM (spec D8): 0 on a
        cancelled order; what was delivered once delivered >= ordered; otherwise the
        larger of the frozen quantity and what was delivered."""
        self.ensure_one()
        if self.order_id.state == "cancel":
            return 0.0
        uom = self.product_id.uom_id
        delivered = self.product_uom._compute_quantity(self.qty_delivered, uom, round=False)
        ordered = self.product_uom._compute_quantity(self.product_uom_qty, uom, round=False)
        if float_compare(delivered, ordered, precision_rounding=uom.rounding) >= 0:
            return delivered
        return max(line_qty, delivered)
