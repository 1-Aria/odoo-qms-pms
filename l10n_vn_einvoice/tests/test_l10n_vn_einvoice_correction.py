# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import EInvoiceBillCase

ORIGINAL = "C26THM_10867.xml"
REPLACEMENT = "C26THM_10868.xml"
DECREASE = "C26THM_10870.xml"
ISSUED_ORIGINAL = "C26TQP_950.xml"
ISSUED_REPLACEMENT = "C26TQP_1118.xml"
ISSUED_ADJUSTED = "C26TQP_931.xml"
ISSUED_ADJUSTMENT = "C26TQP_958.xml"


@tagged("post_install", "-at_install")
class TestEInvoiceCorrection(EInvoiceBillCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hoan_my = cls.env["res.partner"].create(
            {
                "name": "CÔNG TY TNHH KHÓA KÉO HOÀN MỸ",
                "vat": "3700150535",
                "is_company": True,
            }
        )
        cls.hong_nhut = cls.env["res.partner"].create(
            {
                "name": "CÔNG TY TNHH CƠ NHIỆT LẠNH HỒNG NHỰT",
                "vat": "0301097482",
                "is_company": True,
            }
        )

    def _refund(self, amount):
        """A vendor refund entered by hand for Hoàn Mỹ: one line at 8%."""
        return self._document(
            "in_refund",
            partner_id=self.hoan_my.id,
            invoice_line_ids=[
                Command.create(
                    {
                        "name": "adjustment",
                        "quantity": 1.0,
                        "price_unit": amount,
                        "tax_ids": [Command.set(self.tax_8.ids)],
                    }
                )
            ],
        )

    def test_read_relation(self):
        Einvoice = self.env["l10n_vn.einvoice"]
        values = Einvoice._read_xml(self._sample(REPLACEMENT))
        self.assertEqual(values["relation_type"], "1")
        self.assertEqual(values["related_regime"], "1")
        self.assertEqual(values["related_vat"], "3700150535")
        self.assertEqual(values["related_form"], "1")
        self.assertEqual(values["related_symbol"], "C26THM")
        self.assertEqual(values["related_number"], "10867")
        self.assertEqual(values["related_date"], fields.Date.to_date("2026-09-07"))
        self.assertFalse(Einvoice._read_xml(self._sample(ORIGINAL))["relation_type"])

    def test_replacement_after_original(self):
        original_bill = self._upload(ORIGINAL)
        replacement_bill = self._upload(REPLACEMENT)
        original = original_bill.l10n_vn_einvoice_id
        replacement = replacement_bill.l10n_vn_einvoice_id
        self.assertTrue(replacement_bill.invoice_line_ids)
        self.assertEqual(replacement.related_einvoice_id, original)
        self.assertEqual(original.correction_state, "replaced")
        self.assertIn("C26THM-10868", self._bodies(original_bill))
        self.assertIn("It replaces e-invoice C26THM-10867", self._bodies(replacement_bill))

    def test_replacement_before_original(self):
        replacement_bill = self._upload(REPLACEMENT)
        replacement = replacement_bill.l10n_vn_einvoice_id
        self.assertFalse(replacement.related_einvoice_id)
        self.assertIn("which is not in Odoo", self._bodies(replacement_bill))

        original = self._upload(ORIGINAL).l10n_vn_einvoice_id
        self.assertEqual(replacement.related_einvoice_id, original)
        self.assertEqual(original.correction_state, "replaced")

    def test_replaced_document_cannot_post(self):
        original_bill = self._upload(ORIGINAL)
        replacement_bill = self._upload(REPLACEMENT)
        with self.assertRaisesRegex(UserError, "C26THM-10868"):
            original_bill.action_post()
        replacement_bill.action_post()
        self.assertEqual(replacement_bill.state, "posted")

    def test_replaced_posted_original(self):
        original_bill = self._upload(ORIGINAL)
        original_bill.action_post()
        self._upload(REPLACEMENT)
        self.assertEqual(original_bill.state, "posted")
        self.assertEqual(original_bill.l10n_vn_einvoice_correction_state, "replaced")

    def test_adjustment_upload_refused(self):
        original_bill = self._upload(ORIGINAL)
        refused = self._upload(DECREASE)
        self.assertFalse(refused.invoice_line_ids)
        self.assertIn("adjusts an invoice or corrects several", self._bodies(refused))
        self.assertEqual(len(self._einvoices()), 1)

        refund = self._refund(511000)
        self.assertEqual(refund.amount_total, 551880)
        adjustment = self._attach(DECREASE, refund)
        original = original_bill.l10n_vn_einvoice_id
        self.assertEqual(adjustment.related_einvoice_id, original)
        self.assertEqual(adjustment.amount_total, -551880)
        self.assertFalse(adjustment.amounts_differ)
        self.assertEqual(original.correction_state, "adjusted")
        original_bill.action_post()
        self.assertEqual(original_bill.state, "posted")

    def test_several_invoices_refused(self):
        content = self._replaced(REPLACEMENT, "<TCHDon>1</TCHDon>", "<TCHDon>3</TCHDon>", 1)
        bill = self._upload(content)
        self.assertFalse(bill.invoice_line_ids)
        self.assertIn("adjusts an invoice or corrects several", self._bodies(bill))
        self.assertFalse(self._einvoices())

    def test_issued_corrections_by_attach(self):
        first = self._customer_invoice(partner_id=self.hong_nhut.id)
        second = self._customer_invoice(partner_id=self.hong_nhut.id)
        original = self._attach(ISSUED_ORIGINAL, first)
        replacement = self._attach(ISSUED_REPLACEMENT, second)
        self.assertEqual(replacement.related_einvoice_id, original)
        self.assertEqual(original.correction_state, "replaced")
        with self.assertRaises(UserError):
            first.action_post()

        adjusted_invoice = self._customer_invoice()
        adjusted = self._attach(ISSUED_ADJUSTED, adjusted_invoice)
        adjustment = self._attach(ISSUED_ADJUSTMENT, self._customer_invoice())
        self.assertEqual(adjustment.related_einvoice_id, adjusted)
        self.assertEqual(adjusted.correction_state, "adjusted")
        adjusted_invoice.action_post()
        self.assertEqual(adjusted_invoice.state, "posted")

    def test_wizard_preview_relation_and_sign(self):
        wizard = self._wizard(REPLACEMENT, self._bill(partner_id=self.hoan_my.id))
        self.assertFalse(wizard.error)
        self.assertEqual(wizard.preview_relation, "Replaces C26THM-10867")

        wizard = self._wizard(DECREASE, self._refund(511000))
        self.assertFalse(wizard.error)
        self.assertEqual(wizard.preview_relation, "Adjusts C26THM-10867")
        self.assertFalse(wizard.amounts_differ)
