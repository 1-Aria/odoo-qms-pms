# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnEinvoicePortalRow(models.Model):
    _name = "l10n_vn.einvoice.portal.row"
    _description = "E-Invoice Portal List Row"
    _order = "batch_id, id"

    batch_id = fields.Many2one(
        comodel_name="l10n_vn.einvoice.batch",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="batch_id.company_id",
        store=True,
        index=True,
    )
    # The list's columns, as imported (D3).
    col_stt = fields.Char(string="No.")
    col_form = fields.Char(string="Form")
    col_symbol = fields.Char(string="Symbol")
    col_number = fields.Char(string="Number")
    col_date = fields.Char(string="Date")
    col_seller_vat = fields.Char(string="Seller Tax Code")
    col_seller_name = fields.Char(string="Seller")
    col_seller_address = fields.Char(string="Seller Address")
    col_buyer_vat = fields.Char(string="Buyer Tax Code")
    col_buyer_name = fields.Char(string="Buyer")
    col_buyer_address = fields.Char(string="Buyer Address")
    # Not restricted by groups: the import writes every column, and an accountant
    # imports (D14).
    col_citizen_id = fields.Char(string="Citizen ID")
    col_untaxed = fields.Char(string="Untaxed Amount")
    col_tax = fields.Char(string="VAT")
    col_discount = fields.Char(string="Commercial Discount")
    col_fees = fields.Char(string="Fees")
    col_total = fields.Char(string="Total")
    col_currency = fields.Char(string="Currency")
    col_rate = fields.Char(string="Rate")
    col_status = fields.Char(string="Status")
    col_check = fields.Char(string="Check Result")
    invoice_id = fields.Many2one(
        comodel_name="l10n_vn.einvoice.portal",
        string="Portal Invoice",
        ondelete="set null",
        index=True,
    )
    error = fields.Char()
