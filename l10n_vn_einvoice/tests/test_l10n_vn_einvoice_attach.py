# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from .common import EInvoiceCase

RECEIVED = "C26TQL394.xml"
ISSUED = "invoice_xml_0317253698_C26TQP_2160.xml"
TO_BRANCH = "1602181122_1C26TTD_130.xml"


@tagged("post_install", "-at_install")
class TestEInvoiceAttach(EInvoiceCase):
    def _einvoices(self):
        return self.env["l10n_vn.einvoice"].search([("company_id", "=", self.env.company.id)])

    def test_attach_received_to_bill(self):
        bill = self._bill(ref="SUPPLIER-REF")
        before = (bill.partner_id, bill.amount_total, bill.ref, bill.invoice_date)
        einvoice = self._attach(RECEIVED, bill)

        self.assertEqual(self._einvoices(), einvoice)
        self.assertEqual(einvoice.direction, "received")
        self.assertEqual(einvoice.move_id, bill)
        self.assertEqual(einvoice.state, "draft")
        self.assertEqual(einvoice.name, "C26TQL-394")

        attachment = einvoice.attachment_id
        self.assertEqual((attachment.res_model, attachment.res_id), (einvoice._name, einvoice.id))
        self.assertEqual(attachment.raw, self._sample(RECEIVED))

        message = bill.message_ids.filtered(lambda m: "C26TQL-394" in (m.body or ""))
        self.assertEqual(len(message), 1)
        self.assertEqual(message.attachment_ids.raw, self._sample(RECEIVED))
        self.assertNotEqual(message.attachment_ids, attachment)

        self.assertEqual(
            (bill.partner_id, bill.amount_total, bill.ref, bill.invoice_date), before
        )

    def test_state_follows_document(self):
        bill = self._bill()
        einvoice = self._attach(RECEIVED, bill)
        bill.action_post()
        self.assertEqual(einvoice.state, "booked")
        bill.button_draft()
        bill.button_cancel()
        self.assertEqual(einvoice.state, "not_booked")

    def test_attach_issued_to_invoice(self):
        invoice = self._customer_invoice()
        einvoice = self._attach(ISSUED, invoice)
        self.assertEqual(einvoice.direction, "issued")
        self.assertEqual(einvoice.move_id, invoice)
        self.assertFalse(einvoice.buyer_vat)

    def test_wrong_company_refused(self):
        with self.assertRaisesRegex(UserError, "0317253698-001"):
            self._attach(TO_BRANCH, self._bill())
        self.assertFalse(self._einvoices())

    def test_direction_against_document_refused(self):
        with self.assertRaisesRegex(UserError, "vendor bill"):
            self._attach(RECEIVED, self._customer_invoice())
        with self.assertRaisesRegex(UserError, "customer invoice"):
            self._attach(ISSUED, self._bill())
        self.assertFalse(self._einvoices())

    def test_cancelled_document_refused(self):
        bill = self._bill()
        bill.button_cancel()
        with self.assertRaisesRegex(UserError, "cancelled"):
            self._attach(RECEIVED, bill)

    def test_duplicate_on_live_document_refused(self):
        first = self._bill()
        einvoice = self._attach(RECEIVED, first)
        with self.assertRaisesRegex(UserError, "already attached"):
            self._attach(RECEIVED, self._bill())
        self.assertEqual(self._einvoices(), einvoice)
        self.assertEqual(einvoice.move_id, first)

    def test_relink_after_cancel(self):
        first = self._bill()
        einvoice = self._attach(RECEIVED, first)
        attachment = einvoice.attachment_id
        first.button_cancel()
        second = self._bill()
        relinked = self._attach(RECEIVED, second)
        self.assertEqual(relinked, einvoice)
        self.assertEqual(einvoice.move_id, second)
        self.assertEqual(einvoice.attachment_id, attachment)
        self.assertEqual(self._einvoices(), einvoice)

    def test_document_deleted(self):
        bill = self._bill()
        einvoice = self._attach(RECEIVED, bill)
        bill.unlink()
        self.assertTrue(einvoice.exists())
        self.assertFalse(einvoice.move_id)
        self.assertEqual(einvoice.state, "not_booked")
        self.assertTrue(einvoice.attachment_id.raw)

    def test_key_normalised(self):
        self._attach(RECEIVED, self._bill())
        padded = self._edited(RECEIVED, "<SHDon>394</SHDon>", "<SHDon>00394</SHDon>")
        with self.assertRaisesRegex(UserError, "already attached"):
            self._attach(padded, self._bill())

    def test_key_unique_in_database(self):
        Einvoice = self.env["l10n_vn.einvoice"]
        values = Einvoice._read_xml(self._sample(RECEIVED))
        Einvoice.create({**values, "direction": "received"})
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                Einvoice.create({**values, "direction": "received"})
                self.env.flush_all()

        other_company = self._create_company(
            "E-Invoice Second Company", "0100000001", chart=False
        )
        other = Einvoice.with_company(other_company).create(
            {**values, "direction": "received", "company_id": other_company.id}
        )
        self.assertTrue(other)

    def test_wizard_preview(self):
        self.partner_a.vat = "0100109106"
        bill = self._bill()
        wizard = self._wizard(RECEIVED, bill)
        self.assertFalse(wizard.error)
        self.assertEqual(wizard.preview_name, "C26TQL-394")
        self.assertTrue(wizard.partner_differs)
        self.assertTrue(wizard.date_differs)
        self.assertTrue(wizard.amounts_differ)

        self.partner_a.vat = "0308965730"
        wizard = self._wizard(RECEIVED, bill)
        self.assertFalse(wizard.partner_differs)

        wizard = self._wizard(RECEIVED, self._customer_invoice())
        self.assertIn("vendor bill", wizard.error)
        self.assertFalse(wizard.preview_name)

    def test_wizard_read_as_web_client(self):
        """After a save the web client reads the wizard with bin_size=True, which
        turns the file into its size; the preview must still read the content."""
        bill = self._bill()
        wizard = self._wizard(RECEIVED, bill)
        wizard.invalidate_recordset()
        values = wizard.with_context(bin_size=True).read(["preview_name", "error"])[0]
        self.assertFalse(values["error"])
        self.assertEqual(values["preview_name"], "C26TQL-394")
        wizard.with_context(bin_size=True).action_attach()
        self.assertEqual(bill.l10n_vn_einvoice_id.name, "C26TQL-394")

    def test_access_invoicing_user(self):
        user = new_test_user(
            self.env,
            login="einvoice_invoicing",
            groups="base.group_user,account.group_account_invoice",
            company_id=self.env.company.id,
            company_ids=[Command.set(self.env.company.ids)],
        )
        bill = self._bill()

        # Positive control: the user attaches and reads.
        self.env["l10n_vn.einvoice.attach"].with_user(user).create(
            {
                "move_id": bill.id,
                "file": base64.b64encode(self._sample(RECEIVED)),
                "filename": RECEIVED,
            }
        ).action_attach()
        einvoice = bill.l10n_vn_einvoice_id.with_user(user)
        self.assertEqual(einvoice.read(["name"])[0]["name"], "C26TQL-394")

        with self.assertRaises(AccessError):
            einvoice.unlink()

        Tax = self.env["l10n_vn.einvoice.tax"].with_user(user)
        self.assertFalse(Tax.search([]))
        with self.assertRaises(AccessError):
            Tax.create({"code": "10%"})

    def test_vat_code_normalised_unique(self):
        Tax = self.env["l10n_vn.einvoice.tax"]
        row = Tax.create({"code": " kct "})
        self.assertEqual(row.code, "KCT")
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                Tax.create({"code": "KCT"})
                self.env.flush_all()
