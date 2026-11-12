# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrContractType(models.Model):
    _inherit = "hr.contract.type"

    l10n_vn_participant_type_id = fields.Many2one(
        "l10n_vn.payroll.participant.type",
        string="Payroll Participant Type",
        ondelete="restrict",
        groups="payroll.group_payroll_user",
        help="Given to a new contract of this type (D103).",
    )
