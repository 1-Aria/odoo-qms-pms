# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models
from odoo.exceptions import UserError


class L10nVnPayrollPayment(models.Model):
    _inherit = "l10n_vn.payroll.payment"

    l10n_vn_move_ids = fields.Many2many(
        "account.move", string="Journal Entries", compute="_compute_l10n_vn_move_ids"
    )

    def _compute_l10n_vn_move_ids(self):
        for payment in self:
            payment.l10n_vn_move_ids = payment.line_ids.l10n_vn_move_id


class L10nVnPayrollPaymentLine(models.Model):
    _inherit = "l10n_vn.payroll.payment.line"

    l10n_vn_move_id = fields.Many2one(
        "account.move", string="Journal Entry", readonly=True, copy=False
    )

    def _l10n_vn_posts(self):
        """The participant type of the contract behind the line is posted (D5)."""
        self.ensure_one()
        line = self.sudo()
        if not line.payment_id.company_id.l10n_vn_payroll_post:
            return False
        if line.payslip_id:
            contract = line.payslip_id.contract_id
        else:
            advance = line.advance_id
            contract = advance._l10n_vn_month_contract(advance.employee_id, advance.date)
        return bool(contract.l10n_vn_participant_type_id.posted)

    def _l10n_vn_mark_paid(self, paid_date):
        result = super()._l10n_vn_mark_paid(paid_date)
        self._l10n_vn_post_payment(paid_date)
        return result

    def _l10n_vn_post_payment(self, paid_date):
        """One entry per list and method: 3341 per employee against the outstanding account (D6)."""
        lines = self.sudo().filtered(lambda line: line._l10n_vn_posts())
        Move = self.env["account.move"].sudo()
        groups = {}
        for line in lines:
            groups.setdefault((line.payment_id, line.method), self.browse().sudo())
            groups[(line.payment_id, line.method)] |= line
        for (payment, method), group in groups.items():
            company = payment.company_id
            if method == "transfer":
                journal = company.l10n_vn_payroll_bank_journal_id
                kind = self.env._("bank")
            else:
                journal = company.l10n_vn_payroll_cash_journal_id
                kind = self.env._("cash")
            if not journal:
                raise UserError(
                    self.env._("Set the payroll %(kind)s journal in Payroll settings.", kind=kind)
                )
            outstanding = journal.outbound_payment_method_line_ids.filtered(
                "payment_account_id"
            )[:1].payment_account_id
            if not outstanding:
                raise UserError(
                    self.env._(
                        "Journal %(journal)s has no outstanding payments account.",
                        journal=journal.display_name,
                    )
                )
            payable = company.l10n_vn_payroll_payable_account_id
            if not payable:
                raise UserError(self.env._("Set the payroll payable account in Payroll settings."))
            vals = [
                Command.create(
                    {
                        "account_id": payable.id,
                        "partner_id": line.employee_id.work_contact_id.id,
                        "name": f"{line.employee_id.name}, {payment.name}",
                        "debit": line.amount,
                        "credit": 0.0,
                    }
                )
                for line in group
            ]
            vals.append(
                Command.create(
                    {
                        "account_id": outstanding.id,
                        "name": payment.name,
                        "debit": 0.0,
                        "credit": sum(group.mapped("amount")),
                    }
                )
            )
            move = Move.create(
                {
                    "move_type": "entry",
                    "journal_id": journal.id,
                    "date": paid_date,
                    "ref": payment.name,
                    "company_id": company.id,
                    "l10n_vn_payroll_payment_id": payment.id,
                    "line_ids": vals,
                }
            )
            move.action_post()
            group.write({"l10n_vn_move_id": move.id})
            self.env["account.move.line"]._l10n_vn_payroll_reconcile(
                company, group.employee_id.work_contact_id
            )
