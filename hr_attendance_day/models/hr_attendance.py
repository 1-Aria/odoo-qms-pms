# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    correction_reason = fields.Char(
        help="Why this attendance was added or changed by hand. "
        "Payroll lists corrected days for review.",
    )
