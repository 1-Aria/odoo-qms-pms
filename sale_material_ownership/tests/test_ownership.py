# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import MaterialOwnershipCase


@tagged("post_install", "-at_install")
class TestOwnership(MaterialOwnershipCase):
    # Explosion

    def test_explode_two_levels(self):
        batch = self._batch(self._order([(self.shirt, 10)]))
        needs = {need.product_id: need for need in batch.need_line_ids}
        self.assertEqual(set(needs), {self.fabric, self.button})
        self.assertAlmostEqual(needs[self.fabric].material_qty, 15)
        self.assertAlmostEqual(needs[self.button].material_qty, 50)
        for need in needs.values():
            self.assertAlmostEqual(need.line_qty, 10)
            self.assertEqual(need.bom_id, self.bom_shirt)
            self.assertTrue(need.exploded)

    def test_material_sold_as_such(self):
        batch = self._batch(self._order([(self.fabric, 20)]))
        self.assertEqual(len(batch.need_line_ids), 1)
        need = batch.need_line_ids
        self.assertEqual(need.product_id, self.fabric)
        self.assertAlmostEqual(need.material_qty, 20)
        self.assertFalse(need.bom_id)

    def test_not_exploded(self):
        batch = self._batch(self._order([(self.towel, 3), (self.shirt, 1)]))
        towel_need = batch.need_line_ids.filtered(lambda n: n.product_id == self.towel)
        self.assertEqual(len(towel_need), 1)
        self.assertFalse(towel_need.exploded)
        self.assertAlmostEqual(towel_need.material_qty, 3)
        self.assertIn("MO Towel", batch.warning)
        self.assertNotIn(self.towel.id, self._q(self.towel))

    # Owned quantities

    def test_bill_needs_einvoice(self):
        bill = self._bill(self._purchase(self.fabric, 100))
        figures = self._q(self.fabric)[self.fabric.id]
        self.assertAlmostEqual(figures["in"], 0)
        self.assertAlmostEqual(figures["awaiting"], 100)
        self._einvoice(bill)
        figures = self._q(self.fabric)[self.fabric.id]
        self.assertAlmostEqual(figures["in"], 100)
        self.assertAlmostEqual(figures["awaiting"], 0)

    def test_einvoice_amounts_differ(self):
        bill = self._bill(self._purchase(self.fabric, 100))
        self._einvoice(bill, amount_total=bill.amount_total + 1000)
        figures = self._q(self.fabric)[self.fabric.id]
        self.assertAlmostEqual(figures["in"], 0)
        self.assertAlmostEqual(figures["awaiting"], 100)

    def test_einvoice_replaced(self):
        bill = self._bill(self._purchase(self.fabric, 100))
        first = self._einvoice(bill)
        self._einvoice(self.env["account.move"], relation_type="1", related_einvoice_id=first.id)
        self.assertEqual(first.correction_state, "replaced")
        figures = self._q(self.fabric)[self.fabric.id]
        self.assertAlmostEqual(figures["in"], 0)
        self.assertAlmostEqual(figures["awaiting"], 100)

    def test_issued_einvoice_ignored(self):
        bill = self._bill(self._purchase(self.fabric, 100))
        self._einvoice(bill, direction="issued")
        self.assertAlmostEqual(self._q(self.fabric)[self.fabric.id]["in"], 0)

    def test_billed_not_received(self):
        self.fabric.purchase_method = "purchase"
        bill = self._bill(self._purchase(self.fabric, 100, receive=60))
        self._einvoice(bill)
        figures = self._q(self.fabric)[self.fabric.id]
        self.assertAlmostEqual(figures["in"], 60)
        self.assertAlmostEqual(figures["not_received"], 40)

    def test_refund_counts_at_once(self):
        self._counted_bill(self.fabric, 100)
        self._direct_bill([(self.fabric, 30)], refund=True)
        self.assertAlmostEqual(self._q(self.fabric)[self.fabric.id]["in"], 70)

    def test_direct_bill_no_receipt(self):
        bill = self._direct_bill([(self.fabric, 10)])
        self._einvoice(bill)
        figures = self._q(self.fabric)[self.fabric.id]
        self.assertAlmostEqual(figures["in"], 0)
        self.assertAlmostEqual(figures["no_receipt"], 10)

    def test_draft_batch_uses_nothing(self):
        self._counted_bill(self.fabric, 100)
        self._batch(self._order([(self.shirt, 10)]))
        figures = self._q(self.fabric)[self.fabric.id]
        self.assertAlmostEqual(figures["in"], 100)
        self.assertAlmostEqual(figures["used"], 0)

    # Batches and coverage

    def test_order_lines_in_one_batch(self):
        order = self._order([(self.shirt, 10)])
        batch_a = self._batch(order)
        with self.assertRaises(UserError):
            self._batch(order)
        batch_a.order_ids = [Command.unlink(order.id)]
        self.assertFalse(batch_a.need_line_ids)
        batch_b = self._batch(order)
        self.assertEqual(len(batch_b.need_line_ids), 2)

    def test_line_added_after_batch(self):
        order = self._order([(self.shirt, 10)])
        self._batch(order)
        order.write(
            {"order_line": [Command.create({"product_id": self.fabric.id, "product_uom_qty": 4})]}
        )
        self.assertEqual(order.material_coverage, "partly")
        batch_b = self._batch(order)
        self.assertEqual(len(batch_b.need_line_ids), 1)
        self.assertEqual(batch_b.need_line_ids.product_id, self.fabric)
        self.assertAlmostEqual(batch_b.need_line_ids.material_qty, 4)
        self.assertEqual(order.material_coverage, "draft")

    def test_coverage_and_search(self):
        SaleOrder = self.env["sale.order"]
        order = self._order([(self.shirt, 2)])
        self.assertEqual(order.material_coverage, "not_batched")
        self.assertIn(order, SaleOrder.search([("material_coverage", "=", "not_batched")]))
        self._batch(order)
        self.assertEqual(order.material_coverage, "draft")
        self.assertNotIn(order, SaleOrder.search([("material_coverage", "=", "not_batched")]))
        self.assertIn(order, SaleOrder.search([("material_coverage", "in", ["draft"])]))
        services = self._order([(self.service, 1)])
        self.assertEqual(services.material_coverage, "not_needed")
        quotation = self._order([(self.shirt, 1)], confirm=False)
        self.assertFalse(quotation.material_coverage)

    def test_add_uncovered(self):
        first = self._order([(self.shirt, 1)])
        second = self._order([(self.fabric, 2)])
        batched = self._order([(self.shirt, 1)])
        self._batch(batched)
        services = self._order([(self.service, 1)])
        batch = self.env["sale.material.batch"].create({"company_id": self.company.id})
        result = batch.action_add_uncovered()
        self.assertEqual(batch.order_ids, first | second)
        self.assertNotIn(services, batch.order_ids)
        self.assertIn("2", result["params"]["message"])
        self.assertEqual(batch.need_line_ids.order_id, first | second)

    def test_order_before_start_out_of_scope(self):
        old = self._order([(self.shirt, 1)])
        old.date_order = datetime.combine(self.start - timedelta(days=1), time(12, 0))
        self.assertEqual(old.material_coverage, "not_needed")
        with self.assertRaisesRegex(UserError, "before the ownership start"):
            self._batch(old)
        recent = self._order([(self.shirt, 1)])
        batch = self.env["sale.material.batch"].create({"company_id": self.company.id})
        batch.action_add_uncovered()
        self.assertEqual(batch.order_ids, recent)

    def test_start_required(self):
        order = self._order([(self.shirt, 1)])
        self.company.material_ownership_start = False
        self.assertEqual(order.material_coverage, "not_needed")
        with self.assertRaisesRegex(UserError, "ownership start date"):
            self._batch(order)
        batch = self.env["sale.material.batch"].create({"company_id": self.company.id})
        with self.assertRaisesRegex(UserError, "ownership start date"):
            batch.action_add_uncovered()

    def test_warning_list_capped(self):
        Batch = self.env["sale.material.batch"]
        self.assertEqual(Batch._material_list(["a", "b"]), "a, b")
        text = Batch._material_list([f"m{i}" for i in range(12)])
        self.assertIn("m9", text)
        self.assertNotIn("m10", text)
        self.assertIn("2 more", text)

    def test_order_with_no_goods_refused(self):
        services = self._order([(self.service, 1)])
        with self.assertRaisesRegex(UserError, "no goods"):
            self._batch(services)

    # Balance report

    def test_balance_report(self):
        Balance = self.env["sale.material.ownership.balance"]
        self._counted_bill(self.fabric, 100)
        action = Balance.action_open()
        row = Balance.search(action["domain"]).filtered(lambda r: r.product_id == self.fabric)
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.qty_in, 100)
        self.assertAlmostEqual(row.qty_on_hand, 100)
        self.assertAlmostEqual(row.qty_not_owned, 0)
        self._purchase(self.fabric, 20)
        action = Balance.action_open()
        row = Balance.search(action["domain"]).filtered(lambda r: r.product_id == self.fabric)
        self.assertAlmostEqual(row.qty_on_hand, 120)
        self.assertAlmostEqual(row.qty_not_owned, 20)
        self.assertAlmostEqual(row.value_not_owned, 20 * self.fabric.standard_price)

    # Access

    def test_access(self):
        batch = self.env["sale.material.batch"].create({"company_id": self.company.id})
        as_salesman = self._as(self.salesman)["sale.material.batch"]
        self.assertEqual(as_salesman.browse(batch.id).name, batch.name)
        with self.assertRaises(AccessError):
            as_salesman.create({"company_id": self.company.id})
        order = self._order([(self.shirt, 1)])
        manager_batch = self._as(self.sale_manager)["sale.material.batch"].create(
            {"company_id": self.company.id, "order_ids": [Command.link(order.id)]}
        )
        self.assertEqual(len(manager_batch.need_line_ids), 2)
