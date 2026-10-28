# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.l10n_vn_einvoice import normalise_vat


class L10nVnEinvoiceAttach(models.TransientModel):
    _name = "l10n_vn.einvoice.attach"
    _description = "Attach E-Invoice"

    move_id = fields.Many2one(
        comodel_name="account.move", string="Document", required=True, readonly=True
    )
    file = fields.Binary(string="XML File", required=True)
    filename = fields.Char()
    error = fields.Text(compute="_compute_preview")
    preview_name = fields.Char(string="E-Invoice", compute="_compute_preview")
    preview_seller_vat = fields.Char(string="Seller Tax Code", compute="_compute_preview")
    preview_seller_name = fields.Char(string="Seller", compute="_compute_preview")
    preview_buyer_vat = fields.Char(string="Buyer Tax Code", compute="_compute_preview")
    preview_invoice_date = fields.Date(string="Invoice Date", compute="_compute_preview")
    preview_currency_id = fields.Many2one(
        comodel_name="res.currency", compute="_compute_preview"
    )
    preview_amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        compute="_compute_preview",
        currency_field="preview_currency_id",
    )
    preview_amount_tax = fields.Monetary(
        string="VAT", compute="_compute_preview", currency_field="preview_currency_id"
    )
    preview_amount_total = fields.Monetary(
        string="Total", compute="_compute_preview", currency_field="preview_currency_id"
    )
    partner_vat = fields.Char(
        string="Partner Tax Code", related="move_id.commercial_partner_id.vat"
    )
    partner_differs = fields.Boolean(compute="_compute_preview")
    date_differs = fields.Boolean(compute="_compute_preview")
    amounts_differ = fields.Boolean(compute="_compute_preview")

    def _reset_preview(self):
        self.update(
            {
                "error": False,
                "preview_name": False,
                "preview_seller_vat": False,
                "preview_seller_name": False,
                "preview_buyer_vat": False,
                "preview_invoice_date": False,
                "preview_currency_id": False,
                "preview_amount_untaxed": 0.0,
                "preview_amount_tax": 0.0,
                "preview_amount_total": 0.0,
                "partner_differs": False,
                "date_differs": False,
                "amounts_differ": False,
            }
        )

    def _file_content(self):
        """The file's bytes. Read without bin_size: the web client reads a saved
        record with bin_size=True, which turns a Binary field into its size
        ("9.67 kb") (odoo/fields.py:2532, :2604-2605)."""
        self.ensure_one()
        wizard = self.with_context(bin_size=False, bin_size_file=False)
        return base64.b64decode(wizard.file or b"")

    @api.depends("file", "move_id")
    def _compute_preview(self):
        Einvoice = self.env["l10n_vn.einvoice"]
        for wizard in self:
            wizard._reset_preview()
            if not wizard.file or not wizard.move_id:
                continue
            move = wizard.move_id
            try:
                values = Einvoice._read_xml(wizard._file_content())
                direction = Einvoice._get_direction(values, move.company_id)
                Einvoice._check_document(direction, move)
            except UserError as exc:
                wizard.error = exc.args[0]
                continue
            currency = self.env["res.currency"].browse(values["currency_id"])
            party_vat = (
                values["seller_vat"] if direction == "received" else values["buyer_vat"]
            )
            partner_vat = normalise_vat(move.commercial_partner_id.vat)
            wizard.update(
                {
                    "preview_name": f"{values['symbol']}-{values['number']}",
                    "preview_seller_vat": values["seller_vat"],
                    "preview_seller_name": values["seller_name"],
                    "preview_buyer_vat": values["buyer_vat"],
                    "preview_invoice_date": values["invoice_date"],
                    "preview_currency_id": currency.id,
                    "preview_amount_untaxed": values["amount_untaxed"],
                    "preview_amount_tax": values["amount_tax"],
                    "preview_amount_total": values["amount_total"],
                    "partner_differs": bool(partner_vat) and partner_vat != party_vat,
                    "date_differs": bool(move.invoice_date)
                    and move.invoice_date != values["invoice_date"],
                    "amounts_differ": currency != move.currency_id
                    or bool(
                        currency.compare_amounts(values["amount_total"], move.amount_total)
                    ),
                }
            )

    def action_attach(self):
        self.ensure_one()
        self.env["l10n_vn.einvoice"]._attach_xml(
            self._file_content(),
            self.filename or "einvoice.xml",
            self.move_id,
        )
        return {"type": "ir.actions.act_window_close"}
