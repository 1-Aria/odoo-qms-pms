# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import AccessError, RedirectWarning, UserError, ValidationError
from odoo.tests import new_test_user, tagged

from .common import EInvoiceBillCase

VAT_INVOICE = "C26TQL394.xml"
FIVE_LINES = "1_001_C26TAA_21013_8446.xml"
FUEL = "K26TDB122621.xml"
SALES_INVOICE = "2_001_C26TMX_41_10860.xml"
ISSUED = "invoice_xml_0317253698_C26TQP_2160.xml"
TO_BRANCH = "1602181122_1C26TTD_130.xml"


@tagged("post_install", "-at_install")
class TestEInvoiceBill(EInvoiceBillCase):
    # ------------------------------------------------------------------
    # Creating bills
    # ------------------------------------------------------------------

    def test_upload_creates_bill(self):
        bill = self._upload(VAT_INVOICE)
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(bill.state, "draft")
        self.assertEqual(bill.partner_id, self.supplier)
        self.assertEqual(bill.ref, "C26TQL-394")
        self.assertEqual(bill.invoice_date, fields.Date.to_date("2026-10-21"))
        line = bill.invoice_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.name, "VẢI V.43771-A7+A0")
        self.assertEqual(line.quantity, 49979)
        self.assertEqual(line.price_unit, 8800)
        self.assertEqual(line.tax_ids, self.tax_8)
        self.assertTrue(line.is_imported)
        self.assertTrue(line.account_id)
        self.assertEqual(bill.amount_untaxed, 439815200)
        self.assertEqual(bill.amount_tax, 35185216)
        self.assertEqual(bill.amount_total, 475000416)
        einvoice = bill.l10n_vn_einvoice_id
        self.assertEqual(einvoice.state, "draft")
        self.assertFalse(einvoice.amounts_differ)
        self.assertIn("Created from e-invoice C26TQL-394", self._bodies(bill))

    def test_upload_lines_and_no_partner(self):
        bill = self._upload(FIVE_LINES)
        self.assertEqual(
            bill.invoice_line_ids.mapped("price_unit"),
            [1204000, 2282000, 455000, 987000, 483000],
        )
        self.assertEqual(bill.amount_untaxed, 5411000)
        self.assertEqual(bill.amount_tax, 432880)
        self.assertEqual(bill.amount_total, 5843880)
        self.assertFalse(bill.partner_id)
        self.assertIn("0314071202", self._bodies(bill))

    def test_upload_fallback_line(self):
        bill = self._upload(FUEL)
        line = bill.invoice_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual((line.quantity, line.price_unit), (1.0, 5500000))
        self.assertIn("180.92 Lít × 30400", line.name)
        self.assertFalse(line.tax_ids)
        self.assertEqual(bill.amount_tax, 0)
        self.assertEqual(bill.amount_total, 5500000)
        self.assertIn("quantity × price does not give", self._bodies(bill))

    def test_upload_sales_invoice(self):
        (self.code_8 | self.code_kkknt).unlink()
        bill = self._upload(SALES_INVOICE)
        line = bill.invoice_line_ids
        self.assertEqual((line.quantity, line.price_unit), (2040, 24000))
        self.assertFalse(line.tax_ids)
        self.assertEqual(bill.amount_total, 48960000)

    def test_tax_corrected_within_rounding(self):
        content = self._replaced(FIVE_LINES, "432880.0", "432881.0", 2)
        content = self._replaced(content, "5843880.0", "5843881.0", 1)
        bill = self._upload(content)
        self.assertEqual(bill.amount_tax, 432881)
        self.assertEqual(bill.amount_total, 5843881)
        self.assertNotIn("not corrected", self._bodies(bill))
        self.assertFalse(bill.l10n_vn_einvoice_id.amounts_differ)

    def test_tax_not_corrected_beyond_rounding(self):
        content = self._replaced(FIVE_LINES, "432880.0", "432890.0", 2)
        content = self._replaced(content, "5843880.0", "5843890.0", 1)
        bill = self._upload(content)
        self.assertEqual(bill.amount_tax, 432880)
        self.assertIn("not corrected", self._bodies(bill))
        self.assertTrue(bill.l10n_vn_einvoice_id.amounts_differ)

    def test_missing_vat_code(self):
        self.code_8.unlink()
        bill = self._upload(VAT_INVOICE)
        self.assertFalse(bill.invoice_line_ids)
        self.assertIn("8%", self._bodies(bill))
        self.assertFalse(self._einvoices())

        self.env["l10n_vn.einvoice.tax"].create({"code": "8%", "tax_id": self.tax_8.id})
        attachment = self.env["ir.attachment"].create(
            {
                "name": VAT_INVOICE,
                "raw": self._sample(VAT_INVOICE),
                "res_model": "account.move",
                "res_id": bill.id,
            }
        )
        bill.message_post(attachment_ids=attachment.ids)
        self.assertEqual(len(bill.invoice_line_ids), 1)
        self.assertEqual(bill.l10n_vn_einvoice_id.name, "C26TQL-394")

    def test_duplicate_upload_redirects(self):
        self._upload(VAT_INVOICE)
        with self.assertRaises(RedirectWarning), self.cr.savepoint():
            self._upload(VAT_INVOICE)
        self.assertEqual(len(self._einvoices()), 1)

    def test_upload_after_cancelled_attach(self):
        first = self._bill()
        einvoice = self._attach(VAT_INVOICE, first)
        first.button_cancel()
        bill = self._upload(VAT_INVOICE)
        self.assertEqual(bill.l10n_vn_einvoice_id, einvoice)
        self.assertEqual(len(bill.invoice_line_ids), 1)

    def test_attach_never_imports(self):
        """Attaching posts the XML in the chatter; core's chatter hook must not read
        it as an import, whatever the bill's state (account_move.py:6490-6502).
        Its notes are translated, so the test counts messages rather than matching
        their text: attaching adds exactly one."""
        empty = self._document("in_invoice", invoice_line_ids=[])
        before = self._message_count(empty)
        self._attach(VAT_INVOICE, empty)
        self.assertFalse(empty.invoice_line_ids)
        self.assertEqual(self._message_count(empty), before + 1)

        with_lines = self._bill()
        before = self._message_count(with_lines)
        self._attach(FIVE_LINES, with_lines)
        self.assertEqual(len(with_lines.invoice_line_ids), 1)
        self.assertEqual(self._message_count(with_lines), before + 1)

        posted = self._bill()
        posted.action_post()
        before = self._message_count(posted)
        self._attach(FUEL, posted)
        self.assertEqual(self._message_count(posted), before + 1)

    def test_upload_refusals(self):
        adjusted = self._replaced(
            VAT_INVOICE,
            "<HDCTTChinh>0</HDCTTChinh>",
            "<HDCTTChinh>0</HDCTTChinh><TTHDLQuan><TCHDon>2</TCHDon></TTHDLQuan>",
            1,
        )
        cases = [
            (ISSUED, "in_invoice", "Only received e-invoices"),
            (TO_BRANCH, "in_invoice", "0317253698-001"),
            (adjusted, "in_invoice", "adjusts an invoice or corrects several"),
            (VAT_INVOICE, "in_refund", "Only received e-invoices"),
        ]
        for content, move_type, text in cases:
            bill = self._upload(content, move_type=move_type)
            self.assertFalse(bill.invoice_line_ids)
            self.assertIn(text, self._bodies(bill))
        self.assertFalse(self._einvoices())

    # ------------------------------------------------------------------
    # Partners
    # ------------------------------------------------------------------

    def test_partner_never_matched_by_name(self):
        self.supplier.vat = False
        self.env["res.partner"].create({"name": "CÔNG TY TNHH QUANG QUANG LINH"})
        bill = self._upload(VAT_INVOICE)
        self.assertFalse(bill.partner_id)

    def test_several_partners(self):
        self.env["res.partner"].create({"name": "Same code", "vat": "0308965730"})
        bill = self._upload(VAT_INVOICE)
        self.assertFalse(bill.partner_id)
        self.assertIn("Several partners", self._bodies(bill))

    def test_create_supplier(self):
        bill = self._upload(FIVE_LINES)
        action = bill.l10n_vn_einvoice_id.action_create_partner()
        partner = self.env["res.partner"].browse(action["res_id"])
        self.assertEqual(partner.name, "CÔNG TY CỔ PHẦN VIỆC LÀM 24H")
        self.assertEqual(partner.vat, "0314071202")
        self.assertTrue(partner.street.startswith("Tầng M"))
        self.assertEqual(partner.phone, "(028) 7308 2424")
        self.assertEqual(partner.country_id, self.env.ref("base.vn"))
        self.assertTrue(partner.is_company)
        self.assertEqual(bill.partner_id, partner)

    def test_partner_change_keeps_taxes(self):
        bill = self._upload(FIVE_LINES)
        bill.partner_id = self.partner_a
        for line in bill.invoice_line_ids:
            self.assertEqual(line.tax_ids, self.tax_8)
        self.assertEqual(
            bill.invoice_line_ids.mapped("price_unit"),
            [1204000, 2282000, 455000, 987000, 483000],
        )

    # ------------------------------------------------------------------
    # Posting check
    # ------------------------------------------------------------------

    def test_posting_fills_partner_vat(self):
        bill = self._upload(FIVE_LINES)
        bill.partner_id = self.partner_a
        bill.action_post()
        self.assertEqual(self.partner_a.vat, "0314071202")
        self.assertIn("Tax code 0314071202 set", self._bodies(self.partner_a))

    def test_posting_refused_on_mismatch(self):
        bill = self._upload(VAT_INVOICE)
        bill.partner_id = self.env["res.partner"].create(
            {"name": "Other", "vat": "0100000002"}
        )
        with self.assertRaisesRegex(UserError, "0100000002"):
            bill.action_post()

        # The same through step 1's path: a bill with an attached e-invoice.
        self.partner_a.vat = "0100000003"
        attached = self._bill()
        self._attach(FUEL, attached)
        with self.assertRaisesRegex(UserError, "0100000003"):
            attached.action_post()

    def test_posting_refused_when_code_held_elsewhere(self):
        bill = self._upload(FIVE_LINES)
        holder = self.env["res.partner"].create({"name": "Code Holder", "vat": "0314071202"})
        bill.partner_id = self.partner_a
        with self.assertRaisesRegex(UserError, holder.name):
            bill.action_post()
        self.assertFalse(self.partner_a.vat)

    def test_posting_issued_to_consumer(self):
        invoice = self._customer_invoice()
        self._attach(ISSUED, invoice)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    # ------------------------------------------------------------------
    # Configuration and access
    # ------------------------------------------------------------------

    def test_vat_table_refuses_unsuitable_taxes(self):
        VatCode = self.env["l10n_vn.einvoice.tax"]
        sale_tax = self.env["account.tax"].create(
            {"name": "Test sale 10%", "amount": 10.0, "type_tax_use": "sale"}
        )
        included = self.env["account.tax"].create(
            {
                "name": "Test included 10%",
                "amount": 10.0,
                "type_tax_use": "purchase",
                "price_include_override": "tax_included",
            }
        )
        with self.assertRaises(ValidationError):
            VatCode.create({"code": "10%", "tax_id": sale_tax.id})
        with self.assertRaises(ValidationError):
            VatCode.create({"code": "10%", "tax_id": included.id})

    def test_access_invoicing_user_upload(self):
        user = new_test_user(
            self.env,
            login="einvoice_uploader",
            groups="base.group_user,account.group_account_invoice",
            company_id=self.company.id,
            company_ids=[(6, 0, self.company.ids)],
        )
        bill = self._upload(FIVE_LINES, user=user)
        self.assertEqual(len(bill.invoice_line_ids), 5)
        bill.partner_id = self.partner_a.with_user(user)
        bill.action_post()
        self.assertEqual(self.partner_a.vat, "0314071202")

        with self.assertRaises(AccessError):
            bill.l10n_vn_einvoice_id.action_create_partner()
