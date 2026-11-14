# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import ACTION_IN, StockVoucherCase


@tagged("post_install", "-at_install")
class TestStockVoucher(StockVoucherCase):
    def test_receipt_done(self):
        receipt = self._receipt_done()
        data = self._data(receipt)
        self.assertEqual(data["title"], "PHIẾU NHẬP KHO")
        self.assertEqual(data["form_code"], "01-VT")
        self.assertEqual(data["number"], receipt.name)
        self.assertEqual(
            data["date"],
            fields.Datetime.context_timestamp(receipt, receipt.date_done).date(),
        )
        self.assertEqual(data["debit_accounts"], ["1520"])
        self.assertEqual(data["credit_accounts"], ["3399"])
        self.assertEqual(len(data["lines"]), 1)
        line = data["lines"][0]
        self.assertEqual(line["name"], "Vải test")
        self.assertEqual(line["code"], "VTEST1")
        self.assertEqual(line["demand"], 10)
        self.assertEqual(line["done"], 10)
        self.assertAlmostEqual(line["price"], 1000)
        self.assertAlmostEqual(line["amount"], 10000)
        self.assertAlmostEqual(data["total"], 10000)
        self.assertEqual(data["party"], self.partner.display_name)
        self.assertEqual(data["reason"], "Nhập kho mua hàng")

    def test_receipt_not_done(self):
        receipt = self._picking(self.in_type, 10, self.partner)
        receipt.action_confirm()
        data = self._data(receipt)
        self.assertFalse(data["date"])
        line = data["lines"][0]
        self.assertIsNone(line["done"])
        self.assertIsNone(line["price"])
        self.assertIsNone(line["amount"])
        self.assertIs(data["total"], False)
        self.assertEqual(data["debit_accounts"], [])
        self.assertEqual(data["credit_accounts"], [])

    def test_delivery_done(self):
        self._receipt_done()
        delivery = self._validate(self._picking(self.out_type, 4, self.partner))
        data = self._data(delivery)
        self.assertEqual(data["title"], "PHIẾU XUẤT KHO")
        self.assertEqual(data["form_code"], "02-VT")
        self.assertEqual(data["debit_accounts"], ["1599"])
        self.assertEqual(data["credit_accounts"], ["1520"])
        self.assertAlmostEqual(data["lines"][0]["amount"], 4000)
        self.assertEqual(len(data["signers"]), 5)
        self.assertEqual(data["signers"][-1]["role"], "Giám đốc")

    def test_internal_quantities_only(self):
        self._receipt_done()
        internal = self._validate(self._picking(self.int_type, 3))
        data = self._data(internal)
        self.assertEqual(data["kind"], "out")
        line = data["lines"][0]
        self.assertEqual(line["done"], 3)
        self.assertIsNone(line["price"])
        self.assertIsNone(line["amount"])
        self.assertIs(data["total"], False)
        self.assertEqual(data["debit_accounts"], [])
        self.assertEqual(data["credit_accounts"], [])
        self.assertEqual(data["location"], internal.location_id.complete_name)

    def test_reason(self):
        receipt = self._picking(self.in_type, 10, self.partner)
        self.assertEqual(self._data(receipt)["reason"], "Nhập kho mua hàng")
        receipt.l10n_vn_voucher_reason = "Nhập hàng mẫu"
        self.assertEqual(self._data(receipt)["reason"], "Nhập hàng mẫu")

        returned = self._picking(self.in_type, 2, self.partner, return_id=receipt.id)
        self.assertEqual(
            self._data(returned)["reason"],
            "Trả lại hàng theo phiếu %s" % receipt.name,
        )

    def test_cancelled_move_left_out(self):
        # A second product: two moves of one product merge at confirmation.
        thread = (
            self.env["product.product"]
            .with_company(self.company)
            .create(
                {
                    "name": "Chỉ test",
                    "default_code": "VTEST2",
                    "is_storable": True,
                    "categ_id": self.category.id,
                    "standard_price": 500.0,
                }
            )
        )
        receipt = self._picking(self.in_type, 10, self.partner)
        receipt.write(
            {
                "move_ids": [
                    Command.create(
                        {
                            "name": thread.name,
                            "product_id": thread.id,
                            "product_uom_qty": 5,
                            "product_uom": thread.uom_id.id,
                            "location_id": receipt.location_id.id,
                            "location_dest_id": receipt.location_dest_id.id,
                        }
                    )
                ]
            }
        )
        receipt.action_confirm()
        receipt.move_ids.filtered(lambda move: move.product_id == thread)._action_cancel()
        self._validate(receipt)
        lines = self._data(receipt)["lines"]
        self.assertEqual([line["code"] for line in lines], ["VTEST1"])

    def test_no_kind_refused(self):
        no_voucher_type = self.env["stock.picking.type"].create(
            {
                "name": "No Voucher",
                "code": "internal",
                "sequence_code": "NOV",
                "warehouse_id": self.warehouse.id,
                "company_id": self.company.id,
                "default_location_src_id": self.warehouse.lot_stock_id.id,
                "default_location_dest_id": self.warehouse.lot_stock_id.id,
            }
        )
        picking = self._picking(no_voucher_type, 1)
        with self.assertRaises(UserError):
            self._data(picking)
        self.assertEqual(self._valid(picking), set())

    def test_report_domains(self):
        receipt = self._picking(self.in_type, 10, self.partner)
        delivery = self._picking(self.out_type, 4, self.partner)
        self.assertEqual(self._valid(receipt), {self.action_in.id})
        self.assertEqual(self._valid(delivery), {self.action_out.id})
        receipt.action_cancel()
        self.assertEqual(self._valid(receipt), set())

    def test_render_receipt(self):
        receipt = self._receipt_done()
        html = self._html(receipt, ACTION_IN)
        for text in (
            "PHIẾU NHẬP KHO",
            "Mẫu số",
            "01-VT",
            receipt.name,
            "10.000",
            "Mười nghìn đồng",
        ):
            self.assertIn(text, html)
        for label in (
            "Liên 1: Kế toán lưu",
            "Liên 2: Thủ kho giữ để ghi thẻ kho",
            "Liên 3: Giao cho người giao hàng",
        ):
            self.assertEqual(html.count(label), 1, label)
        self.assertEqual(html.count("page-break-before"), 2)

    def test_render_as_storekeeper(self):
        receipt = self._receipt_done()
        storekeeper_env = self.env(
            user=self.storekeeper,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        # Positive control: the storekeeper reads the transfer.
        self.assertEqual(
            receipt.with_env(storekeeper_env).name, receipt.name
        )
        html = self._html(receipt, ACTION_IN, env=storekeeper_env)
        for text in ("10.000", "1520", "3399"):
            self.assertIn(text, html)
