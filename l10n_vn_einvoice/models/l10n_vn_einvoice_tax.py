# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


def _normalise_code(values):
    if values.get("code"):
        values["code"] = values["code"].strip().upper()
    return values


class L10nVnEinvoiceTax(models.Model):
    _name = "l10n_vn.einvoice.tax"
    _description = "E-Invoice VAT Code"
    _order = "company_id, code"
    _rec_name = "code"
    _check_company_auto = True

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    code = fields.Char(
        string="VAT Code",
        required=True,
        help="The rate code as the e-invoice writes it in TSuat: 0%, 5%, 8%, 10%, "
        "KCT, KKKNT, KHAC:…",
    )
    tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Tax",
        check_company=True,
        domain="[('type_tax_use', '=', 'purchase')]",
        ondelete="restrict",
        help="The purchase tax for lines with this code. Leave empty for lines that "
        "carry no VAT.",
    )

    _sql_constraints = [
        (
            "code_unique",
            "unique(company_id, code)",
            "This VAT code is already mapped in this company.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([_normalise_code(dict(vals)) for vals in vals_list])

    def write(self, vals):
        return super().write(_normalise_code(dict(vals)))
