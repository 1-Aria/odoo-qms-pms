# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.tests import TransactionCase, tagged

from ..models.l10n_vn_voucher import DATE_DOTTED

# The blocks as a form uses them: one voucher_page per copy label.
TEST_ARCH = """
<t t-name="l10n_vn_voucher.test_blocks">
    <t t-foreach="env['l10n_vn.voucher']._copy_labels(copies)" t-as="copy_label">
        <t t-call="l10n_vn_voucher.voucher_page">
            <t t-call="l10n_vn_voucher.voucher_header"/>
            <t t-call="l10n_vn_voucher.voucher_title"/>
            <t t-call="l10n_vn_voucher.voucher_field">
                <t t-set="label" t-value="'Lý do'"/>
                <t t-set="value" t-value="reason"/>
            </t>
            <t t-call="l10n_vn_voucher.voucher_amount_words"/>
            <t t-if="with_order">
                <t t-call="l10n_vn_voucher.voucher_party"/>
                <t t-call="l10n_vn_voucher.voucher_order_lines"/>
                <t t-call="l10n_vn_voucher.voucher_variant_grids"/>
                <t t-call="l10n_vn_voucher.voucher_totals"/>
            </t>
            <t t-call="l10n_vn_voucher.voucher_signatures"/>
        </t>
    </t>
</t>
"""


@tagged("post_install", "-at_install")
class TestVoucherLayout(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vnd = cls.env.ref("base.VND")
        cls.usd = cls.env.ref("base.USD")
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Voucher Test Partner",
                "street": "12 Lê Lợi",
                "city": "Hồ Chí Minh",
                "country_id": cls.env.ref("base.vn").id,
            }
        )
        cls.view = cls.env["ir.ui.view"].create(
            {
                "name": "l10n_vn_voucher test blocks",
                "type": "qweb",
                "key": "l10n_vn_voucher.test_blocks",
                "arch": TEST_ARCH,
            }
        )
        cls.helpers = cls.env["l10n_vn.voucher"]

        # A configurable template with two variants, and a product without.
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
        cls.thread = cls.env["product.product"].create(
            {"name": "Chỉ test", "default_code": "CTEST"}
        )
        cls.customer = cls.env["res.partner"].create(
            {"name": "Khách hàng test", "is_company": True, "vat": "0300000002"}
        )
        cls.contact = cls.env["res.partner"].create(
            {"name": "Chị Lan", "parent_id": cls.customer.id}
        )

    def _render(self, **values):
        base = {
            "copies": False,
            "company": self.company,
            "department": "Kho Chi Lăng",
            "form_code": "01-VT",
            "title": "PHIẾU NHẬP KHO",
            "voucher_date": date(2026, 11, 5),
            "number": "WH/IN/00001",
            "debit_accounts": ["152"],
            "credit_accounts": ["3399"],
            "reason": "Nhập kho mua hàng",
            "currency": self.vnd,
            "amount": 10000,
            "sign_date": date(2026, 11, 5),
            "signers": [
                {"role": "Người lập phiếu", "name": "Nguyễn Văn A"},
                {"role": "Thủ kho"},
            ],
        }
        base.update(values)
        qweb = self.env["ir.qweb"].with_context(lang="vi_VN")
        return str(qweb._render(self.view.id, base))

    def _row(self, product, qty, price, **values):
        row = {
            "display_type": False,
            "name": product.display_name,
            "code": product.default_code or "",
            "uom": product.uom_id.name,
            "qty": qty,
            "price": price,
            "discount": 0.0,
            "taxes": "",
            "amount": qty * price,
            "product": product,
        }
        row.update(values)
        return row

    def test_amount_to_words(self):
        cases = {
            0: "Không đồng",
            15: "Mười lăm đồng",
            105: "Một trăm lẻ năm đồng",
            1005000: "Một triệu năm nghìn đồng",
            1000000.4: "Một triệu đồng",
            999.5: "Một nghìn đồng",
            -2500: "Hai nghìn năm trăm đồng",
        }
        for amount, words in cases.items():
            self.assertEqual(self.vnd.l10n_vn_amount_to_words(amount), words, amount)
        self.assertEqual(self.usd.l10n_vn_amount_to_words(1000), "")

    def test_copy_labels(self):
        self.assertEqual(
            self.helpers._copy_labels("Liên 1: A\n\n  Liên 2: B \n"),
            ["Liên 1: A", "Liên 2: B"],
        )
        for empty in ("", False, "\n \n"):
            self.assertEqual(self.helpers._copy_labels(empty), [False], repr(empty))

    def test_date_text(self):
        self.assertEqual(
            self.helpers._date_text(date(2026, 11, 5)), "Ngày 05 tháng 11 năm 2026"
        )
        self.assertEqual(self.helpers._date_text(False), DATE_DOTTED)

    def test_address(self):
        address = self.helpers._address(self.partner)
        self.assertNotIn("\n", address)
        self.assertIn("12 Lê Lợi", address)
        self.assertIn("Hồ Chí Minh", address)
        self.assertEqual(self.helpers._address(self.env["res.partner"]), "")

    def test_copies_render(self):
        html = self._render(copies="Liên 1: A\nLiên 2: B\nLiên 3: C")
        self.assertEqual(html.count("l10n_vn_voucher_page"), 3)
        self.assertEqual(html.count("page-break-before"), 2)
        for label in ("Liên 1: A", "Liên 2: B", "Liên 3: C"):
            self.assertEqual(html.count(label), 1, label)

        html = self._render(copies=False)
        self.assertEqual(html.count("l10n_vn_voucher_page"), 1)
        self.assertNotIn("page-break-before", html)

    def test_blocks_render(self):
        html = self._render()
        for text in (
            "Mẫu số",
            "01-VT",
            self.company.name,
            "Kho Chi Lăng",
            "PHIẾU NHẬP KHO",
            "Ngày 05 tháng 11 năm 2026",
            "WH/IN/00001",
            "152",
            "3399",
            "Nhập kho mua hàng",
            "Mười nghìn đồng",
            "Người lập phiếu",
            "Nguyễn Văn A",
            "Thủ kho",
            "(Ký, họ tên)",
        ):
            self.assertIn(text, html)

        html = self._render(debit_accounts=[], credit_accounts=[], reason="")
        self.assertIn("Nợ:", html)
        # Debit, credit and the empty reason are dotted spaces.
        self.assertGreaterEqual(html.count("o_dots"), 3)

        html = self._render(show_accounts=False)
        self.assertNotIn("Nợ:", html)

    def test_compact_rows(self):
        section = {"display_type": "line_section", "name": "Đợt 1"}
        rows = self.helpers._compact_rows(
            [
                section,
                self._row(self.shirt_s, 10, 100),
                self._row(self.shirt_m, 5, 100),
                self._row(self.thread, 3, 50),
                self._row(self.shirt_m, 2, 90),
            ]
        )
        self.assertEqual(len(rows), 3)
        first, second, third = rows
        self.assertEqual(first["name"], "Áo test")
        self.assertEqual(first["code"], "")
        self.assertEqual(first["qty"], 15)
        self.assertEqual(first["amount"], 1500)
        self.assertTrue(first["grouped"])
        self.assertEqual(second["product"], self.thread)
        self.assertFalse(second["grouped"])
        self.assertEqual(third["price"], 90)
        self.assertEqual(third["qty"], 2)
        self.assertTrue(third["grouped"])

        # A configurable template on one row only is not grouped.
        single = self.helpers._compact_rows([self._row(self.shirt_s, 10, 100)])
        self.assertEqual(len(single), 1)
        self.assertFalse(single[0]["grouped"])
        self.assertEqual(single[0]["name"], self.shirt_s.display_name)

    def test_order_blocks_render(self):
        order = {
            "with_order": True,
            "party_title": "Bên mua",
            "partner": self.contact,
            "rows": [
                {"display_type": "line_section", "name": "Đợt 1"},
                self._row(self.shirt_s, 10, 100, taxes="10%"),
            ],
            "show_discount": False,
            "untaxed": 1000,
            "tax": 100,
            "total": 1100,
        }
        html = self._render(**order)
        for text in (
            "Bên mua",
            "Khách hàng test",
            "0300000002",
            "Người liên hệ",
            "Chị Lan",
            "Đợt 1",
            "Thuế",
            "1.100",
            "Một nghìn một trăm đồng",
        ):
            self.assertIn(text, html)
        self.assertNotIn("CK (%)", html)

        self.assertNotIn("o_product_variant_grid", html)

        grid = {
            "header": [{"name": "Áo test"}, {"name": "S"}, {"name": "M"}],
            "matrix": [[{"name": "Trắng"}, {"qty": 10.0}, {"qty": 2.5}]],
        }
        html = self._render(**dict(order, grids=[grid]))
        self.assertIn("o_product_variant_grid", html)
        self.assertIn("Trắng", html)
        self.assertIn("2,5", html)

        html = self._render(**dict(order, show_discount=True))
        self.assertIn("CK (%)", html)

        html = self._render(**dict(order, currency=self.usd))
        self.assertIn("Loại tiền:", html)
        self.assertIn("USD", html)
        self.assertNotIn("đồng", html)

    def test_qty_text(self):
        self.assertEqual(self.helpers._qty_text(10.0), "10")
        self.assertEqual(self.helpers._qty_text(2.5), "2,5")
        self.assertEqual(self.helpers._qty_text(False), "0")

    def test_header_without_code(self):
        html = self._render(form_code=False, department=None)
        self.assertNotIn("Mẫu số", html)
        self.assertNotIn("Bộ phận:", html)
