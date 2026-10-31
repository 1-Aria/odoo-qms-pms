# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import unicodedata

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from .common import COMPANY_VAT, PortalListCase


@tagged("post_install", "-at_install")
class TestPortalImport(PortalListCase):
    def _three_purchase_rows(self):
        return [
            self._row(stt=1.0, symbol="C26TAA", number="21013", seller_vat="0314071202",
                      untaxed=5411000.0, tax=432880.0, total=5843880.0),
            self._row(stt=2.0, symbol="C26TQL", number="394", seller_vat="0308965730",
                      untaxed=439815200.0, tax=35185216.0, total=475000416.0),
            self._row(stt=3.0, form="2", symbol="C26TMX", number="41", seller_vat="1701032837",
                      untaxed=None, tax=None, discount=None, total=48960000.0),
        ]

    def test_import_purchase_list(self):
        batch = self._batch("purchase", self._portal_list(self._three_purchase_rows()))
        self.assertEqual(len(batch.row_ids), 3)
        self.assertEqual(batch.row_ids[0].col_symbol, "C26TAA")
        self.assertEqual(batch.row_ids[0].col_number, "21013")
        self.assertEqual(batch.date_from, fields.Date.to_date("2026-10-01"))
        self.assertEqual(batch.date_to, fields.Date.to_date("2026-10-31"))
        self.assertEqual(batch.name, "Purchases 01/10/2026 – 31/10/2026")
        self.assertEqual(batch.filename, "list.xlsx")
        self.assertTrue(batch.import_date)

        invoices = batch.invoice_ids
        self.assertEqual(len(invoices), 3)
        by_name = {invoice.name: invoice for invoice in invoices}
        first = by_name["C26TAA-21013"]
        self.assertEqual((first.seller_vat, first.form), ("0314071202", "1"))
        self.assertEqual(first.invoice_date, fields.Date.to_date("2026-10-01"))
        self.assertEqual(
            (first.amount_untaxed, first.amount_tax, first.amount_total),
            (5411000, 432880, 5843880),
        )
        self.assertEqual(first.status_kind, "new")
        sales_invoice = by_name["C26TMX-41"]
        self.assertEqual(sales_invoice.amount_untaxed, 48960000)
        self.assertEqual(sales_invoice.amount_tax, 0)

    def test_file_not_kept(self):
        batch = self._batch("purchase", self._portal_list(self._three_purchase_rows()))
        attachments = self.env["ir.attachment"].search(
            [("res_model", "in", ("l10n_vn.einvoice.batch", "l10n_vn.einvoice.batch.import"))]
        )
        self.assertFalse(attachments.filtered(lambda a: a.res_model != "l10n_vn.einvoice.batch" or a.res_id == batch.id))
        self.assertFalse(self.env["l10n_vn.einvoice.batch.import"]._fields["file"].attachment)

    def test_number_cells(self):
        row = self._row(number=25, tax=0, untaxed=5411000, total=5411000)
        batch = self._batch("purchase", self._portal_list([row]))
        self.assertEqual(batch.row_ids.col_number, "25")
        self.assertEqual(batch.row_ids.col_untaxed, "5411000")
        self.assertFalse(batch.row_ids.col_tax)
        invoice = batch.invoice_ids
        self.assertEqual(invoice.number, "25")
        self.assertEqual(invoice.amount_untaxed, 5411000)
        self.assertEqual(invoice.amount_tax, 0)

    def test_reimport_replaces(self):
        batch = self._batch("purchase", self._portal_list(self._three_purchase_rows()))
        old_invoices = batch.invoice_ids
        self._import(batch, self._portal_list(self._three_purchase_rows()[:2]))
        self.assertEqual(len(batch.row_ids), 2)
        self.assertEqual(len(batch.invoice_ids), 2)
        self.assertFalse(old_invoices.exists())

    def test_several_rows_grouped(self):
        rows = [
            self._row(stt=1.0, untaxed=1000000.0, tax=50000.0, total=1050000.0),
            self._row(stt=2.0, untaxed=2000000.0, tax=200000.0, total=2200000.0),
        ]
        batch = self._batch("purchase", self._portal_list(rows))
        invoice = batch.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.row_count, 2)
        self.assertEqual(
            (invoice.amount_untaxed, invoice.amount_tax, invoice.amount_total), (0, 0, 0)
        )
        self.assertFalse(invoice.rows_disagree)

        rows[1]["status"] = "Hóa đơn đã bị thay thế"
        batch = self._batch("purchase", self._portal_list(rows))
        self.assertTrue(batch.invoice_ids.rows_disagree)

    def test_status_kinds(self):
        statuses = {
            "Hóa đơn mới": "new",
            "Hóa đơn thay thế": "replacing",
            "Hóa đơn điều chỉnh": "adjusting",
            "Hóa đơn đã bị thay thế": "replaced",
            "Hóa đơn đã bị điều chỉnh": "adjusted",
            "Hóa đơn đã bị hủy": "cancelled",
            "Trạng thái lạ": "unknown",
        }
        rows = [
            self._row(stt=float(index), number=str(index), status=status)
            for index, status in enumerate(statuses, start=1)
        ]
        rows.append(
            self._row(stt=99.0, number="99",
                      status=unicodedata.normalize("NFD", "Hóa đơn đã bị điều chỉnh"))
        )
        batch = self._batch("purchase", self._portal_list(rows))
        kinds = {invoice.number: invoice.status_kind for invoice in batch.invoice_ids}
        for index, expected in enumerate(statuses.values(), start=1):
            self.assertEqual(kinds[str(index)], expected)
        self.assertEqual(kinds["99"], "adjusted")

    def test_key_error_kept(self):
        rows = [self._row(stt=1.0, number=None), self._row(stt=2.0, number="7")]
        batch = self._batch("purchase", self._portal_list(rows))
        self.assertEqual(len(batch.row_ids), 2)
        failed = batch.row_ids.filtered("error")
        self.assertEqual(failed.error, "No number.")
        self.assertFalse(failed.invoice_id)
        self.assertEqual(batch.error_count, 1)
        self.assertEqual(len(batch.invoice_ids), 1)

    def test_wrong_company_refused(self):
        batch = self._new_batch("purchase")
        content = self._portal_list([self._row(buyer_vat="0100000001")])
        with self.assertRaisesRegex(UserError, "0100000001"), self.cr.savepoint():
            self._import(batch, content)
        batch.invalidate_recordset()
        self.assertFalse(batch.row_ids)

        batch = self._new_batch("sale")
        content = self._portal_list([self._row(seller_vat="0100000001", buyer_vat=None)])
        with self.assertRaisesRegex(UserError, "0100000001"), self.cr.savepoint():
            self._import(batch, content)

    def test_sales_list(self):
        rows = [
            self._row(stt=1.0, symbol="C26TQP", number="2001", seller_vat=COMPANY_VAT,
                      buyer_vat=None, buyer_name="Khách lẻ"),
            self._row(stt=2.0, symbol="C26TQP", number="2002", seller_vat=COMPANY_VAT,
                      buyer_vat="091185007544", buyer_name="Người mua Thử"),
        ]
        batch = self._batch("sale", self._portal_list(rows))
        by_number = {invoice.number: invoice for invoice in batch.invoice_ids}
        self.assertFalse(by_number["2001"].buyer_vat)
        self.assertEqual(by_number["2002"].buyer_vat, "091185007544")
        self.assertEqual(batch.name, "Sales 01/10/2026 – 31/10/2026")

    def test_header_mismatch_refused(self):
        content = self._portal_list([self._row()], headers={"status": "Trạng thái"})
        batch = self._new_batch("purchase")
        with self.assertRaisesRegex(UserError, "R6"), self.cr.savepoint():
            self._import(batch, content)

    def test_cash_register_list(self):
        rows = [
            self._row(stt=1.0, symbol="C26MYY", number="00029704", seller_vat="0101243150",
                      seller_address="Cửa hàng Thử", untaxed=795000.0, tax=0.0, total=795000.0),
            self._row(stt=2.0, symbol="C26MYY", number="00056822", seller_vat="0101243150",
                      seller_address="Cửa hàng Thử", untaxed=124900.0, tax=0.0, total=124900.0),
        ]
        batch = self._batch("purchase", self._portal_list(rows, kind="cash_register"),
                            kind="cash_register")
        self.assertEqual(batch.template_id, self.env.ref(
            "l10n_vn_einvoice_reconcile.xlsx_template_cash_register_list"))
        self.assertEqual(batch.row_ids[0].col_seller_address, "Cửa hàng Thử")
        self.assertEqual(len(batch.invoice_ids), 2)
        self.assertEqual(
            set(batch.invoice_ids.mapped("number")), {"29704", "56822"}
        )
        self.assertEqual(batch.invoice_ids[0].currency_id, self.company.currency_id)
        self.assertIn("cash register", batch.name)

    def test_layout_title_refused(self):
        batch = self._new_batch("purchase", "ordinary")
        content = self._portal_list([self._row()], kind="cash_register")
        with self.assertRaisesRegex(UserError, "cash-register list"), self.cr.savepoint():
            self._import(batch, content)

        batch = self._new_batch("purchase", "cash_register")
        content = self._portal_list([self._row()], kind="ordinary")
        with self.assertRaisesRegex(UserError, "not the cash-register list"), self.cr.savepoint():
            self._import(batch, content)

    def test_access(self):
        def user(login, group):
            return new_test_user(
                self.env,
                login=login,
                groups=f"base.group_user,{group}",
                company_id=self.company.id,
                company_ids=[Command.set(self.company.ids)],
            )

        reader = user("portal_list_reader", "account.group_account_readonly")
        accountant = user("portal_list_accountant", "account.group_account_user")
        manager = user("portal_list_manager", "account.group_account_manager")

        # Positive control: an accountant imports (D14).
        batch = self._new_batch("purchase", "cash_register", user=accountant)
        self._import(batch, self._portal_list([self._row(citizen_id="012345678901")],
                                              kind="cash_register"))
        self.assertEqual(len(batch.invoice_ids), 1)
        self.assertEqual(batch.row_ids.col_citizen_id, "012345678901")
        with self.assertRaises(AccessError):
            batch.unlink()

        as_reader = batch.with_user(reader)
        self.assertEqual(as_reader.invoice_ids.read(["name"])[0]["name"], "C26TAA-100")
        self.assertTrue(as_reader.row_ids.read(["col_number"]))
        with self.assertRaises(AccessError):
            self.env["l10n_vn.einvoice.batch"].with_user(reader).create({"direction": "purchase"})

        batch.with_user(manager).unlink()
        self.assertFalse(batch.exists())
