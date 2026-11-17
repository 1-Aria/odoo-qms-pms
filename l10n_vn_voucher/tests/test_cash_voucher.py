# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

ACTION_IN = "l10n_vn_voucher.action_report_cash_in"
ACTION_OUT = "l10n_vn_voucher.action_report_cash_out"


@tagged("post_install", "-at_install")
class TestCashVoucher(TransactionCase):
    """Built on TransactionCase, not on account's AccountTestInvoicingCommon,
    whose package cannot be imported on this image."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Cash Voucher Test Company",
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
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.cash = cls.journal.default_account_id
        prefix = f"account.{cls.company.id}_"
        cls.payable = cls.env.ref(prefix + "chart3311")
        cls.receivable = cls.env.ref(prefix + "chart1311")
        cls.expense = cls.env.ref(prefix + "chart632")
        cls.partner_a = cls.env["res.partner"].create(
            {
                "name": "Nhà cung cấp A",
                "street": "12 Lê Lợi",
                "city": "Hồ Chí Minh",
                "country_id": cls.env.ref("base.vn").id,
            }
        )
        cls.partner_b = cls.env["res.partner"].create({"name": "Nhà cung cấp B"})
        cls.invoicing_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Cash Voucher User",
                    "login": "l10n_vn_voucher_cash_user",
                    "company_id": cls.company.id,
                    "company_ids": [Command.set(cls.company.ids)],
                    "groups_id": [
                        Command.set([cls.env.ref("account.group_account_invoice").id])
                    ],
                }
            )
        )

    def _entry(self, lines, entry_date=date(2026, 11, 10), journal=None, env=None, **values):
        """A posted entry in the cash journal from (account, debit, credit, partner)."""
        env = env or self.env
        journal = journal or self.journal
        vals = {
            "move_type": "entry",
            "journal_id": journal.id,
            "date": entry_date,
            "line_ids": [
                Command.create(
                    {
                        "name": "Test line",
                        "account_id": account.id,
                        "debit": debit,
                        "credit": credit,
                        "partner_id": partner.id if partner else False,
                    }
                )
                for account, debit, credit, partner in lines
            ],
        }
        vals.update(values)
        move = env["account.move"].create(vals)
        move.action_post()
        return move

    def _payment(self, amount=1_000_000, **values):
        return self._entry(
            [(self.payable, amount, 0, self.partner_a), (self.cash, 0, amount, None)], **values
        )

    def _receipt(self, amount=1_000_000, **values):
        return self._entry(
            [(self.cash, amount, 0, None), (self.receivable, 0, amount, self.partner_a)],
            **values,
        )

    def _html(self, move, action, env=None):
        reports = (env or self.env)["ir.actions.report"]
        html, _type = reports._render_qweb_html(action, move.ids)
        return html.decode()

    def test_cash_out_series(self):
        first, second = self._payment(), self._payment()
        self.assertEqual(first.l10n_vn_voucher_kind, "cash_out")
        self.assertEqual(first.l10n_vn_voucher_number, "PC/2026/0001")
        self.assertEqual(second.l10n_vn_voucher_number, "PC/2026/0002")
        receipt = self._receipt()
        self.assertEqual(receipt.l10n_vn_voucher_kind, "cash_in")
        self.assertEqual(receipt.l10n_vn_voucher_number, "PT/2026/0001")

    def test_new_year(self):
        self._payment()
        payment = self._payment(entry_date=date(2027, 1, 5))
        self.assertEqual(payment.l10n_vn_voucher_number, "PC/2027/0001")

    def test_no_voucher(self):
        mixed = self._entry(
            [
                (self.cash, 500, 0, None),
                (self.cash, 0, 300, None),
                (self.receivable, 0, 200, self.partner_a),
            ]
        )
        untouched = self._entry(
            [(self.expense, 100, 0, None), (self.payable, 0, 100, self.partner_a)]
        )
        for move in (mixed, untouched):
            self.assertFalse(move.l10n_vn_voucher_kind)
            self.assertFalse(move.l10n_vn_voucher_number)
            with self.assertRaises(UserError):
                move._l10n_vn_cash_voucher_data()

    def test_repost(self):
        payment = self._payment()
        number = payment.l10n_vn_voucher_number
        payment.button_draft()
        payment.action_post()
        self.assertEqual(payment.l10n_vn_voucher_number, number)

        payment.button_draft()
        payment.write(
            {
                "line_ids": [Command.delete(line.id) for line in payment.line_ids]
                + [
                    Command.create(
                        {"account_id": self.cash.id, "debit": 1_000_000, "credit": 0}
                    ),
                    Command.create(
                        {
                            "account_id": self.receivable.id,
                            "debit": 0,
                            "credit": 1_000_000,
                            "partner_id": self.partner_a.id,
                        }
                    ),
                ]
            }
        )
        payment.action_post()
        self.assertEqual(payment.l10n_vn_voucher_kind, "cash_in")
        self.assertEqual(payment.l10n_vn_voucher_number, "PT/2026/0001")
        # The payment number it held is not reused.
        self.assertEqual(self._payment().l10n_vn_voucher_number, "PC/2026/0002")

    def test_person(self):
        payment = self._payment()
        data = payment._l10n_vn_cash_voucher_data()
        self.assertEqual(data["person"], self.partner_a.name)
        self.assertEqual(
            data["address"],
            self.env["l10n_vn.voucher"]._address(self.partner_a.with_context(lang="vi_VN")),
        )

        two = self._entry(
            [
                (self.payable, 600, 0, self.partner_a),
                (self.payable, 400, 0, self.partner_b),
                (self.cash, 0, 1000, None),
            ]
        )
        self.assertEqual(two._l10n_vn_cash_voucher_data()["person"], "")

        payment.write({"l10n_vn_voucher_person": "Anh Tư", "l10n_vn_voucher_address": "Kho Chi Lăng"})
        data = payment._l10n_vn_cash_voucher_data()
        self.assertEqual(data["person"], "Anh Tư")
        self.assertEqual(data["address"], "Kho Chi Lăng")

    def test_accounts(self):
        data = self._payment()._l10n_vn_cash_voucher_data()
        self.assertEqual(data["debit_accounts"], [self.payable.code])
        self.assertEqual(data["credit_accounts"], [self.cash.code])

        split = self._entry(
            [
                (self.payable, 600_000, 0, self.partner_a),
                (self.expense, 400_000, 0, None),
                (self.cash, 0, 1_000_000, None),
            ]
        )
        data = split._l10n_vn_cash_voucher_data()
        self.assertEqual(
            data["debit_accounts"],
            sorted(["%s: 600.000" % self.payable.code, "%s: 400.000" % self.expense.code]),
        )
        self.assertEqual(data["credit_accounts"], [self.cash.code])

    def test_render_cash_in(self):
        self.journal.l10n_vn_cash_in_copies = (
            "Liên 1: Lưu tại nơi lập phiếu\n"
            "Liên 2: Thủ quỹ giữ để ghi sổ quỹ\n"
            "Liên 3: Giao cho người nộp tiền"
        )
        receipt = self._receipt()
        html = self._html(receipt, ACTION_IN)
        for text in (
            "PHIẾU THU",
            "Mẫu số",
            "01-TT",
            receipt.l10n_vn_voucher_number,
            "Quyển số",
            self.journal.name,
            "Một triệu đồng",
            "Người nộp tiền",
            "Thủ quỹ",
            "Đã nhận đủ số tiền",
        ):
            self.assertIn(text, html)
        for label in (
            "Liên 1: Lưu tại nơi lập phiếu",
            "Liên 2: Thủ quỹ giữ để ghi sổ quỹ",
            "Liên 3: Giao cho người nộp tiền",
        ):
            self.assertEqual(html.count(label), 1, label)
        self.assertEqual(html.count("page-break-before"), 2)

    def test_report_domains(self):
        actions = self.env.ref(ACTION_IN) | self.env.ref(ACTION_OUT)

        def valid(move):
            return set(actions.get_valid_action_reports("account.move", move.ids))

        self.assertEqual(valid(self._receipt()), {self.env.ref(ACTION_IN).id})
        payment = self._payment()
        self.assertEqual(valid(payment), {self.env.ref(ACTION_OUT).id})
        payment.button_draft()
        self.assertEqual(valid(payment), set())

    def test_post_as_invoicing_user(self):
        journal = self.env["account.journal"].create(
            {"name": "Quỹ phụ test", "code": "TQP", "type": "cash", "company_id": self.company.id}
        )
        self.assertFalse(journal.l10n_vn_cash_out_sequence_id)
        user_env = self.env(
            user=self.invoicing_user,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )
        payment = self._entry(
            [
                (self.payable, 1_000_000, 0, self.partner_a),
                (journal.default_account_id, 0, 1_000_000, None),
            ],
            journal=journal,
            env=user_env,
        )
        # Positive control: the user reads the entry.
        self.assertEqual(payment.with_env(user_env).name, payment.name)
        self.assertEqual(payment.l10n_vn_voucher_number, "PC/2026/0001")
        self.assertTrue(journal.l10n_vn_cash_out_sequence_id)
        html = self._html(payment, ACTION_OUT, env=user_env)
        self.assertIn("PHIẾU CHI", html)
