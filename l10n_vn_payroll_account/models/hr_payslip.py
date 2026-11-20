# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

POSTING_KINDS = ("earning", "deduction", "employer")


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _l10n_vn_posts(self):
        """A Vietnamese payslip of a company that posts payroll, whose contract's
        participant type is posted (D5, D11)."""
        self.ensure_one()
        payslip = self.sudo()
        if not payslip.company_id.l10n_vn_payroll_post:
            return False
        participant = payslip.contract_id.l10n_vn_participant_type_id
        return self._l10n_vn_is_vn() and bool(participant.posted)

    def _l10n_vn_cost_group(self):
        """The contract's cost group, else its department's or the nearest parent's (D4)."""
        self.ensure_one()
        contract = self.sudo().contract_id
        if contract.l10n_vn_cost_group_id:
            return contract.l10n_vn_cost_group_id
        department = contract.department_id or self.sudo().employee_id.department_id
        if department:
            return department._l10n_vn_cost_group()
        return self.env["l10n_vn.payroll.cost.group"]

    def _l10n_vn_posting_lines(self):
        """The payslip's lines that post, with their component."""
        self.ensure_one()
        return self.sudo().line_ids.filtered(
            lambda line: line.l10n_vn_component_id.kind in POSTING_KINDS and line.total
        )

    def _l10n_vn_posting_problems(self):
        """What posting this payslip would lack (D8)."""
        self.ensure_one()
        payslip = self.sudo()
        company = payslip.company_id
        problems = []
        if not company.l10n_vn_payroll_journal_id:
            problems.append(self.env._("the payroll journal"))
        if not company.l10n_vn_payroll_payable_account_id:
            problems.append(self.env._("the payroll payable account"))
        components = payslip._l10n_vn_posting_lines().l10n_vn_component_id
        group = payslip._l10n_vn_cost_group()
        needs_group = any(
            c.kind == "employer" or (c.kind == "earning" and not c.l10n_vn_account_id)
            for c in components
        )
        if needs_group and not group.expense_account_id:
            department = payslip.contract_id.department_id or payslip.employee_id.department_id
            problems.append(
                self.env._(
                    "a cost group for department %(department)s",
                    department=department.display_name or self.env._("(none)"),
                )
            )
        for component in components.filtered(
            lambda c: c.kind in ("deduction", "employer") and not c.l10n_vn_account_id
        ):
            problems.append(self.env._("an account on component %(code)s", code=component.code))
        # OCA's own posting would add a second entry (D8, D9)
        for rule in payslip._get_salary_rules().filtered(
            lambda r: r.account_debit or r.account_credit
        ):
            problems.append(
                self.env._("no OCA account on salary rule %(code)s", code=rule.code)
            )
        return problems
