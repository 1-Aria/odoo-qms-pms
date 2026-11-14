# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

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
        return str(self.env["ir.qweb"]._render(self.view.id, base))

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
