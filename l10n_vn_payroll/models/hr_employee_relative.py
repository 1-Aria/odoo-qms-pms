# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

PAYROLL_GROUPS = "payroll.group_payroll_user"


class HrEmployeeRelative(models.Model):
    _inherit = "hr.employee.relative"

    l10n_vn_pit_dependent = fields.Boolean(string="PIT Dependent", groups=PAYROLL_GROUPS)
    l10n_vn_tax_code = fields.Char(string="Dependent Tax Code", groups=PAYROLL_GROUPS)
    l10n_vn_from = fields.Date(string="Registered From", groups=PAYROLL_GROUPS)
    l10n_vn_to = fields.Date(string="Registered To", groups=PAYROLL_GROUPS)
    l10n_vn_document_ref = fields.Char(string="Registration Document", groups=PAYROLL_GROUPS)
    l10n_vn_document = fields.Binary(
        string="Document File", attachment=True, groups=PAYROLL_GROUPS
    )
    l10n_vn_document_name = fields.Char(groups=PAYROLL_GROUPS)

    @api.constrains("l10n_vn_pit_dependent", "l10n_vn_from", "l10n_vn_to")
    def _check_l10n_vn_dependent(self):
        _ = self.env._
        for relative in self.sudo():
            if relative.l10n_vn_pit_dependent and not relative.l10n_vn_from:
                raise ValidationError(
                    _("Dependent %(name)s needs the month it is registered from.", name=relative.name)
                )
            for date in (relative.l10n_vn_from, relative.l10n_vn_to):
                if date and date.day != 1:
                    raise ValidationError(
                        _(
                            "Dependent %(name)s: registration dates are first days of months.",
                            name=relative.name,
                        )
                    )
            if (
                relative.l10n_vn_from
                and relative.l10n_vn_to
                and relative.l10n_vn_to < relative.l10n_vn_from
            ):
                raise ValidationError(
                    _("Dependent %(name)s: registered to before registered from.", name=relative.name)
                )

    def _l10n_vn_counts_in(self, month_start):
        self.ensure_one()
        return bool(
            self.l10n_vn_pit_dependent
            and self.l10n_vn_from
            and self.l10n_vn_from <= month_start
            and (not self.l10n_vn_to or self.l10n_vn_to >= month_start)
        )
