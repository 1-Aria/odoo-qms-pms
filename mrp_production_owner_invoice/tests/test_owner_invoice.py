# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOwnerInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Owner Invoice Test Company"})
        cls.env.user.company_ids = [Command.link(cls.company.id)]
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=cls.company.ids))
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.warehouse.manufacture_steps = "pbm"
        cls.stock = cls.warehouse.lot_stock_id
        cls.owner = cls.env["res.partner"].create({"name": "Owner test", "is_company": True})

        def account(code, account_type, reconcile=False):
            return cls.env["account.account"].create(
                {"code": code, "name": f"Test {code}", "account_type": account_type, "reconcile": reconcile,
                 "company_ids": [Command.set(cls.company.ids)]}
            )

        cls.acc_valuation = account("152001", "asset_current")
        cls.acc_input = account("339901", "liability_current")
        cls.acc_output = account("159901", "asset_current")
        cls.acc_production = account("154101", "asset_current")
        cls.acc_expense = account("632001", "expense_direct_cost")
        cls.acc_income = account("511001", "income")
        cls.acc_receivable = account("131001", "asset_receivable", reconcile=True)
        cls.acc_other = account("338001", "liability_current")
        cls.owner.with_company(cls.company).property_account_receivable_id = cls.acc_receivable
        Journal = cls.env["account.journal"]
        cls.stock_journal = Journal.create(
            {"name": "Stock test", "code": "STKT", "type": "general", "company_id": cls.company.id}
        )
        cls.sale_journal = Journal.create(
            {"name": "Sales test", "code": "SALT", "type": "sale", "company_id": cls.company.id,
             "default_account_id": cls.acc_income.id}
        )
        category = cls.env["product.category"].with_company(cls.company).create(
            {
                "name": "Owner invoice test category",
                "property_cost_method": "average",
                "property_valuation": "real_time",
                "property_stock_valuation_account_id": cls.acc_valuation.id,
                "property_stock_account_input_categ_id": cls.acc_input.id,
                "property_stock_account_output_categ_id": cls.acc_output.id,
                "property_stock_account_production_cost_id": cls.acc_production.id,
                "property_account_expense_categ_id": cls.acc_expense.id,
                "property_stock_journal": cls.stock_journal.id,
            }
        )
        Product = cls.env["product.product"].with_company(cls.company)
        cls.component = Product.create(
            {"name": "Vải test", "is_storable": True, "categ_id": category.id, "standard_price": 10.0}
        )
        cls.finished = Product.create({"name": "Áo test", "is_storable": True, "categ_id": category.id})
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1,
                "company_id": cls.company.id,
                "bom_line_ids": [Command.create({"product_id": cls.component.id, "product_qty": 1})],
            }
        )
        cls.processing_type = cls.warehouse.manu_type_id.copy(
            {"name": "Processing test", "sequence_code": "PRCT", "owner_partner_id": cls.owner.id}
        )
        cls.order_type = cls.warehouse.manu_type_id.copy(
            {"name": "Order processing test", "sequence_code": "OPRT", "owner_from_partner": True,
             "production_owned": False}
        )

        def service(name):
            return Product.create({
                "name": name, "type": "service", "sale_ok": True, "taxes_id": [Command.clear()],
                "property_account_income_id": cls.acc_income.id,
                "property_account_expense_id": cls.acc_expense.id,
            })

        cls.fee_product = service("Phí gia công test")
        cls.material_product = service("Vật tư cung cấp test")
        cls.pricelist = cls.env["product.pricelist"].create({
            "name": "Fee test",
            "company_id": cls.company.id,
            "currency_id": cls.company.currency_id.id,
            "item_ids": [Command.create({
                "applied_on": "1_product",
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "compute_price": "fixed",
                "fixed_price": 500.0,
            })],
        })
        today = fields.Date.context_today(cls.env.user)
        cls.month_start = today.replace(day=1)
        cls.month_end = (cls.month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Helpers --------------------------------------------------------------------------------

    def _stock(self, qty, owner=None):
        if owner:
            self.env["stock.quant"]._update_available_quantity(self.component, self.stock, qty, owner_id=owner)
        else:
            self.env["stock.quant"].with_context(inventory_mode=True).create(
                {"product_id": self.component.id, "location_id": self.stock.id, "inventory_quantity": qty}
            ).action_apply_inventory()

    def _done_order(self, picking_type, **values):
        vals = {"product_id": self.finished.id, "product_qty": 10, "bom_id": self.bom.id,
                "picking_type_id": picking_type.id, "company_id": self.company.id}
        vals.update(values)
        production = self.env["mrp.production"].create(vals)
        production.action_confirm()
        pick = production.picking_ids.filtered(lambda p: p.picking_type_id == self.warehouse.pbm_type_id)
        pick.action_assign()
        pick.move_ids.picked = True
        pick.button_validate()
        production.action_assign()
        production.qty_producing = 10
        production._set_qty_producing()
        production.move_raw_ids.picked = True
        production.with_context(skip_backorder=True, mo_ids_to_backorder=[]).button_mark_done()
        self.assertEqual(production.state, "done")
        return production

    def _processing_done(self):
        self._stock(6, owner=self.owner)
        self._stock(4)
        return self._done_order(self.processing_type)

    def _wizard(self, date_from=None, date_to=None):
        return self.env["mrp.production.owner.invoice.wizard"].create({
            "company_id": self.company.id,
            "owner_id": self.owner.id,
            "date_from": date_from or self.month_start,
            "date_to": date_to or self.month_end,
            "pricelist_id": self.pricelist.id,
            "fee_product_id": self.fee_product.id,
            "material_product_id": self.material_product.id,
        })

    # Tests ----------------------------------------------------------------------------------

    def test_fee_lines(self):
        self._processing_done()
        wizard = self._wizard()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.product_tmpl_id, self.finished.product_tmpl_id)
        self.assertEqual(wizard.line_ids.quantity, 10)
        self.assertEqual(wizard.line_ids.price_unit, 500)
        self.assertTrue(wizard.line_ids.has_rule)

    def test_style_without_rule(self):
        self._processing_done()
        self.pricelist.item_ids.unlink()
        wizard = self._wizard()
        self.assertEqual(wizard.line_ids.price_unit, 0)
        self.assertFalse(wizard.line_ids.has_rule)
        self.assertIn(self.finished.product_tmpl_id.name, wizard.warning)

    def test_material_amount(self):
        self._processing_done()
        self.assertAlmostEqual(self._wizard().material_amount, 40)

    def test_order_processing_left_out(self):
        self._stock(10)
        self._done_order(self.order_type, owner_id=self.owner.id)
        wizard = self._wizard()
        self.assertFalse(wizard.line_ids)
        self.assertEqual(wizard.material_amount, 0)

    def test_period(self):
        self._processing_done()
        previous_end = self.month_start - timedelta(days=1)
        wizard = self._wizard(date_from=previous_end.replace(day=1), date_to=previous_end)
        self.assertFalse(wizard.line_ids)
        self.assertEqual(wizard.material_amount, 0)

    def test_create_invoice(self):
        self._processing_done()
        wizard = self._wizard()
        action = wizard.action_create_invoice()
        invoice = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(invoice.state, "draft")
        self.assertEqual(invoice.partner_id, self.owner)
        self.assertEqual(invoice.invoice_date, self.month_end)
        self.assertEqual(invoice.invoice_origin, f"Gia công Owner test {self.month_end:%m/%Y}")
        fee = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.fee_product)
        material = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.material_product)
        self.assertEqual((fee.quantity, fee.price_unit), (10, 500))
        self.assertAlmostEqual(material.price_unit, 40)
        self.assertIn("An invoice for this period already exists", self._wizard().warning)

    def test_late_attributions(self):
        entry = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.stock_journal.id,
            "date": self.month_start,
            "line_ids": [
                Command.create({"account_id": self.acc_expense.id, "debit": 75, "name": "Vải X đã dùng cho đơn Owner"}),
                Command.create({"account_id": self.acc_expense.id, "debit": 5, "name": "Vải Y khác"}),
                Command.create({"account_id": self.acc_other.id, "credit": 80, "name": "Đối ứng"}),
            ],
        })
        entry.action_post()
        wizard = self._wizard()
        self.assertEqual(wizard.late_account_id, self.acc_expense)
        self.assertEqual(wizard.late_line_ids.mapped("debit"), [75])
