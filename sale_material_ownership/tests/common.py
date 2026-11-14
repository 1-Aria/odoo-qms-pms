# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import itertools
from datetime import timedelta

from odoo import Command, fields
from odoo.tests import TransactionCase

_einvoice_numbers = itertools.count(1)


class MaterialOwnershipCase(TransactionCase):
    """Shared fixtures; holds no test methods.

    A Vietnamese company of its own with the vn chart, materials and goods at average
    cost with real-time valuation, a shirt made of a cut panel (fabric) and buttons.
    Built on TransactionCase, not on account's AccountTestInvoicingCommon, whose
    package cannot be imported on this image.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Material Ownership Test Company",
                "country_id": cls.env.ref("base.vn").id,
                "currency_id": cls.env.ref("base.VND").id,
            }
        )
        cls.env.user.company_ids = [Command.link(cls.company.id)]
        cls.env["account.chart.template"].try_loading(
            "vn", company=cls.company, install_demo=False
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )

        Account = cls.env["account.account"]

        def account(code, name, account_type):
            return Account.create(
                {
                    "code": code,
                    "name": name,
                    "account_type": account_type,
                    "company_ids": [Command.set(cls.company.ids)],
                }
            )

        # The chart's raw-materials account; the vn chart pads codes to four digits.
        cls.account_1520 = cls.env.ref(f"account.{cls.company.id}_chart152")
        cls.account_3399 = account("3399", "GRNP (test)", "liability_current")
        cls.account_1599 = account("1599", "GINI (test)", "asset_current")
        cls.account_33889 = account("33889", "Pre-opening clearing (test)", "liability_current")
        stock_journal = cls.env["account.journal"].search(
            [("code", "=", "STJ"), ("company_id", "=", cls.company.id)], limit=1
        )

        Category = cls.env["product.category"].with_company(cls.company)
        category_vals = {
            "property_valuation": "real_time",
            "property_cost_method": "average",
            "property_stock_valuation_account_id": cls.account_1520.id,
            "property_stock_account_input_categ_id": cls.account_3399.id,
            "property_stock_account_output_categ_id": cls.account_1599.id,
            "property_stock_journal": stock_journal.id,
        }
        cls.categ_material = Category.create(
            {"name": "MO Test Materials", "material_ownership": True, **category_vals}
        )
        cls.categ_goods = Category.create({"name": "MO Test Goods", **category_vals})

        Product = cls.env["product.product"].with_company(cls.company)
        meter = cls.env.ref("uom.product_uom_meter")

        def product(name, code, categ, **vals):
            return Product.create(
                {
                    "name": name,
                    "default_code": code,
                    "is_storable": True,
                    "categ_id": categ.id,
                    **vals,
                }
            )

        cls.fabric = product(
            "MO Fabric",
            "MOFAB",
            cls.categ_material,
            uom_id=meter.id,
            uom_po_id=meter.id,
            standard_price=50000.0,
            purchase_method="receive",
        )
        cls.button = product(
            "MO Button",
            "MOBTN",
            cls.categ_material,
            standard_price=500.0,
            purchase_method="receive",
        )
        cls.panel = product("MO Panel", "MOPNL", cls.categ_goods)
        cls.shirt = product("MO Shirt", "MOSHT", cls.categ_goods)
        cls.towel = product("MO Towel", "MOTWL", cls.categ_goods)
        cls.service = Product.create({"name": "MO Service", "type": "service"})

        # mrp_bom_version creates BoMs archived outside test runs: set active explicitly.
        Bom = cls.env["mrp.bom"]
        cls.bom_panel = Bom.create(
            {
                "product_tmpl_id": cls.panel.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "company_id": cls.company.id,
                "active": True,
                "bom_line_ids": [
                    Command.create({"product_id": cls.fabric.id, "product_qty": 1.5})
                ],
            }
        )
        cls.bom_shirt = Bom.create(
            {
                "product_tmpl_id": cls.shirt.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "company_id": cls.company.id,
                "active": True,
                "bom_line_ids": [
                    Command.create({"product_id": cls.panel.id, "product_qty": 1.0}),
                    Command.create({"product_id": cls.button.id, "product_qty": 5.0}),
                ],
            }
        )

        Partner = cls.env["res.partner"]
        cls.supplier = Partner.create({"name": "MO Supplier"})
        cls.trading = Partner.create({"name": "MO Trading Company"})
        cls.customer = Partner.create({"name": "MO Customer"})
        cls.fiscal_position = cls.env["account.fiscal.position"].create(
            {
                "name": "MO Material Transfer",
                "company_id": cls.company.id,
                "account_ids": [
                    Command.create(
                        {
                            "account_src_id": cls.account_3399.id,
                            "account_dest_id": cls.account_33889.id,
                        }
                    )
                ],
            }
        )
        cls.start = fields.Date.today() - timedelta(days=30)
        cls.company.write(
            {
                "material_ownership_start": cls.start,
                "material_owner_partner_id": cls.trading.id,
                "material_fiscal_position_id": cls.fiscal_position.id,
            }
        )

        cls.salesman = cls._user("mo_test_salesman", ["sales_team.group_sale_salesman"])
        cls.sale_manager = cls._user("mo_test_sale_manager", ["sales_team.group_sale_manager"])
        cls.accountant = cls._user(
            "mo_test_accountant",
            ["sales_team.group_sale_manager", "account.group_account_invoice"],
        )

    @classmethod
    def _user(cls, login, groups):
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": login,
                    "login": login,
                    "company_id": cls.company.id,
                    "company_ids": [Command.set(cls.company.ids)],
                    "groups_id": [Command.set([cls.env.ref(g).id for g in groups])],
                }
            )
        )

    def _as(self, user):
        return self.env(
            user=user, context=dict(self.env.context, allowed_company_ids=[self.company.id])
        )

    def _order(self, lines, partner=None, confirm=True, **vals):
        order = self.env["sale.order"].create(
            {
                "partner_id": (partner or self.customer).id,
                "company_id": self.company.id,
                "order_line": [
                    Command.create({"product_id": product.id, "product_uom_qty": qty})
                    for product, qty in lines
                ],
                **vals,
            }
        )
        if confirm:
            order.action_confirm()
        return order

    def _purchase(self, product, qty, receive=None):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.supplier.id,
                "company_id": self.company.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_qty": qty,
                            "price_unit": product.standard_price,
                        }
                    )
                ],
            }
        )
        order.button_confirm()
        receipt = order.picking_ids
        for move in receipt.move_ids:
            move.quantity = qty if receive is None else receive
            move.picked = True
        receipt.with_context(skip_backorder=True).button_validate()
        return order

    def _bill(self, purchase):
        purchase.action_create_invoice()
        bill = purchase.invoice_ids.sorted("id")[-1:]
        bill.invoice_date = fields.Date.context_today(bill)
        bill.action_post()
        return bill

    def _direct_bill(self, lines, refund=False):
        move = self.env["account.move"].create(
            {
                "move_type": "in_refund" if refund else "in_invoice",
                "partner_id": self.supplier.id,
                "invoice_date": fields.Date.context_today(self.env.user),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "quantity": qty,
                            "price_unit": product.standard_price,
                        }
                    )
                    for product, qty in lines
                ],
            }
        )
        move.action_post()
        return move

    def _einvoice(self, move, **overrides):
        sign = -1 if move and move.move_type in ("in_refund", "out_refund") else 1
        vals = {
            "direction": "received",
            "move_id": move.id if move else False,
            "company_id": self.company.id,
            "format_version": "2.1.0",
            "form": "1",
            "symbol": "C26TAA",
            "number": str(next(_einvoice_numbers)),
            "invoice_date": move.invoice_date if move else fields.Date.today(),
            "seller_vat": "0300000001",
            "currency_id": self.company.currency_id.id,
            "amount_untaxed": sign * move.amount_untaxed if move else 0.0,
            "amount_tax": sign * move.amount_tax if move else 0.0,
            "amount_total": sign * move.amount_total if move else 0.0,
        }
        vals.update(overrides)
        return self.env["l10n_vn.einvoice"].create(vals)

    def _counted_bill(self, product, qty):
        bill = self._bill(self._purchase(product, qty))
        self._einvoice(bill)
        return bill

    def _stock(self, product, qty):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.env["stock.quant"]._update_available_quantity(
            product, warehouse.lot_stock_id, qty
        )

    def _deliver(self, order, qty=None):
        """Validate the order's open delivery for qty (all when None); a backorder
        holds the rest."""
        picking = order.picking_ids.filtered(
            lambda p: p.picking_type_code == "outgoing" and p.state not in ("done", "cancel")
        )[:1]
        picking.action_assign()
        for move in picking.move_ids.filtered(lambda m: m.state != "cancel"):
            move.quantity = move.product_uom_qty if qty is None else qty
            move.picked = True
        picking.with_context(skip_backorder=True).button_validate()
        self.assertEqual(picking.state, "done")
        return picking

    def _request(self, batch, user=None):
        self._as(user or self.accountant)["sale.material.batch"].browse(
            batch.id
        ).action_request()
        return batch

    def _post(self, bill):
        bill.invoice_date = fields.Date.context_today(bill)
        bill.action_post()
        return bill

    def _batch(self, *orders):
        return self.env["sale.material.batch"].create(
            {
                "company_id": self.company.id,
                "order_ids": [Command.link(order.id) for order in orders],
            }
        )

    def _q(self, *products):
        products = self.env["product.product"].union(*products)
        return self.env["sale.material.batch"]._ownership_quantities(self.company, products)
