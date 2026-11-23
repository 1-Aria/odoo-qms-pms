# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_vn_legal_rep_id = fields.Many2one(
        "res.partner",
        string="Legal Representative",
        help="The person who signs labour contracts for the company.",
    )
    l10n_vn_legal_rep_title = fields.Char(
        string="Representative's Title",
        help="As printed under the signature, e.g. Giám đốc.",
    )
    # step 2 (D23, D27)
    l10n_vn_contract_code = fields.Char(
        string="Contract Number Code",
        help="Added at the end of contract numbers, e.g. QP in 0012/2026/HĐLĐ-QP.",
    )
    l10n_vn_contract_approval = fields.Boolean(
        string="Contracts Run Only When Approved",
        help="A contract becomes Running only through approval of its contract document.",
    )
