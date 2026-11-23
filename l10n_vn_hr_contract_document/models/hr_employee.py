# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_vn_id_issue_date = fields.Date(
        string="ID Issue Date", groups="hr.group_hr_user", tracking=True
    )
    l10n_vn_id_issue_place = fields.Char(
        string="ID Issued By",
        help="The issuing authority as printed on the card.",
        groups="hr.group_hr_user",
        tracking=True,
    )
    l10n_vn_permanent_address = fields.Char(
        string="Permanent Address",
        help="Nơi thường trú, as on the ID card or the residence record.",
        groups="hr.group_hr_user",
        tracking=True,
    )
