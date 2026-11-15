# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import StockVoucherCase

ACTION_HANDOVER = "l10n_vn_voucher_stock.action_report_stock_handover"


@tagged("post_install", "-at_install")
class TestStockHandover(StockVoucherCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.in_type | cls.out_type).l10n_vn_handover_report = True
        cls.helpers = cls.env["l10n_vn.voucher"]

    def _address_vi(self, partner):
        # The form reads addresses in Vietnamese (Việt Nam, not Vietnam).
        return self.helpers._address(partner.with_context(lang="vi_VN"))

    def _handover(self, picking):
        return picking._l10n_vn_handover_data()

    def _delivery_done(self):
        self._receipt_done()
        return self._validate(self._picking(self.out_type, 4, self.partner))

    def test_handover_delivery(self):
        delivery = self._delivery_done()
        data = self._handover(delivery)
        self.assertEqual(data["title"], "BIÊN BẢN GIAO NHẬN HÀNG HÓA")
        self.assertEqual(data["giver"], self.company.partner_id)
        self.assertEqual(data["receiver"], self.partner)
        self.assertEqual(data["place"], self._address_vi(self.partner))
        self.assertEqual(len(data["lines"]), 1)
        self.assertEqual(data["lines"][0]["qty"], 4)
        self.assertTrue(data["date"])

    def test_handover_receipt(self):
        receipt = self._picking(self.in_type, 10, self.partner)
        receipt.action_confirm()
        data = self._handover(receipt)
        self.assertEqual(data["giver"], self.partner)
        self.assertEqual(data["receiver"], self.company.partner_id)
        self.assertEqual(data["place"], self._address_vi(self.warehouse.partner_id))
        self.assertEqual(data["lines"][0]["qty"], 10)
        self.assertFalse(data["date"])

    def test_handover_domain(self):
        action = self.env.ref(ACTION_HANDOVER)

        def valid(picking):
            return action.get_valid_action_reports("stock.picking", picking.ids)

        receipt = self._picking(self.in_type, 10, self.partner)
        internal = self._picking(self.int_type, 1)
        self.assertEqual(valid(receipt), action.ids)
        self.assertEqual(valid(internal), [])
        receipt.action_cancel()
        self.assertEqual(valid(receipt), [])

    def test_partner_fallback(self):
        group_model = self.env["procurement.group"]
        if "sale_id" not in group_model._fields:
            self.skipTest("sale_stock is not installed")
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        group = group_model.create({"name": "WH/MO/TEST", "sale_id": order.id})
        receipt = self._picking(self.in_type, 2)
        # A transfer's group is its moves' (stock/models/stock_picking.py:582-584).
        receipt.move_ids.group_id = group
        self.assertEqual(receipt.group_id, group)
        self.assertFalse(receipt.partner_id)
        self.assertEqual(receipt._l10n_vn_partner(), self.partner)
        self.assertEqual(self._data(receipt)["party"], self.partner.display_name)
        handover = self._handover(receipt)
        self.assertEqual(handover["giver"], self.partner)
        self.assertEqual(handover["basis"], order.name)
        self.assertFalse(receipt.partner_id)

        # A storekeeper, who cannot read sales orders, gets the same customer.
        storekeeper_env = self.env(
            user=self.storekeeper,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        self.assertEqual(receipt.with_env(storekeeper_env)._l10n_vn_partner(), self.partner)

    def test_render_handover(self):
        html = self._html(self._delivery_done(), ACTION_HANDOVER)
        for text in (
            "BIÊN BẢN GIAO NHẬN HÀNG HÓA",
            "Bên giao",
            "Bên nhận",
            "Đại diện bên giao",
            "Địa điểm giao nhận",
            "Biên bản được lập thành 02 bản",
        ):
            self.assertIn(text, html)
        for text in ("Đơn giá", "Nợ:", "Liên"):
            self.assertNotIn(text, html)

    def test_render_handover_as_storekeeper(self):
        delivery = self._delivery_done()
        storekeeper_env = self.env(
            user=self.storekeeper,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        # Positive control: the storekeeper reads the transfer.
        self.assertEqual(delivery.with_env(storekeeper_env).name, delivery.name)
        html = self._html(delivery, ACTION_HANDOVER, env=storekeeper_env)
        self.assertIn("BIÊN BẢN GIAO NHẬN HÀNG HÓA", html)
