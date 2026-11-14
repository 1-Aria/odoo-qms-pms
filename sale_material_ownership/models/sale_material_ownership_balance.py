# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_is_zero

QTY = "Product Unit of Measure"


class SaleMaterialOwnershipBalance(models.TransientModel):
    _name = "sale.material.ownership.balance"
    _description = "Material Ownership Balance"
    _order = "categ_id, product_id"

    company_id = fields.Many2one(comodel_name="res.company", required=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    product_id = fields.Many2one(comodel_name="product.product", string="Material")
    categ_id = fields.Many2one(comodel_name="product.category", string="Category")
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit")
    qty_in = fields.Float(string="Owned by Bills", digits=QTY)
    qty_used = fields.Float(string="Used by Batches", digits=QTY)
    qty_balance = fields.Float(string="Balance", digits=QTY)
    qty_pending = fields.Float(string="Pending Requests", digits=QTY)
    qty_awaiting = fields.Float(string="Awaiting E-Invoice", digits=QTY)
    qty_not_received = fields.Float(string="Billed, Not Received", digits=QTY)
    qty_no_receipt = fields.Float(string="Not Linked to a Receipt", digits=QTY)
    qty_on_hand = fields.Float(string="On Hand", digits=QTY)
    qty_not_owned = fields.Float(string="On Hand, Not Owned", digits=QTY)
    unit_cost = fields.Float(digits="Product Price", aggregator=None)
    value_on_hand = fields.Monetary(string="Value On Hand")
    value_not_owned = fields.Monetary(string="Value Not Owned")

    @api.model
    def action_open(self):
        company = self.env.company
        quantities = self.env["sale.material.batch"]._ownership_quantities(company)
        on_hand = {
            product.id: qty
            for product, qty in self.env["stock.quant"]
            .sudo()
            ._read_group(
                [
                    ("company_id", "=", company.id),
                    ("location_id.usage", "=", "internal"),
                    ("product_id.categ_id.material_ownership", "=", True),
                ],
                ["product_id"],
                ["quantity:sum"],
            )
        }
        products = (
            self.env["product.product"]
            .sudo()
            .with_company(company)
            .browse(sorted(set(quantities) | set(on_hand)))
        )
        vals_list = []
        for product in products:
            figures = quantities[product.id]
            qty_on_hand = on_hand.get(product.id, 0.0)
            rounding = product.uom_id.rounding
            if all(
                float_is_zero(value, precision_rounding=rounding)
                for value in (*figures.values(), qty_on_hand)
            ):
                continue
            balance = figures["in"] - figures["used"]
            not_owned = max(qty_on_hand - max(balance, 0.0), 0.0)
            unit_cost = product.standard_price
            vals_list.append(
                {
                    "company_id": company.id,
                    "product_id": product.id,
                    "categ_id": product.categ_id.id,
                    "uom_id": product.uom_id.id,
                    "qty_in": figures["in"],
                    "qty_used": figures["used"],
                    "qty_balance": balance,
                    "qty_pending": figures["pending"],
                    "qty_awaiting": figures["awaiting"],
                    "qty_not_received": figures["not_received"],
                    "qty_no_receipt": figures["no_receipt"],
                    "qty_on_hand": qty_on_hand,
                    "qty_not_owned": not_owned,
                    "unit_cost": unit_cost,
                    "value_on_hand": company.currency_id.round(qty_on_hand * unit_cost),
                    "value_not_owned": company.currency_id.round(not_owned * unit_cost),
                }
            )
        rows = self.create(vals_list)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Material Ownership Balance"),
            "res_model": self._name,
            "view_mode": "list,pivot",
            "views": [(False, "list"), (False, "pivot")],
            "domain": [("id", "in", rows.ids)],
            "context": {"create": False},
        }
