# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged

ACTION_FULL = "l10n_vn_purchase_report.action_report_purchase_order_vn"
ACTION_COMPACT = "l10n_vn_purchase_report.action_report_purchase_order_vn_compact"


@tagged("post_install", "-at_install")
class TestPurchaseOrderReport(TransactionCase):
    """Built on TransactionCase, not on account's AccountTestInvoicingCommon,
    whose package cannot be imported on this image."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Purchase Form Test Company",
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

        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Nhà cung cấp test",
                "is_company": True,
                "vat": "0300000001",
                "street": "12 Lê Lợi",
                "city": "Hồ Chí Minh",
                "country_id": cls.env.ref("base.vn").id,
            }
        )
        size = cls.env["product.attribute"].create(
            {
                "name": "Size test",
                "create_variant": "always",
                "value_ids": [Command.create({"name": "S"}), Command.create({"name": "M"})],
            }
        )
        cls.shirt = cls.env["product.template"].create(
            {
                "name": "Áo test",
                "attribute_line_ids": [
                    Command.create(
                        {"attribute_id": size.id, "value_ids": [Command.set(size.value_ids.ids)]}
                    )
                ],
            }
        )
        cls.shirt_s, cls.shirt_m = cls.shirt.product_variant_ids
        # The product's name as the form prints it, without its code: OCA
        # product_sequence gives every new product one (PR/00141), which
        # display_name would prefix.
        cls.shirt_s_name = cls.shirt_s.with_context(display_default_code=False).display_name
        cls.shirt_m_name = cls.shirt_m.with_context(display_default_code=False).display_name
        cls.thread = cls.env["product.product"].create(
            {"name": "Chỉ test", "default_code": "CTEST"}
        )
        cls.order = cls._order()
        cls.purchase_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Purchase Form User",
                    "login": "l10n_vn_purchase_report_user",
                    "company_id": cls.company.id,
                    "company_ids": [Command.set(cls.company.ids)],
                    "groups_id": [
                        Command.set([cls.env.ref("purchase.group_purchase_user").id])
                    ],
                }
            )
        )

    @classmethod
    def _order(cls, **values):
        def line(product, qty, price):
            return Command.create(
                {
                    "product_id": product.id,
                    "product_qty": qty,
                    "price_unit": price,
                    "taxes_id": [Command.clear()],
                }
            )

        vals = {
            "partner_id": cls.vendor.id,
            "order_line": [
                line(cls.shirt_s, 10, 100),
                line(cls.shirt_m, 5, 100),
                line(cls.thread, 3, 50),
            ],
        }
        vals.update(values)
        return cls.env["purchase.order"].create(vals)

    def _subcontracting_bom(self):
        component = self.env["product.product"].create({"name": "Vải test"})
        return self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.thread.product_tmpl_id.id,
                "type": "subcontract",
                "subcontractor_ids": [Command.set(self.vendor.ids)],
                "company_id": self.company.id,
                "bom_line_ids": [
                    Command.create({"product_id": component.id, "product_qty": 1})
                ],
            }
        )

    def _data(self, order, compact=False):
        return order._l10n_vn_order_data(compact)

    def _html(self, order, xmlid, env=None):
        reports = (env or self.env)["ir.actions.report"]
        html, _type = reports._render_qweb_html(xmlid, order.ids)
        return html.decode()

    def test_titles(self):
        self.assertEqual(self._data(self.order)["title"], "YÊU CẦU BÁO GIÁ")
        self.order.button_confirm()
        data = self._data(self.order)
        self.assertEqual(data["title"], "ĐƠN ĐẶT HÀNG")
        self.assertEqual(
            data["date"],
            fields.Datetime.context_timestamp(self.order, self.order.date_approve).date(),
        )

    def test_subcontracting_title(self):
        self._subcontracting_bom()
        self.order.button_confirm()
        self.assertEqual(self._data(self.order)["title"], "ĐƠN ĐẶT HÀNG GIA CÔNG")

    def test_full_rows(self):
        rows = self._data(self.order)["rows"]
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["name"], self.shirt_s_name)
        self.assertEqual(rows[0]["code"], self.shirt_s.default_code or "")
        self.assertEqual(rows[2]["code"], "CTEST")
        self.assertEqual(rows[2]["taxes"], "")
        self.assertEqual(rows[2]["amount"], 150)

    def test_compact_rows(self):
        rows = self._data(self.order, compact=True)["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Áo test")
        self.assertEqual(rows[0]["qty"], 15)
        self.assertEqual(rows[0]["amount"], 1500)
        self.assertTrue(rows[0]["grouped"])
        self.assertEqual(rows[1]["code"], "CTEST")
        self.assertFalse(rows[1]["grouped"])

    def test_agreement(self):
        agreement = self.env["purchase.requisition"].create(
            {
                "vendor_id": self.vendor.id,
                "requisition_type": "blanket_order",
                "line_ids": [
                    Command.create(
                        {"product_id": self.thread.id, "product_qty": 100, "price_unit": 50}
                    )
                ],
            }
        )
        order = self._order(requisition_id=agreement.id)
        self.assertEqual(self._data(order)["agreement"], agreement.name)
        self.assertIn("Theo hợp đồng nguyên tắc số", self._html(order, ACTION_FULL))

    def test_render_full(self):
        html = self._html(self.order, ACTION_FULL)
        for text in (
            "YÊU CẦU BÁO GIÁ",
            self.order.name,
            "Bên mua",
            "Bên bán",
            "Nhà cung cấp test",
            "0300000001",
            "Xác nhận của nhà cung cấp",
            "(Ký, ghi rõ họ tên, đóng dấu)",
            "1.650",
            "Một nghìn sáu trăm năm mươi đồng",
            self.shirt_s_name,
        ):
            self.assertIn(text, html)
        self.assertNotIn("o_product_variant_grid", html)

    def test_render_compact(self):
        html = self._html(self.order, ACTION_COMPACT)
        self.assertIn("o_product_variant_grid", html)
        self.assertIn("1.500", html)
        self.assertNotIn(self.shirt_s_name, html)

    def test_report_domains(self):
        actions = self.env.ref(ACTION_FULL) | self.env.ref(ACTION_COMPACT)

        def valid(order):
            return set(actions.get_valid_action_reports("purchase.order", order.ids))

        self.assertEqual(valid(self.order), set(actions.ids))
        self.order.button_cancel()
        self.assertEqual(valid(self.order), set())

    def test_render_as_purchase_user(self):
        self._subcontracting_bom()
        self.order.button_confirm()
        user_env = self.env(
            user=self.purchase_user,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        # Positive control: the purchase user reads the order.
        self.assertEqual(self.order.with_env(user_env).name, self.order.name)
        html = self._html(self.order, ACTION_FULL, env=user_env)
        self.assertIn("ĐƠN ĐẶT HÀNG GIA CÔNG", html)
