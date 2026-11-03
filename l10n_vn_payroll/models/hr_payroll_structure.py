# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    l10n_vn_payroll = fields.Boolean(
        string="Vietnamese Pay Context",
        help="Payslips of this structure are calculated by the Vietnamese pay context: "
        "the latest contract of the month, the monthly input, one Pay Component rule "
        "per component.",
    )
