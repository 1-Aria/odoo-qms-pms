# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_vn_payroll.models.hr_payslip_run import APPROVER, OFFICER


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    l10n_vn_payment_ids = fields.One2many(
        "l10n_vn.payroll.payment", "run_id", string="Payment List", readonly=True
    )

    def _l10n_vn_check_advances(self):
        """Refuses runs whose payslips would now settle other advances (D8)."""
        changed = self.env["hr.employee"]
        for run in self.filtered(lambda r: r.l10n_vn_period_id and r.state == "reviewed"):
            for payslip in run.slip_ids.filtered("l10n_vn_context"):
                context = payslip.l10n_vn_context
                snapshot = [
                    (advance["id"], advance["settled"])
                    for advance in context.get("advances", [])
                    if advance.get("settled")
                ]
                left = max(context.get("net", 0), 0)
                now = []
                for advance in payslip._l10n_vn_advances():
                    settled = min(advance["amount"], left)
                    left -= settled
                    if settled:
                        now.append((advance["id"], settled))
                if snapshot != now:
                    changed |= payslip.employee_id
        if changed:
            raise UserError(
                self.env._(
                    "The advances of %(employees)s changed after the run was calculated; "
                    "calculate it again.",
                    employees=", ".join(changed.mapped("name")[:3]),
                )
            )

    def action_l10n_vn_approve(self):
        self._l10n_vn_require(APPROVER)
        self.sudo()._l10n_vn_check_advances()
        result = super().action_l10n_vn_approve()
        # the run's payment list (step 2, D20)
        Payment = self.env["l10n_vn.payroll.payment"]
        for run in self.sudo():
            if run.state == "approved" and not run.l10n_vn_payment_ids:
                Payment._l10n_vn_from_run(run)
        return result

    def action_l10n_vn_mark_paid(self):
        """A run with a payment list is paid through it: the lines still to pay, dated today."""
        listed = self.filtered(lambda run: run.sudo().l10n_vn_payment_ids)
        if listed:
            self._l10n_vn_require(OFFICER)
            if any(run.sudo().state != "approved" for run in listed):
                raise UserError(self.env._("Only an approved run is marked as paid."))
            lines = listed.sudo().l10n_vn_payment_ids.line_ids.filtered(
                lambda line: line.state == "to_pay"
            )
            # as the user, so the payment's own group check applies (D25)
            self.env["l10n_vn.payroll.payment.line"].browse(lines.ids)._l10n_vn_mark_paid(
                fields.Date.context_today(self)
            )
            listed.sudo().l10n_vn_payment_ids._l10n_vn_after_paid()
        rest = self - listed
        return super(HrPayslipRun, rest).action_l10n_vn_mark_paid() if rest else True

    def action_open_l10n_vn_payment(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_vn.payroll.payment",
            "res_id": self.l10n_vn_payment_ids[:1].id,
            "view_mode": "form",
        }
