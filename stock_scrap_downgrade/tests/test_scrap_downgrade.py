# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestScrapDowngrade(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Scrap Downgrade Test Company",
                "country_id": cls.env.ref("base.vn").id,
                "currency_id": cls.env.ref("base.VND").id,
            }
        )
        cls.env.user.company_ids = [Command.link(cls.company.id)]
        cls.env["account.chart.template"].try_loading(
            "vn", company=cls.company, install_demo=False
        )
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=cls.company.ids))
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.stock = cls.warehouse.lot_stock_id

        cls.valuation_account = cls._account("155901", "asset_current")
        cls.input_account = cls._account("155902", "asset_current")
        cls.output_account = cls._account("155903", "asset_current")
        cls.expense_account = cls._account("632901", "expense_direct_cost")
        cls.goods = cls._category("Downgrade Test Goods")
        cls.seconds = cls._category("Downgrade Test Seconds")

        attribute = cls.env["product.attribute"].create(
            {
                "name": "Downgrade Test Size",
                "create_variant": "always",
                "value_ids": [Command.create({"name": "S"}), Command.create({"name": "M"})],
            }
        )
        cls.style = cls.env["product.template"].create(
            {
                "name": "Downgrade Test Style",
                "is_storable": True,
                "categ_id": cls.goods.id,
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [Command.set(attribute.value_ids.ids)],
                        }
                    )
                ],
            }
        )
        cls.variant_1, cls.variant_2 = cls.style.product_variant_ids
        cls.other = cls._product("Downgrade Test Other", cls.goods)
        cls.second = cls._product("Downgrade Test Second", cls.seconds)
        cls.second_b = cls._product("Downgrade Test Second B", cls.seconds)
        cls.owner = cls.env["res.partner"].create({"name": "Downgrade Test Owner"})

        virtual = cls.env.ref("stock.stock_location_locations_virtual")
        cls.downgrade = cls.env["stock.location"].create(
            {
                "name": "Downgrade",
                "location_id": virtual.id,
                "usage": "inventory",
                "scrap_location": True,
                "company_id": cls.company.id,
                "downgrade_categ_id": cls.seconds.id,
                "valuation_in_account_id": cls.valuation_account.id,
                "valuation_out_account_id": cls.valuation_account.id,
            }
        )
        cls.waste = cls.env["stock.location"].create(
            {
                "name": "Waste",
                "location_id": virtual.id,
                "usage": "inventory",
                "scrap_location": True,
                "company_id": cls.company.id,
                "valuation_in_account_id": cls.expense_account.id,
            }
        )

    @classmethod
    def _account(cls, code, account_type):
        return cls.env["account.account"].create(
            {
                "code": code,
                "name": f"Downgrade Test {code}",
                "account_type": account_type,
                "company_ids": [Command.set(cls.company.ids)],
            }
        )

    @classmethod
    def _category(cls, name):
        journal = cls.env["account.journal"].search(
            [("code", "=", "STJ"), ("company_id", "=", cls.company.id)], limit=1
        )
        return (
            cls.env["product.category"]
            .with_company(cls.company)
            .create(
                {
                    "name": name,
                    "property_cost_method": "average",
                    "property_valuation": "real_time",
                    "property_stock_valuation_account_id": cls.valuation_account.id,
                    "property_stock_account_input_categ_id": cls.input_account.id,
                    "property_stock_account_output_categ_id": cls.output_account.id,
                    "property_stock_journal": journal.id,
                }
            )
        )

    @classmethod
    def _product(cls, name, category):
        return cls.env["product.product"].create(
            {"name": name, "is_storable": True, "categ_id": category.id}
        )

    def _stock_in(self, product, quantity, price, owner=None):
        supplier = self.env.ref("stock.stock_location_suppliers")
        owner_id = owner.id if owner else False
        move = self.env["stock.move"].create(
            {
                "name": "Downgrade test receipt",
                "company_id": self.company.id,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": quantity,
                "location_id": supplier.id,
                "location_dest_id": self.stock.id,
                "price_unit": price,
                "restrict_partner_id": owner_id,
                "picked": True,
                "move_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_id": product.uom_id.id,
                            "quantity": quantity,
                            "location_id": supplier.id,
                            "location_dest_id": self.stock.id,
                            "owner_id": owner_id,
                        }
                    )
                ],
            }
        )
        move._action_done()

    def _draft(self, product, quantity, location, env=None, **values):
        return (env or self.env)["stock.scrap"].create(
            {
                "company_id": self.company.id,
                "product_id": product.id,
                "scrap_qty": quantity,
                "location_id": self.stock.id,
                "scrap_location_id": location.id,
                **values,
            }
        )

    def _scrap(self, product, quantity, location, env=None, **values):
        scrap = self._draft(product, quantity, location, env=env, **values)
        scrap.do_scrap()
        return scrap

    def _downgrade(self, product, quantity, second, env=None):
        return self._scrap(
            product, quantity, self.downgrade, env=env, downgrade_product_id=second.id
        )

    def _on_hand(self, product, location=None, owner=None):
        """Quantity in a location; of one owner when given (an empty partner: none)."""
        domain = [("product_id", "=", product.id), ("location_id", "=", (location or self.stock).id)]
        if owner is not None:
            domain.append(("owner_id", "=", owner.id))
        return sum(self.env["stock.quant"].search(domain).mapped("quantity"))

    def _value(self, product):
        layers = self.env["stock.valuation.layer"].search(
            [("product_id", "=", product.id), ("company_id", "=", self.company.id)]
        )
        return sum(layers.mapped("value"))

    def _cost(self, product):
        return product.with_company(self.company).standard_price

    def _entries(self, scrap):
        return self.env["account.move"].search([("stock_move_id", "in", scrap.move_ids.ids)])

    def test_downgrade_moves_stock(self):
        self._stock_in(self.variant_1, 10, 100)
        scrap = self._downgrade(self.variant_1, 3, self.second)
        self.assertEqual(self._on_hand(self.variant_1), 7)
        self.assertEqual(self._on_hand(self.second), 3)
        self.assertEqual(self._on_hand(self.variant_1, self.downgrade), 3)
        self.assertEqual(self._on_hand(self.second, self.downgrade), -3)
        self.assertEqual(scrap.state, "done")
        self.assertEqual(len(scrap.move_ids), 2)
        self.assertEqual(set(scrap.move_ids.mapped("state")), {"done"})
        self.assertEqual(scrap.scrap_qty, 3)

    def test_cost_follows_the_goods(self):
        self._stock_in(self.variant_1, 10, 100)
        self._downgrade(self.variant_1, 3, self.second)
        self.assertEqual(self._value(self.variant_1), 700)
        self.assertEqual(self._value(self.second), 300)
        self.assertEqual(self._cost(self.second), 100)

    def test_entries_stay_on_valuation(self):
        self._stock_in(self.variant_1, 10, 100)
        scrap = self._downgrade(self.variant_1, 3, self.second)
        entries = self._entries(scrap)
        self.assertEqual(len(entries), 2)
        for entry in entries:
            self.assertEqual(entry.state, "posted")
            self.assertEqual(entry.line_ids.account_id, self.valuation_account)
            self.assertEqual(sum(entry.line_ids.mapped("debit")), 300)
            self.assertEqual(sum(entry.line_ids.mapped("credit")), 300)

    def test_owner_kept(self):
        self._stock_in(self.variant_1, 5, 100, owner=self.owner)
        scrap = self._scrap(
            self.variant_1,
            3,
            self.downgrade,
            owner_id=self.owner.id,
            downgrade_product_id=self.second.id,
        )
        no_owner = self.env["res.partner"]
        self.assertEqual(self._on_hand(self.variant_1, owner=self.owner), 2)
        self.assertEqual(self._on_hand(self.second, owner=self.owner), 3)
        self.assertEqual(self._on_hand(self.second, owner=no_owner), 0)
        receipt = scrap.move_ids.filtered(lambda move: move.product_id == self.second)
        self.assertEqual(receipt.restrict_partner_id, self.owner)
        self.assertEqual(receipt.move_line_ids.owner_id, self.owner)
        layers = self.env["stock.valuation.layer"].search(
            [("stock_move_id", "in", scrap.move_ids.ids)]
        )
        self.assertFalse(layers)
        self.assertFalse(self._entries(scrap))

    def test_average_of_two_sources(self):
        self._stock_in(self.variant_1, 3, 100)
        self._stock_in(self.other, 1, 200)
        self._downgrade(self.variant_1, 3, self.second)
        self._downgrade(self.other, 1, self.second)
        self.assertEqual(self._on_hand(self.second), 4)
        self.assertEqual(self._value(self.second), 500)
        self.assertEqual(self._cost(self.second), 125)

    def test_zero_cost_stays_zero(self):
        self._stock_in(self.variant_1, 2, 100)
        self._stock_in(self.other, 2, 0)
        self._downgrade(self.variant_1, 2, self.second)
        self._downgrade(self.other, 2, self.second)
        self.assertEqual(self._on_hand(self.second), 4)
        self.assertEqual(self._value(self.second), 200)
        self.assertEqual(self._cost(self.second), 50)

    def test_unit_conversion(self):
        self._stock_in(self.variant_1, 24, 10)
        self._scrap(
            self.variant_1,
            1,
            self.downgrade,
            product_uom_id=self.env.ref("uom.product_uom_dozen").id,
            downgrade_product_id=self.second.id,
        )
        self.assertEqual(self._on_hand(self.variant_1), 12)
        self.assertEqual(self._on_hand(self.second), 12)
        self.assertEqual(self._value(self.second), 120)

    def test_refused_without_product(self):
        self._stock_in(self.other, 5, 100)
        scrap = self._draft(self.other, 2, self.downgrade)
        self.assertFalse(scrap.downgrade_product_id)
        with self.assertRaises(UserError):
            scrap.do_scrap()
        self.assertEqual(scrap.state, "draft")
        self.assertEqual(self._on_hand(self.other), 5)

    def test_ordinary_scrap(self):
        self._stock_in(self.variant_1, 10, 100)
        scrap = self._scrap(self.variant_1, 3, self.waste)
        self.assertFalse(scrap.downgrade_product_id)
        self.assertEqual(len(scrap.move_ids), 1)
        self.assertEqual(self._on_hand(self.second), 0)
        expense = self._entries(scrap).line_ids.filtered(
            lambda line: line.account_id == self.expense_account
        )
        self.assertEqual(expense.debit, 300)

    def test_proposal(self):
        self._stock_in(self.variant_1, 5, 100)
        self._stock_in(self.other, 5, 100)
        no_history = self._product("Downgrade Test No History", self.goods)
        self._downgrade(self.variant_1, 1, self.second)
        self._downgrade(self.other, 1, self.second_b)
        scrap = self._draft(self.variant_1, 1, self.downgrade)
        self.assertEqual(scrap.downgrade_product_id, self.second)
        self.assertEqual(
            self._draft(self.variant_2, 1, self.downgrade).downgrade_product_id, self.second
        )
        self.assertEqual(
            self._draft(self.other, 1, self.downgrade).downgrade_product_id, self.second_b
        )
        self.assertFalse(self._draft(no_history, 1, self.downgrade).downgrade_product_id)
        scrap.scrap_location_id = self.waste
        self.assertFalse(scrap.downgrade_product_id)

    def test_variant_first(self):
        self._stock_in(self.variant_1, 5, 100)
        self._stock_in(self.variant_2, 5, 100)
        self._downgrade(self.variant_1, 1, self.second)
        self._downgrade(self.variant_2, 1, self.second_b)
        self.assertEqual(
            self._draft(self.variant_1, 1, self.downgrade).downgrade_product_id, self.second
        )
        self.assertEqual(
            self._draft(self.variant_2, 1, self.downgrade).downgrade_product_id, self.second_b
        )

    def test_proposal_kept_when_changed(self):
        self._stock_in(self.variant_1, 5, 100)
        self._downgrade(self.variant_1, 1, self.second)
        scrap = self._draft(self.variant_1, 1, self.downgrade)
        scrap.downgrade_product_id = self.second_b
        scrap.do_scrap()
        self.assertEqual(self._on_hand(self.second_b), 1)
        self.assertEqual(self._on_hand(self.second), 1)

    def test_as_stock_user(self):
        self._stock_in(self.variant_1, 5, 100)
        user = self.env["res.users"].create(
            {
                "name": "Downgrade Test Stock User",
                "login": "downgrade.test.stock.user",
                "company_id": self.company.id,
                "company_ids": [Command.set(self.company.ids)],
                "groups_id": [Command.set(self.env.ref("stock.group_stock_user").ids)],
            }
        )
        user_env = self.env(
            user=user, context=dict(self.env.context, allowed_company_ids=self.company.ids)
        )
        with self.assertRaises(AccessError):
            user_env["stock.valuation.layer"].search([], limit=1)
        self._downgrade(self.variant_1, 2, self.second, env=user_env)
        self.assertEqual(self._on_hand(self.second), 2)
        self.assertEqual(self._value(self.second), 200)
