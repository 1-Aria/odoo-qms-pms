# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.tests import TransactionCase, tagged

ACTION_FULL = "l10n_vn_sale_report.action_report_sale_order_vn"
ACTION_COMPACT = "l10n_vn_sale_report.action_report_sale_order_vn_compact"


@tagged("post_install", "-at_install")
class TestSaleOrderReport(TransactionCase):
    """Built on TransactionCase, not on account's AccountTestInvoicingCommon,
    whose package cannot be imported on this image."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Sales Form Test Company",
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

        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Khách hàng test",
                "is_company": True,
                "vat": "0300000002",
                "street": "12 Lê Lợi",
                "city": "Hồ Chí Minh",
                "country_id": cls.env.ref("base.vn").id,
            }
        )
        cls.contact = cls.env["res.partner"].create(
            {"name": "Chị Lan", "parent_id": cls.customer.id}
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
        cls.salesman = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Sales Form User",
                    "login": "l10n_vn_sale_report_user",
                    "company_id": cls.company.id,
                    "company_ids": [Command.set(cls.company.ids)],
                    "groups_id": [
                        Command.set([cls.env.ref("sales_team.group_sale_salesman").id])
                    ],
                }
            )
        )

        def line(product, qty, price):
            return Command.create(
                {
                    "product_id": product.id,
                    "product_uom_qty": qty,
                    "price_unit": price,
                    "tax_id": [Command.clear()],
                }
            )

        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.contact.id,
                "user_id": cls.salesman.id,
                "validity_date": date(2026, 12, 31),
                "order_line": [
                    Command.create({"display_type": "line_section", "name": "Đợt 1"}),
                    line(cls.shirt_s, 10, 100),
                    line(cls.shirt_m, 5, 100),
                    line(cls.thread, 3, 50),
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
        data = self._data(self.order)
        self.assertEqual(data["title"], "BÁO GIÁ")
        self.assertEqual(data["validity_date"], "31/12/2026")
        self.order.action_confirm()
        data = self._data(self.order)
        self.assertEqual(data["title"], "XÁC NHẬN ĐƠN HÀNG")
        self.assertIs(data["validity_date"], False)

    def test_full_rows(self):
        rows = self._data(self.order)["rows"]
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["display_type"], "line_section")
        self.assertEqual(rows[0]["name"], "Đợt 1")
        self.assertEqual(rows[1]["name"], self.shirt_s_name)
        self.assertEqual(rows[2]["name"], self.shirt_m_name)
        self.assertEqual(rows[3]["code"], "CTEST")

    def test_compact_rows(self):
        rows = self._data(self.order, compact=True)["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Áo test")
        self.assertEqual(rows[0]["qty"], 15)
        self.assertEqual(rows[0]["amount"], 1500)
        self.assertTrue(rows[0]["grouped"])
        self.assertEqual(rows[1]["code"], "CTEST")
        self.assertFalse(rows[1]["grouped"])

    def test_render_full(self):
        html = self._html(self.order, ACTION_FULL)
        for text in (
            "BÁO GIÁ",
            self.order.name,
            "Bên bán",
            "Bên mua",
            "Khách hàng test",
            "0300000002",
            "Người liên hệ",
            "Chị Lan",
            "Báo giá có hiệu lực đến",
            "Đợt 1",
            "Xác nhận của khách hàng",
            "1.650",
            "Một nghìn sáu trăm năm mươi đồng",
        ):
            self.assertIn(text, html)
        self.assertNotIn("o_product_variant_grid", html)

    def test_render_compact(self):
        # Core draws no sales grid for this style (variant selection by
        # configurator, not order grid); the compact form does.
        self.assertEqual(self.shirt.product_add_mode, "configurator")
        self.assertFalse(self.order.get_report_matrixes())
        html = self._html(self.order, ACTION_COMPACT)
        self.assertIn("o_product_variant_grid", html)
        self.assertIn("1.500", html)
        self.assertNotIn(self.shirt_s_name, html)
        self.assertNotIn("Đợt 1", html)

    def test_report_domains(self):
        actions = self.env.ref(ACTION_FULL) | self.env.ref(ACTION_COMPACT)

        def valid(order):
            return set(actions.get_valid_action_reports("sale.order", order.ids))

        self.assertEqual(valid(self.order), set(actions.ids))
        self.order._action_cancel()
        self.assertEqual(valid(self.order), set())

    def test_render_as_salesman(self):
        user_env = self.env(
            user=self.salesman,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        # Positive control: the salesman reads the order.
        self.assertEqual(self.order.with_env(user_env).name, self.order.name)
        html = self._html(self.order, ACTION_FULL, env=user_env)
        self.assertIn(self.order.name, html)
