# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.l10n_vn_einvoice import normalise_number, normalise_symbol, normalise_vat
from .common import EInvoiceCase


@tagged("post_install", "-at_install")
class TestEInvoiceRead(EInvoiceCase):
    def _read(self, content):
        if isinstance(content, str):
            content = self._sample(content)
        return self.env["l10n_vn.einvoice"]._read_xml(content)

    def test_normalise_helpers(self):
        self.assertEqual(normalise_vat(" 0317 253698-001 "), "0317253698-001")
        self.assertEqual(normalise_symbol(" c26tql "), "C26TQL")
        self.assertEqual(normalise_number("00029704"), "29704")
        self.assertEqual(normalise_number("0"), "0")
        for empty in (None, "  "):
            self.assertEqual(normalise_vat(empty), "")
            self.assertEqual(normalise_symbol(empty), "")
            self.assertEqual(normalise_number(empty), "")

    def test_read_vat_invoice(self):
        values = self._read("C26TQL394.xml")
        self.assertEqual(values["format_version"], "2.1.0")
        self.assertEqual(values["form"], "1")
        self.assertEqual(values["symbol"], "C26TQL")
        self.assertEqual(values["number"], "394")
        self.assertEqual(values["invoice_date"], fields.Date.to_date("2026-10-21"))
        self.assertEqual(values["tax_authority_code"], "0061B2D1564D8848E0B3F42D7B2A7D513A")
        self.assertEqual(values["seller_vat"], "0308965730")
        self.assertEqual(values["buyer_vat"], "0317253698")
        self.assertEqual(values["provider_vat"], "0100109106")
        self.assertEqual(values["currency_id"], self.env.ref("base.VND").id)
        self.assertEqual(values["exchange_rate"], 1.0)
        self.assertEqual(values["amount_untaxed"], 439815200)
        self.assertEqual(values["amount_tax"], 35185216)
        self.assertEqual(values["amount_total"], 475000416)

    def test_read_decimal_text(self):
        values = self._read("1_001_C26TAA_21013_8446.xml")
        self.assertEqual(values["amount_untaxed"], 5411000)
        self.assertEqual(values["amount_tax"], 432880)
        self.assertEqual(values["amount_total"], 5843880)

    def test_read_sales_invoice(self):
        values = self._read("2_001_C26TMX_41_10860.xml")
        self.assertEqual(values["form"], "2")
        self.assertEqual(values["amount_untaxed"], 48960000)
        self.assertEqual(values["amount_tax"], 0)
        self.assertEqual(values["amount_total"], 48960000)

    def test_read_uncoded(self):
        values = self._read("K26TDB122621.xml")
        self.assertEqual(values["symbol"], "K26TDB")
        self.assertFalse(values["tax_authority_code"])

    def test_read_version_2_1_1(self):
        values = self._read(
            self._edited("C26TQL394.xml", "<PBan>2.1.0</PBan>", "<PBan>2.1.1</PBan>")
        )
        self.assertEqual(values["format_version"], "2.1.1")
        self.assertEqual((values["symbol"], values["number"]), ("C26TQL", "394"))
        self.assertEqual(values["amount_total"], 475000416)

    def test_unknown_version_refused(self):
        content = self._edited("C26TQL394.xml", "<PBan>2.1.0</PBan>", "<PBan>9.9.9</PBan>")
        with self.assertRaisesRegex(UserError, "9.9.9"):
            self._read(content)

    def test_form_refused(self):
        content = self._edited(
            "C26TQL394.xml", "<KHMSHDon>1</KHMSHDon>", "<KHMSHDon>7</KHMSHDon>"
        )
        with self.assertRaisesRegex(UserError, "form 7"):
            self._read(content)

    def test_coded_without_code_refused(self):
        content = self._sample("C26TQL394.xml")
        content, count = re.subn(rb"<MCCQT[^>]*>[^<]*</MCCQT>", b"", content)
        self.assertEqual(count, 1)
        with self.assertRaisesRegex(UserError, "no tax authority code"):
            self._read(content)

    def test_not_an_einvoice_refused(self):
        for content in (b"<Invoice/>", b"not xml"):
            with self.assertRaisesRegex(UserError, "not a Vietnamese e-invoice"):
                self._read(content)

    def test_inactive_currency_refused(self):
        inactive = (
            self.env["res.currency"]
            .with_context(active_test=False)
            .search([("active", "=", False)], limit=1)
        )
        self.assertTrue(inactive, "the test needs an inactive currency")
        content = self._edited(
            "C26TQL394.xml", "<DVTTe>VND</DVTTe>", f"<DVTTe>{inactive.name}</DVTTe>"
        )
        with self.assertRaisesRegex(UserError, inactive.name):
            self._read(content)
