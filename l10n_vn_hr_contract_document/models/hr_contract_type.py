# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

DOCUMENT_KINDS = [
    ("labour", "Labour contract"),
    ("probation", "Probation contract"),
    ("training", "Training contract"),
    ("none", "No document"),
]
# kinds that print a form
FORM_KINDS = ("labour", "probation", "training")


class HrContractType(models.Model):
    _inherit = "hr.contract.type"

    l10n_vn_document_kind = fields.Selection(
        DOCUMENT_KINDS,
        string="Contract Document",
        help="The form printed for contracts of this type.",
    )
