# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class L10nVnPayrollCheck(models.Model):
    _inherit = "l10n_vn.payroll.check"

    def _l10n_vn_find_posting(self, payslip, context):
        """What posting would lack on a payslip that posts (D8)."""
        if not payslip._l10n_vn_posts():
            return []
        problems = payslip._l10n_vn_posting_problems()
        if not problems:
            return []
        return [
            (
                False,
                self.env._("Posting needs: %(problems)s.", problems=", ".join(problems)),
            )
        ]
