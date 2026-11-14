# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import MaterialOwnershipCase


@tagged("post_install", "-at_install")
class TestRequest(MaterialOwnershipCase):
    def _lines(self, batch):
        return {line.product_id: line for line in batch.request_line_ids}

    def _used(self, product):
        return self._q(product)[product.id]["used"]

    # Netting and the bill

    def test_request_nets_against_balance(self):
        self._counted_bill(self.fabric, 100)
        batch = self._request(self._batch(self._order([(self.shirt, 10)])))
        lines = self._lines(batch)
        fabric, button = lines[self.fabric], lines[self.button]
        self.assertAlmostEqual(fabric.need_qty, 15)
        self.assertAlmostEqual(fabric.available_qty, 100)
        self.assertAlmostEqual(fabric.request_qty, 0)
        self.assertAlmostEqual(button.need_qty, 50)
        self.assertAlmostEqual(button.available_qty, 0)
        self.assertAlmostEqual(button.request_qty, 50)
        self.assertAlmostEqual(button.unit_cost, 500)
        self.assertAlmostEqual(button.amount, 25000)
        self.assertEqual(batch.state, "requested")
        bill = batch.bill_ids
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.state, "draft")
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(bill.partner_id, self.trading)
        self.assertEqual(bill.fiscal_position_id, self.fiscal_position)
        self.assertEqual(bill.invoice_origin, batch.name)
        line = bill.invoice_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.product_id, self.button)
        self.assertAlmostEqual(line.quantity, 50)
        self.assertAlmostEqual(line.price_unit, 500)
        self.assertEqual(line.account_id, self.account_33889)

    def test_bill_posts_no_stock(self):
        batch = self._request(self._batch(self._order([(self.button, 50)])))
        bill = self._post(batch.bill_ids)
        layers = self.env["stock.valuation.layer"].search_count(
            ["|", ("account_move_id", "=", bill.id), ("account_move_line_id", "in", bill.line_ids.ids)]
        )
        self.assertEqual(layers, 0)
        debit = sum(
            bill.line_ids.filtered(lambda l: l.account_id == self.account_33889).mapped("debit")
        )
        self.assertAlmostEqual(debit, 25000)

    def test_all_owned_covered_at_once(self):
        self._counted_bill(self.fabric, 100)
        self._counted_bill(self.button, 100)
        batch = self._request(self._batch(self._order([(self.shirt, 10)])))
        self.assertEqual(batch.state, "covered")
        self.assertFalse(batch.bill_ids)

    def test_pending_not_requested_twice(self):
        self._request(self._batch(self._order([(self.shirt, 10)])))
        batch_b = self._request(self._batch(self._order([(self.shirt, 4)])))
        button = self._lines(batch_b)[self.button]
        self.assertAlmostEqual(button.available_qty, 0)
        self.assertAlmostEqual(button.request_qty, 20)

    # Coverage

    def test_covered_when_bill_counts(self):
        order = self._order([(self.shirt, 10)])
        batch = self._request(self._batch(order))
        bill = self._post(batch.bill_ids)
        self.assertEqual(batch.state, "requested")
        self._einvoice(bill)
        self.assertEqual(batch.state, "covered")
        self.assertEqual(order.material_coverage, "covered")
        bill.button_draft()
        self.assertEqual(batch.state, "requested")

    def test_shortfall_next_batch(self):
        batch_a = self._request(self._batch(self._order([(self.shirt, 10)])))
        bill = batch_a.bill_ids
        bill.invoice_line_ids.filtered(lambda l: l.product_id == self.button).quantity = 45
        self._post(bill)
        self._einvoice(bill)
        self.assertEqual(batch_a.state, "covered")
        button_a = self._lines(batch_a)[self.button]
        self.assertAlmostEqual(button_a.billed_qty, 45)
        self.assertAlmostEqual(button_a.difference_qty, -5)
        batch_b = self._request(self._batch(self._order([(self.shirt, 4)])))
        button_b = self._lines(batch_b)[self.button]
        self.assertAlmostEqual(button_b.available_qty, -5)
        self.assertAlmostEqual(button_b.shortfall_qty, 5)
        self.assertAlmostEqual(button_b.request_qty, 25)

    # Effective quantity

    def test_partial_delivery(self):
        self._stock(self.shirt, 100)
        order = self._order([(self.shirt, 10)])
        self._request(self._batch(order))
        self._deliver(order, 6)
        self.assertAlmostEqual(self._used(self.fabric), 15)
        order.order_line.product_uom_qty = 6
        self.assertAlmostEqual(self._used(self.fabric), 9)

    def test_return_released(self):
        self._stock(self.shirt, 100)
        order = self._order([(self.shirt, 10)])
        self._request(self._batch(order))
        delivery = self._deliver(order)
        self.assertAlmostEqual(self._used(self.fabric), 15)
        wizard = self.env["stock.return.picking"].create({"picking_id": delivery.id})
        wizard.product_return_moves.write({"quantity": 4, "to_refund": True})
        result = wizard.action_create_returns()
        returned = self.env["stock.picking"].browse(result["res_id"])
        for move in returned.move_ids:
            move.quantity = 4
            move.picked = True
        returned.button_validate()
        self.assertEqual(returned.state, "done")
        self.assertAlmostEqual(order.order_line.qty_delivered, 6)
        self.assertAlmostEqual(self._used(self.fabric), 15)
        order.order_line.product_uom_qty = 6
        self.assertAlmostEqual(self._used(self.fabric), 9)

    def test_delivered_beyond_order(self):
        self._stock(self.shirt, 100)
        order = self._order([(self.shirt, 10)])
        self._request(self._batch(order))
        order.order_line.product_uom_qty = 12
        self._deliver(order)
        self.assertAlmostEqual(order.order_line.qty_delivered, 12)
        self.assertAlmostEqual(self._used(self.fabric), 18)

    def test_cancelled_order_released(self):
        order = self._order([(self.shirt, 10)])
        self._request(self._batch(order))
        self.assertAlmostEqual(self._used(self.fabric), 15)
        order._action_cancel()
        self.assertAlmostEqual(self._used(self.fabric), 0)

    # Cancel, settings, access

    def test_cancel_batch(self):
        order = self._order([(self.shirt, 10)])
        batch = self._request(self._batch(order))
        bill = batch.bill_ids
        batch.action_cancel()
        self.assertEqual(batch.state, "cancel")
        self.assertEqual(bill.state, "cancel")
        self.assertEqual(order.material_coverage, "not_batched")
        other = self._request(self._batch(self._order([(self.shirt, 2)])))
        self._post(other.bill_ids)
        with self.assertRaisesRegex(UserError, "posted bill"):
            other.action_cancel()

    def test_request_requires_settings(self):
        self.company.material_fiscal_position_id = False
        batch = self._batch(self._order([(self.shirt, 1)]))
        with self.assertRaisesRegex(UserError, "fiscal position"):
            self._request(batch)
        self.assertEqual(batch.state, "draft")
        self.assertFalse(batch.request_line_ids)

    def test_request_access(self):
        batch = self._batch(self._order([(self.shirt, 1)]))
        with self.assertRaises(AccessError):
            self._request(batch, user=self.sale_manager)
        self.assertEqual(batch.state, "draft")
        self._request(batch, user=self.accountant)
        self.assertEqual(batch.state, "requested")

    def test_picking_banner_field(self):
        uncovered = self._order([(self.shirt, 1)])
        self.assertEqual(uncovered.picking_ids.material_coverage, "not_batched")
        self._counted_bill(self.fabric, 100)
        self._counted_bill(self.button, 100)
        covered = self._order([(self.shirt, 1)])
        self._request(self._batch(covered))
        self.assertEqual(covered.picking_ids.material_coverage, "covered")
