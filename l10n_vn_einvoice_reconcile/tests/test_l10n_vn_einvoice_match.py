# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from .common import COMPANY_VAT, PortalListCase


@tagged("post_install", "-at_install")
class TestPortalMatch(PortalListCase):
    def _einvoice(self, number, booking="posted", **values):
        """A received e-invoice of the test company, keyed like _row()'s default,
        linked to a bill posted before the link, a draft bill, or nothing."""
        vals = {
            "direction": "received",
            "seller_vat": "0314071202",
            "form": "1",
            "symbol": "C26TAA",
            "number": number,
            "invoice_date": "2026-10-01",
            "format_version": "2.1.0",
            "currency_id": self.company.currency_id.id,
            "amount_untaxed": 1000000.0,
            "amount_tax": 80000.0,
            "amount_total": 1080000.0,
            **values,
        }
        if booking:
            move = self._bill()
            if booking == "posted":
                move.action_post()
            vals["move_id"] = move.id
        return self.env["l10n_vn.einvoice"].create(vals)

    def _states(self, batch):
        return {invoice.number: invoice.match_state for invoice in batch.invoice_ids}

    def test_match_states(self):
        self._einvoice("1")
        self._einvoice("2")
        self._einvoice("3", booking=None)
        self._einvoice("4")
        self._einvoice("6")
        self._einvoice("7")
        self._einvoice("8", booking=None)
        adjusted = self._einvoice("9")
        self._einvoice("90", booking=None, relation_type="2", related_einvoice_id=adjusted.id)
        self._einvoice("10")
        self._einvoice("11")
        rows = [
            self._row(stt=1.0, number="1"),
            self._row(stt=2.0, number="2", total=1080001.0),
            self._row(stt=3.0, number="3"),
            self._row(stt=4.0, number="4", total=1085000.0),
            self._row(stt=5.0, number="5"),
            self._row(stt=6.0, number="6"),
            self._row(stt=7.0, number="6"),
            self._row(stt=8.0, number="7", status="Hóa đơn đã bị thay thế"),
            self._row(stt=9.0, number="8", status="Hóa đơn đã bị thay thế"),
            self._row(stt=10.0, number="9", status="Hóa đơn đã bị điều chỉnh"),
            self._row(stt=11.0, number="10", status="Hóa đơn đã bị điều chỉnh"),
            self._row(stt=12.0, number="11", status="Trạng thái lạ"),
        ]
        batch = self._batch("purchase", self._portal_list(rows))
        self.assertEqual(
            self._states(batch),
            {
                "1": "matched",
                "2": "matched",
                "3": "not_booked",
                "4": "amount_diff",
                "5": "portal_only",
                "6": "amounts_to_check",
                "7": "status_diff",
                "8": "matched",
                "9": "matched",
                "10": "status_diff",
                "11": "status_diff",
            },
        )
        off = batch.invoice_ids.filtered(lambda invoice: invoice.number == "4")
        self.assertEqual(off.diff_total, 5000)
        self.assertEqual(batch.issue_count, 7)

    def test_state_follows_booking(self):
        einvoice = self._einvoice("1", booking="draft")
        batch = self._batch("purchase", self._portal_list([self._row(number="1")]))
        self.assertEqual(batch.invoice_ids.match_state, "not_booked")
        einvoice.move_id.action_post()
        self.assertEqual(batch.invoice_ids.match_state, "matched")

    def test_new_einvoice_links(self):
        batch = self._batch("purchase", self._portal_list([self._row(number="5")]))
        self.assertEqual(batch.invoice_ids.match_state, "portal_only")
        einvoice = self._einvoice("5")
        self.assertEqual(batch.invoice_ids.einvoice_id, einvoice)
        self.assertEqual(batch.invoice_ids.match_state, "matched")

    def test_match_again(self):
        einvoice = self._einvoice("1")
        batch = self._batch("purchase", self._portal_list([self._row(number="1")]))
        batch.invoice_ids.einvoice_id = False
        self.assertEqual(batch.invoice_ids.match_state, "portal_only")
        batch.action_match()
        self.assertEqual(batch.invoice_ids.einvoice_id, einvoice)
        self.assertEqual(batch.invoice_ids.match_state, "matched")

    def test_direction_respected(self):
        self._einvoice("1", booking=None, direction="issued")
        batch = self._batch("purchase", self._portal_list([self._row(number="1")]))
        self.assertEqual(batch.invoice_ids.match_state, "portal_only")

    def test_odoo_only_einvoices(self):
        self._einvoice("1")
        missing = self._einvoice("50", booking=None)
        self._einvoice("51", booking=None, invoice_date="2026-09-15")
        batch = self._batch("purchase", self._portal_list([self._row(number="1")]))
        self.assertEqual(batch.odoo_only_einvoice_count, 1)
        self.assertEqual(
            self.env["l10n_vn.einvoice"].search(batch._odoo_only_einvoice_domain()), missing
        )

    def test_documents_without_einvoice(self):
        self._einvoice("1")
        vietnamese = self.env["res.partner"].create(
            {"name": "Nhà cung cấp VN", "vat": "0300000001", "country_id": self.env.ref("base.vn").id}
        )
        foreign = self.env["res.partner"].create(
            {"name": "Foreign Supplier", "vat": "US123456789", "country_id": self.env.ref("base.us").id}
        )
        counted = self._bill(partner_id=vietnamese.id)
        counted.action_post()
        self._bill(partner_id=foreign.id).action_post()
        self._bill(partner_id=vietnamese.id)  # a draft
        batch = self._batch("purchase", self._portal_list([self._row(number="1")]))
        self.assertEqual(batch.odoo_only_document_count, 1)
        self.assertEqual(
            self.env["account.move"].search(batch._odoo_only_document_domain()), counted
        )

        sale = self._customer_invoice()
        sale.action_post()
        sales_row = self._row(number="2001", symbol="C26TQP", seller_vat=COMPANY_VAT, buyer_vat=None)
        sales_batch = self._batch("sale", self._portal_list([sales_row]))
        self.assertEqual(
            self.env["account.move"].search(sales_batch._odoo_only_document_domain()), sale
        )

    def test_match_access(self):
        def user(login, group):
            return new_test_user(
                self.env,
                login=login,
                groups=f"base.group_user,{group}",
                company_id=self.company.id,
                company_ids=[Command.set(self.company.ids)],
            )

        self._einvoice("1")
        batch = self._batch("purchase", self._portal_list([self._row(number="1")]))
        batch.invoice_ids.einvoice_id = False
        reader = user("portal_match_reader", "account.group_account_readonly")
        accountant = user("portal_match_accountant", "account.group_account_user")
        with self.assertRaises(AccessError), self.cr.savepoint():
            batch.with_user(reader).action_match()
        # Positive control.
        batch.with_user(accountant).action_match()
        self.assertEqual(batch.invoice_ids.match_state, "matched")
