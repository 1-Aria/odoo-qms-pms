# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

SIGN_HINT = "(Ký, họ tên)"
DIRECTOR_HINT = "(Ký, họ tên, đóng dấu)"


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_vn_voucher_kind = fields.Selection(
        [("cash_in", "Phiếu thu"), ("cash_out", "Phiếu chi")],
        string="Cash Voucher",
        readonly=True,
        copy=False,
        index="btree_not_null",
    )
    l10n_vn_voucher_number = fields.Char(
        string="Cash Voucher Number", readonly=True, copy=False
    )
    l10n_vn_voucher_person = fields.Char(string="Người nộp / nhận tiền", copy=False)
    l10n_vn_voucher_address = fields.Char(
        string="Địa chỉ người nộp / nhận tiền", copy=False
    )
    l10n_vn_journal_type = fields.Selection(related="journal_id.type")

    _sql_constraints = [
        (
            "l10n_vn_voucher_number_uniq",
            "unique(journal_id, l10n_vn_voucher_number)",
            "A cash voucher number is used once per journal.",
        ),
    ]

    def _l10n_vn_cash_lines(self):
        """The lines on the cash journal's own account."""
        self.ensure_one()
        journal = self.journal_id
        if journal.type != "cash" or not journal.default_account_id:
            return self.env["account.move.line"]
        return self.line_ids.filtered(
            lambda line: line.account_id == journal.default_account_id
        )

    def _l10n_vn_voucher_kind_of(self):
        """cash_in when every cash line receives, cash_out when every one pays,
        False otherwise (no cash line, or both directions)."""
        self.ensure_one()
        lines = self._l10n_vn_cash_lines()
        if not lines:
            return False
        currency = self.company_currency_id
        if all(currency.compare_amounts(line.balance, 0) > 0 for line in lines):
            return "cash_in"
        if all(currency.compare_amounts(line.balance, 0) < 0 for line in lines):
            return "cash_out"
        return False

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            kind = move._l10n_vn_voucher_kind_of()
            if not kind:
                if move.l10n_vn_voucher_kind:
                    # Reposted with lines that no longer make a voucher.
                    move.l10n_vn_voucher_kind = False
                continue
            if kind == move.l10n_vn_voucher_kind and move.l10n_vn_voucher_number:
                continue
            sequence = move.journal_id._l10n_vn_voucher_sequence(kind)
            move.write(
                {
                    "l10n_vn_voucher_kind": kind,
                    "l10n_vn_voucher_number": sequence.next_by_id(sequence_date=move.date),
                }
            )
        return posted

    def _l10n_vn_voucher_partner(self):
        """The partner of the lines other than cash, when there is exactly one."""
        self.ensure_one()
        partners = (self.line_ids - self._l10n_vn_cash_lines()).partner_id
        return partners if len(partners) == 1 else self.env["res.partner"]

    def _l10n_vn_side_accounts(self, lines):
        """The accounts of one side of the entry, each code once, sorted; with
        several, each followed by its amount."""
        totals = {}
        for line in lines:
            code = line.account_id.with_company(self.company_id).code
            totals[code] = totals.get(code, 0.0) + abs(line.balance)
        codes = sorted(totals)
        if len(codes) <= 1:
            return codes
        digits = self.company_currency_id.decimal_places
        return [
            "%s: %s" % (code, formatLang(self.env, totals[code], digits=digits))
            for code in codes
        ]

    def _l10n_vn_cash_voucher_data(self):
        """Everything the Phiếu thu or Phiếu chi prints."""
        self.ensure_one()
        if self.state != "posted" or not self.l10n_vn_voucher_kind:
            raise UserError(
                _(
                    "%(entry)s is not a posted cash entry that only receives or only pays "
                    "cash; split it into one entry per direction to print a voucher.",
                    entry=self.display_name,
                )
            )
        move = self.with_context(lang="vi_VN")
        helpers = self.env["l10n_vn.voucher"]
        cash_in = move.l10n_vn_voucher_kind == "cash_in"
        cash_lines = move._l10n_vn_cash_lines()
        currency = move.company_currency_id
        amount = abs(sum(cash_lines.mapped("balance")))
        partner = move._l10n_vn_voucher_partner()
        creator = move.create_uid.name or ""
        if cash_in:
            signers = [
                {"role": "Giám đốc", "hint": DIRECTOR_HINT, "name": ""},
                {"role": "Kế toán trưởng", "hint": SIGN_HINT, "name": ""},
                {"role": "Người nộp tiền", "hint": SIGN_HINT, "name": ""},
                {"role": "Người lập phiếu", "hint": SIGN_HINT, "name": creator},
                {"role": "Thủ quỹ", "hint": SIGN_HINT, "name": ""},
            ]
        else:
            signers = [
                {"role": "Giám đốc", "hint": DIRECTOR_HINT, "name": ""},
                {"role": "Kế toán trưởng", "hint": SIGN_HINT, "name": ""},
                {"role": "Thủ quỹ", "hint": SIGN_HINT, "name": ""},
                {"role": "Người lập phiếu", "hint": SIGN_HINT, "name": creator},
                {"role": "Người nhận tiền", "hint": SIGN_HINT, "name": ""},
            ]
        return {
            "kind": move.l10n_vn_voucher_kind,
            "title": "PHIẾU THU" if cash_in else "PHIẾU CHI",
            "form_code": "01-TT" if cash_in else "02-TT",
            "company": move.company_id,
            "department": "",
            "book": move.journal_id.name,
            "number": move.l10n_vn_voucher_number,
            "date": move.date,
            "debit_accounts": move._l10n_vn_side_accounts(
                move.line_ids.filtered(lambda line: line.debit > 0)
            ),
            "credit_accounts": move._l10n_vn_side_accounts(
                move.line_ids.filtered(lambda line: line.credit > 0)
            ),
            "person_label": "Họ và tên người nộp tiền" if cash_in else "Họ và tên người nhận tiền",
            "person": move.l10n_vn_voucher_person or partner.name or "",
            "address": move.l10n_vn_voucher_address or helpers._address(partner),
            "reason_label": "Lý do nộp" if cash_in else "Lý do chi",
            "reason": move.ref or cash_lines[:1].name or "",
            "amount": amount,
            "amount_text": "%s %s"
            % (formatLang(move.env, amount, digits=currency.decimal_places), currency.name),
            "currency": currency,
            "copies": move.journal_id.l10n_vn_cash_in_copies
            if cash_in
            else move.journal_id.l10n_vn_cash_out_copies,
            "signers": signers,
        }
