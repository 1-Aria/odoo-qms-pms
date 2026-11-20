# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    l10n_vn_move_id = fields.Many2one(
        "account.move", string="Journal Entry", readonly=True, copy=False
    )

    # ------------------------------------------------------------------ the journal (divergence 3)
    @api.model_create_multi
    def create(self, vals_list):
        Period = self.env["l10n_vn.payroll.period"].sudo()
        for vals in vals_list:
            if vals.get("l10n_vn_period_id") and not vals.get("journal_id"):
                journal = Period.browse(vals["l10n_vn_period_id"]).company_id.l10n_vn_payroll_journal_id
                if journal:
                    vals["journal_id"] = journal.id
        return super().create(vals_list)

    @api.onchange("l10n_vn_period_id")
    def _onchange_l10n_vn_period_journal(self):
        journal = self.l10n_vn_period_id.company_id.l10n_vn_payroll_journal_id
        if journal:
            self.journal_id = journal

    # ------------------------------------------------------------------ the entry (D3)
    def action_l10n_vn_approve(self):
        result = super().action_l10n_vn_approve()
        self._l10n_vn_post()
        return result

    def _l10n_vn_entry_lines(self):
        """The run entry's line values (D2, D3)."""
        self.ensure_one()
        run = self.sudo()
        company = run.company_id
        currency = company.currency_id
        payable = company.l10n_vn_payroll_payable_account_id
        month = f"{run.l10n_vn_period_id.date_from:%m/%Y}"
        expenses = defaultdict(float)  # (account, cost group) -> debit
        credits = defaultdict(float)  # (account, partner) -> credit
        gross_lines, deduction_lines = [], []
        slips = run.slip_ids.filtered(lambda s: s._l10n_vn_posts()).sorted(
            lambda s: (s.employee_id.name or "", s.id)
        )
        for slip in slips:
            problems = slip._l10n_vn_posting_problems()
            if problems:
                raise UserError(
                    self.env._(
                        "Posting the payslip of %(employee)s needs: %(problems)s.",
                        employee=slip.employee_id.name,
                        problems=", ".join(problems),
                    )
                )
            partner = slip.employee_id.work_contact_id
            group = slip._l10n_vn_cost_group()
            gross = 0.0
            by_component = defaultdict(float)
            for line in slip._l10n_vn_posting_lines():
                by_component[line.l10n_vn_component_id] += line.total
            for component, amount in by_component.items():
                register_partner = component.register_id.partner_id
                if component.kind == "earning":
                    account = component.l10n_vn_account_id or group.expense_account_id
                    expenses[(account, group)] += amount
                    gross += amount
                elif component.kind == "deduction":
                    # deductions are negative on the payslip
                    deduction_lines.append((partner, slip.employee_id, component, -amount))
                    credits[(component.l10n_vn_account_id, register_partner)] += -amount
                else:
                    expenses[(group.expense_account_id, group)] += amount
                    credits[(component.l10n_vn_account_id, register_partner)] += amount
            if not currency.is_zero(gross):
                gross_lines.append((partner, slip.employee_id, gross))

        def line(account, debit, name, partner=None):
            debit = currency.round(debit)
            return {
                "account_id": account.id,
                "partner_id": partner.id if partner else False,
                "name": name,
                "debit": debit if debit > 0 else 0.0,
                "credit": -debit if debit < 0 else 0.0,
            }

        vals = []
        for (account, group), amount in expenses.items():
            if not currency.is_zero(amount):
                vals.append(line(account, amount, f"{group.name or account.name} {month}"))
        for partner, employee, amount in gross_lines:
            vals.append(
                line(payable, -amount, self.env._("%(employee)s, pay %(month)s",
                                                  employee=employee.name, month=month), partner)
            )
        for partner, employee, component, amount in deduction_lines:
            vals.append(line(payable, amount, f"{employee.name}, {component.name}", partner))
        for (account, register_partner), amount in credits.items():
            if not currency.is_zero(amount):
                vals.append(line(account, -amount, f"{account.name} {month}", register_partner))
        return vals

    def _l10n_vn_post(self):
        """Posts each approved run's entry and reconciles its employees' 3341 (D3, D7)."""
        Move = self.env["account.move"].sudo()
        for run in self.sudo().filtered(
            lambda r: r.l10n_vn_period_id and r.state == "approved" and not r.l10n_vn_move_id
        ):
            vals = run._l10n_vn_entry_lines()
            if not vals:
                continue
            company = run.company_id
            move = Move.create(
                {
                    "move_type": "entry",
                    "journal_id": company.l10n_vn_payroll_journal_id.id,
                    "date": run.l10n_vn_period_id.date_to,
                    "ref": run.name,
                    "company_id": company.id,
                    "l10n_vn_payroll_run_id": run.id,
                    "line_ids": [Command.create(v) for v in vals],
                }
            )
            move.action_post()
            run.l10n_vn_move_id = move
            partners = move.line_ids.filtered(
                lambda l: l.account_id == company.l10n_vn_payroll_payable_account_id
            ).partner_id
            self.env["account.move.line"]._l10n_vn_payroll_reconcile(company, partners)

    def action_open_l10n_vn_move(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.l10n_vn_move_id.id,
            "view_mode": "form",
        }
