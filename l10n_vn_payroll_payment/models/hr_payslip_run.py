# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError

from odoo.addons.l10n_vn_payroll.models.hr_payslip_run import APPROVER


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

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
        return super().action_l10n_vn_approve()
