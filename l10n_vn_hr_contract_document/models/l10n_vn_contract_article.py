# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnContractArticle(models.Model):
    """An extra article of one form, on the company's wording record (D15)."""

    _name = "l10n_vn.contract.article"
    _description = "Contract Article"
    _order = "wording_id, kind, sequence, id"
    _check_company_auto = True

    wording_id = fields.Many2one(
        "l10n_vn.contract.wording", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="wording_id.company_id", store=True)
    kind = fields.Selection(
        [
            ("labour", "Labour contract"),
            ("probation", "Probation contract"),
            ("training", "Training contract"),
        ],
        string="Form",
        required=True,
        default="labour",
    )
    sequence = fields.Integer(default=10)
    title = fields.Char(string="Title", required=True)
    body = fields.Html(string="Text")
    active = fields.Boolean(default=True)
