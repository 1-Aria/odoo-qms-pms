# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    l10n_vn_si_paid = fields.Boolean(string="Paid by social insurance")

    @api.constrains("l10n_vn_si_paid", "unpaid")
    def _check_l10n_vn_si_paid(self):
        for leave_type in self:
            if leave_type.l10n_vn_si_paid and leave_type.unpaid:
                raise ValidationError(
                    self.env._(
                        "Time off type %(name)s cannot be both unpaid and paid by social "
                        "insurance.",
                        name=leave_type.name,
                    )
                )
