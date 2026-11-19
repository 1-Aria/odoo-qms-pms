# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

from openpyxl import load_workbook

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D

from .common import AdvanceCase


@tagged("post_install", "-at_install")
class TestPayment(AdvanceCase):
    """Payment lists (step 2): payday and advances paid the same way."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_bank = cls.env["res.partner.bank"].create(
            {"acc_number": "TEST-COMPANY-PAYING", "partner_id": cls.company.partner_id.id}
        )

    # ------------------------------------------------------------------ helpers
    def _casual(self, contract):
        contract.l10n_vn_participant_type_id = self.env.ref("l10n_vn_payroll.participant_casual")

    def _approved_run_noted(self):
        """Calculated, warnings noted, reviewed and approved."""
        run = self._new_run()
        self._calculate(run)
        run.l10n_vn_check_result_ids.filtered(
            lambda r: r.level == "warning" and not r.note
        ).write({"note": "Seen"})
        self._review(run)
        self._approve(run)
        return run

    def _line_of(self, payment, employee):
        return payment.line_ids.filtered(lambda l: l.employee_id == employee)

    # ------------------------------------------------------------------ run lists (D20)
    def test_run_list_at_approval(self):
        run = self._approved_run()
        payment = run.l10n_vn_payment_ids
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.kind, "payroll")
        self.assertEqual(payment.company_bank_id, self.company_bank)
        self.assertEqual(payment.line_ids.payslip_id, run.slip_ids)
        for line in payment.line_ids:
            self.assertEqual(line.amount, line.payslip_id.l10n_vn_to_pay)
            self.assertEqual(line.method, "transfer")
            self.assertEqual(line.bank_account_id, line.employee_id.bank_account_id)
        self.assertEqual(payment.state, "to_pay")

    def test_cash_and_nothing_to_pay(self):
        self._casual(self.bao_contract)
        # Alice's advance is above her net: nothing left to pay her
        self._paid_advance(self.alice, 5000000)
        run = self._approved_run_noted()
        self.assertEqual(self._slip(run, self.alice).l10n_vn_to_pay, 0)
        payment = run.l10n_vn_payment_ids
        self.assertEqual(payment.line_ids.employee_id, self.bao)
        self.assertEqual(payment.line_ids.method, "cash")
        self.assertFalse(payment.line_ids.bank_account_id)

    # ------------------------------------------------------------------ the transfer file (D23)
    def test_transfer_file(self):
        self._casual(self.bao_contract)
        run = self._approved_run_noted()
        payment = run.l10n_vn_payment_ids
        payment.date = D(2026, 11, 10)
        action = self._as(self.officer)["l10n_vn.payroll.payment"].browse(
            payment.id
        ).action_transfer_file()
        self.assertEqual(action["type"], "ir.actions.act_url")
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", payment._name), ("res_id", "=", payment.id)]
        )
        self.assertEqual(len(attachment), 1)
        sheet = load_workbook(io.BytesIO(base64.b64decode(attachment.datas))).active
        alice_line = self._line_of(payment, self.alice)
        self.assertEqual(sheet["A2"].value, 1)
        self.assertEqual(sheet["B2"].value, self.alice.name)
        self.assertEqual(sheet["E2"].value, "TEST-COMPANY-PAYING")
        self.assertEqual(sheet["F2"].value, self.alice.bank_account_id.acc_number)
        self.assertEqual(sheet["H2"].value, alice_line.amount)
        self.assertEqual(sheet["L2"].value, "OUR")
        value_date = sheet["M2"].value
        self.assertEqual(getattr(value_date, "date", lambda: value_date)(), D(2026, 11, 10))
        # Bao is paid in cash: not in the file
        self.assertFalse(sheet["B3"].value)

    def test_transfer_file_needs_bank(self):
        run = self._approved_run()
        payment = run.l10n_vn_payment_ids
        self._line_of(payment, self.alice).bank_account_id = False
        with self.assertRaises(UserError) as caught:
            self._as(self.officer)["l10n_vn.payroll.payment"].browse(
                payment.id
            ).action_transfer_file()
        self.assertIn(self.alice.name, str(caught.exception))

    # ------------------------------------------------------------------ paying (D25)
    def test_mark_paid_by_method(self):
        self._casual(self.bao_contract)
        run = self._approved_run_noted()
        payment = run.l10n_vn_payment_ids
        self._pay(payment, "transfer", D(2026, 12, 10))
        alice_line = self._line_of(payment, self.alice)
        self.assertEqual((alice_line.state, alice_line.paid_date), ("paid", D(2026, 12, 10)))
        self.assertEqual(self._line_of(payment, self.bao).state, "to_pay")
        self.assertEqual(payment.state, "to_pay")
        self.assertEqual(run.state, "approved")
        self._pay(payment, "cash", D(2026, 12, 11))
        self.assertEqual(payment.state, "paid")
        self.assertEqual(run.state, "paid")

    def test_returned_transfer(self):
        run = self._approved_run()
        payment = run.l10n_vn_payment_ids
        self._pay(payment, "transfer", lines=self._line_of(payment, self.alice))
        self.assertEqual(self._line_of(payment, self.bao).state, "to_pay")
        self.assertEqual(payment.state, "to_pay")
        self._pay(payment, "transfer", D(2026, 10, 20))
        self.assertEqual(self._line_of(payment, self.bao).paid_date, D(2026, 10, 20))
        self.assertEqual(payment.state, "paid")
        self.assertEqual(run.state, "paid")

    def test_run_button_pays_the_rest(self):
        run = self._approved_run()
        payment = run.l10n_vn_payment_ids
        self._pay(payment, "transfer", D(2026, 10, 20), lines=self._line_of(payment, self.alice))
        with self.assertRaises(AccessError):
            self._runs(self.reader).browse(run.id).action_l10n_vn_mark_paid()
        self._runs(self.officer).browse(run.id).action_l10n_vn_mark_paid()
        self.assertEqual(self._line_of(payment, self.alice).paid_date, D(2026, 10, 20))
        bao_line = self._line_of(payment, self.bao)
        self.assertEqual(bao_line.state, "paid")
        self.assertEqual(bao_line.paid_date, fields.Date.context_today(bao_line))
        self.assertEqual(run.state, "paid")

    # ------------------------------------------------------------------ the cash list (D24)
    def test_cash_list_report(self):
        self._casual(self.bao_contract)
        run = self._approved_run_noted()
        payment = run.l10n_vn_payment_ids
        html, _kind = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_vn_payroll_payment.action_report_l10n_vn_cash_list", payment.ids
        )
        html = html.decode()
        lang = self.env["res.lang"]._lang_get(self.env.lang or "en_US")
        bao_line = self._line_of(payment, self.bao)
        self.assertIn("DANH SÁCH CHI LƯƠNG BẰNG TIỀN MẶT", html)
        self.assertIn(self.bao.name, html)
        self.assertIn(lang.format("%.0f", bao_line.amount, grouping=True), html)
        self.assertNotIn(self.alice.name, html)

    # ------------------------------------------------------------------ advances (D21, D26)
    def test_advance_list(self):
        batch = self.env["l10n_vn.payroll.advance.batch"].create(
            {"company_id": self.company.id, "date": D(2026, 10, 16), "reason": "Test batch"}
        )
        advances = self._advance(
            self.alice, 1000000, state="approved", batch_id=batch.id
        ) | self._advance(self.bao, 500000, state="approved", batch_id=batch.id)
        Batch = self._as(self.officer)["l10n_vn.payroll.advance.batch"]
        action = Batch.browse(batch.id).action_create_payment()
        payment = self.env["l10n_vn.payroll.payment"].browse(action["res_id"])
        self.assertEqual(payment.kind, "advance")
        self.assertEqual(payment.line_ids.advance_id, advances)
        self.assertEqual(payment.amount_total, 1500000)
        with self.assertRaises(UserError):
            Batch.browse(batch.id).action_create_payment()
        self._pay(payment, "transfer", D(2026, 10, 16))
        self.assertEqual(set(advances.mapped("state")), {"paid"})
        self.assertEqual(set(advances.mapped("paid_date")), {D(2026, 10, 16)})
        self.assertEqual(batch.state, "paid")
        self.assertEqual(payment.state, "paid")

    def test_cancel_removes_line(self):
        advance = self._advance(self.alice, 1000000, state="approved")
        Advances = self._advances(self.officer)
        action = Advances.browse(advance.id).action_create_payment()
        payment = self.env["l10n_vn.payroll.payment"].browse(action["res_id"])
        self.assertTrue(payment.line_ids)
        Advances.browse(advance.id).action_cancel()
        self.assertFalse(payment.line_ids)
        self.assertEqual(advance.state, "cancelled")

    # ------------------------------------------------------------------ roles and deleting
    def test_roles(self):
        run = self._approved_run()
        payment = run.l10n_vn_payment_ids
        as_reader = self._as(self.reader)["l10n_vn.payroll.payment"].browse(payment.id)
        self.assertEqual(as_reader.amount_total, payment.amount_total)
        with self.assertRaises(AccessError):
            as_reader.action_open_pay_transfer()
        self._pay(payment, "transfer")
        self.assertEqual(payment.state, "paid")

    def test_unlink(self):
        advance = self._advance(self.alice, 1000000, state="approved")
        Advances = self._advances(self.officer)
        Payments = self._as(self.officer)["l10n_vn.payroll.payment"]
        first = Advances.browse(advance.id).action_create_payment()
        Payments.browse(first["res_id"]).unlink()
        self.assertFalse(advance.payment_line_ids)
        second = Payments.browse(Advances.browse(advance.id).action_create_payment()["res_id"])
        self._pay(second, "transfer")
        with self.assertRaises(UserError):
            Payments.browse(second.id).unlink()
        run = self._approved_run()
        with self.assertRaises(UserError):
            Payments.browse(run.l10n_vn_payment_ids.id).unlink()
