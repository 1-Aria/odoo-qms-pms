# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from decimal import Decimal, InvalidOperation

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# --------------------------------------------------------------------------
# Normalisation of the invoice key (design §4). Module-level, so that
# l10n_vn_einvoice_reconcile applies the same rules to the portal's columns.
# --------------------------------------------------------------------------


def normalise_vat(value):
    """Tax code without whitespace; the branch suffix (-001) is kept."""
    return re.sub(r"\s+", "", value or "")


def normalise_symbol(value):
    """Symbol without whitespace, in upper case."""
    return re.sub(r"\s+", "", value or "").upper()


def normalise_number(value):
    """Invoice number without leading zeros; "0" stays "0"."""
    value = (value or "").strip()
    if not value:
        return ""
    return value.lstrip("0") or "0"


def _path(path):
    """Turn "DLHDon/TTChung/PBan" into a namespace-agnostic lxml path."""
    return "/".join("{*}" + step for step in path.split("/"))


def _text(root, path):
    node = root.find(_path(path))
    if node is None or node.text is None:
        return ""
    return node.text.strip()


class L10nVnEinvoice(models.Model):
    _name = "l10n_vn.einvoice"
    _description = "Vietnamese E-Invoice"
    _inherit = ["mail.thread"]
    _order = "invoice_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True, index="trigram")
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
    )
    direction = fields.Selection(
        selection=[("received", "Received"), ("issued", "Issued")],
        required=True,
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Document",
        readonly=True,
        index=True,
        copy=False,
        ondelete="set null",
        check_company=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("not_booked", "Not Booked"),
            ("draft", "Draft"),
            ("booked", "Booked"),
        ],
        compute="_compute_state",
        store=True,
        index=True,
    )
    format_version = fields.Char(string="Format Version", required=True, readonly=True)
    form = fields.Char(required=True, readonly=True)
    symbol = fields.Char(required=True, readonly=True)
    number = fields.Char(required=True, readonly=True)
    invoice_date = fields.Date(required=True, readonly=True)
    tax_authority_code = fields.Char(readonly=True)
    seller_vat = fields.Char(
        string="Seller Tax Code", required=True, readonly=True, index=True
    )
    seller_name = fields.Char(string="Seller", readonly=True)
    buyer_vat = fields.Char(string="Buyer Tax Code", readonly=True, index=True)
    buyer_name = fields.Char(string="Buyer", readonly=True)
    provider_vat = fields.Char(string="Provider Tax Code", readonly=True)
    currency_id = fields.Many2one(
        comodel_name="res.currency", required=True, readonly=True
    )
    exchange_rate = fields.Float(readonly=True)
    amount_untaxed = fields.Monetary(string="Untaxed Amount", readonly=True)
    amount_tax = fields.Monetary(string="VAT", readonly=True)
    amount_total = fields.Monetary(string="Total", readonly=True)
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML File",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )

    _sql_constraints = [
        (
            "key_unique",
            "unique(company_id, seller_vat, form, symbol, number)",
            "This e-invoice has already been read into this company.",
        ),
        (
            "move_unique",
            "unique(move_id)",
            "A document can carry only one e-invoice.",
        ),
    ]

    @api.depends("symbol", "number")
    def _compute_name(self):
        for einvoice in self:
            einvoice.name = f"{einvoice.symbol or ''}-{einvoice.number or ''}"

    @api.depends("move_id", "move_id.state")
    def _compute_state(self):
        for einvoice in self:
            move_state = einvoice.move_id.state
            if move_state == "posted":
                einvoice.state = "booked"
            elif move_state == "draft":
                einvoice.state = "draft"
            else:
                einvoice.state = "not_booked"

    # ----------------------------------------------------------------------
    # Reading the XML
    # ----------------------------------------------------------------------

    @api.model
    def _l10n_vn_einvoice_readers(self):
        return {
            "2.1.0": self._read_v2_1,
            "2.1.1": self._read_v2_1,
        }

    @api.model
    def _read_xml(self, content):
        """Read an e-invoice XML into field values (no company, direction or
        document). Raises UserError when the file cannot be read."""
        root = None
        try:
            root = etree.fromstring(
                content,
                parser=etree.XMLParser(remove_comments=True, resolve_entities=False),
            )
        except (etree.XMLSyntaxError, ValueError, TypeError):
            root = None
        if root is None or etree.QName(root).localname != "HDon":
            raise UserError(_("This file is not a Vietnamese e-invoice XML."))
        version = _text(root, "DLHDon/TTChung/PBan")
        reader = self._l10n_vn_einvoice_readers().get(version)
        if not reader:
            raise UserError(
                _(
                    "E-invoice format version %(version)s is not supported.",
                    version=version or "?",
                )
            )
        values = reader(root)
        self._check_read_values(values)
        return values

    @api.model
    def _read_amount(self, root, path, default=0.0):
        text = _text(root, path)
        if not text:
            return default
        try:
            return float(Decimal(text))
        except InvalidOperation as exc:
            raise UserError(
                _(
                    "The e-invoice has an unreadable amount in %(tag)s: %(value)s",
                    tag=path.rsplit("/", 1)[-1],
                    value=text,
                )
            ) from exc

    @api.model
    def _read_v2_1(self, root):
        form = _text(root, "DLHDon/TTChung/KHMSHDon")
        date_text = _text(root, "DLHDon/TTChung/NLap")
        try:
            invoice_date = fields.Date.to_date(date_text[:10]) if date_text else False
        except ValueError as exc:
            raise UserError(
                _("The e-invoice has an unreadable date: %(value)s", value=date_text)
            ) from exc

        currency_code = _text(root, "DLHDon/TTChung/DVTTe")
        currency = self.env["res.currency"].search([("name", "=", currency_code)], limit=1)
        if not currency:
            raise UserError(
                _("Currency %(code)s is not active.", code=currency_code or "?")
            )

        amount_total = self._read_amount(root, "DLHDon/NDHDon/TToan/TgTTTBSo")
        if form == "2":
            # A sales invoice carries no VAT and gives only the total.
            amount_untaxed, amount_tax = amount_total, 0.0
        else:
            amount_untaxed = self._read_amount(root, "DLHDon/NDHDon/TToan/TgTCThue")
            amount_tax = self._read_amount(root, "DLHDon/NDHDon/TToan/TgTThue")

        return {
            "format_version": _text(root, "DLHDon/TTChung/PBan"),
            "form": form,
            "symbol": normalise_symbol(_text(root, "DLHDon/TTChung/KHHDon")),
            "number": normalise_number(_text(root, "DLHDon/TTChung/SHDon")),
            "invoice_date": invoice_date,
            "tax_authority_code": _text(root, "MCCQT") or False,
            "seller_vat": normalise_vat(_text(root, "DLHDon/NDHDon/NBan/MST")),
            "seller_name": _text(root, "DLHDon/NDHDon/NBan/Ten") or False,
            "buyer_vat": normalise_vat(_text(root, "DLHDon/NDHDon/NMua/MST")) or False,
            "buyer_name": _text(root, "DLHDon/NDHDon/NMua/Ten") or False,
            "provider_vat": normalise_vat(_text(root, "DLHDon/TTChung/MSTTCGP")) or False,
            "currency_id": currency.id,
            "exchange_rate": self._read_amount(root, "DLHDon/TTChung/TGia", default=1.0),
            "amount_untaxed": amount_untaxed,
            "amount_tax": amount_tax,
            "amount_total": amount_total,
        }

    @api.model
    def _check_read_values(self, values):
        if values.get("form") not in ("1", "2"):
            raise UserError(
                _(
                    "Invoice form %(form)s is not supported: only VAT invoices (1) "
                    "and sales invoices (2) are read.",
                    form=values.get("form") or "?",
                )
            )
        for field_name, tag in (
            ("invoice_date", "NLap"),
            ("symbol", "KHHDon"),
            ("number", "SHDon"),
            ("seller_vat", "NBan/MST"),
        ):
            if not values.get(field_name):
                raise UserError(_("The e-invoice has no %(tag)s.", tag=tag))
        if values["symbol"].startswith("C") and not values.get("tax_authority_code"):
            raise UserError(
                _(
                    "Invoice %(symbol)s-%(number)s has a coded symbol but no tax "
                    "authority code: this is not the tax authority's version of the file.",
                    symbol=values["symbol"],
                    number=values["number"],
                )
            )

    # ----------------------------------------------------------------------
    # Company, document and key
    # ----------------------------------------------------------------------

    @api.model
    def _get_direction(self, values, company):
        company_vat = normalise_vat(company.vat)
        if company_vat and values.get("seller_vat") == company_vat:
            return "issued"
        if company_vat and values.get("buyer_vat") == company_vat:
            return "received"
        raise UserError(
            _(
                "This e-invoice is between %(seller)s and %(buyer)s; neither is the "
                "tax code of %(company)s (%(vat)s).",
                seller=values.get("seller_vat") or "?",
                buyer=values.get("buyer_vat") or _("a consumer"),
                company=company.name,
                vat=company.vat or _("none"),
            )
        )

    @api.model
    def _check_document(self, direction, move):
        if move.state == "cancel":
            raise UserError(_("An e-invoice cannot be attached to a cancelled document."))
        if direction == "received" and not move.is_purchase_document():
            raise UserError(
                _("A received e-invoice can only be attached to a vendor bill or refund.")
            )
        if direction == "issued" and not move.is_sale_document():
            raise UserError(
                _(
                    "An issued e-invoice can only be attached to a customer invoice "
                    "or credit note."
                )
            )

    @api.model
    def _find_by_key(self, values, company):
        # sudo: a record rule must not hide a duplicate.
        return self.sudo().search(
            [
                ("company_id", "=", company.id),
                ("seller_vat", "=", values["seller_vat"]),
                ("form", "=", values["form"]),
                ("symbol", "=", values["symbol"]),
                ("number", "=", values["number"]),
            ],
            limit=1,
        )

    @api.model
    def _attach_xml(self, content, filename, move):
        """Read the XML and link its e-invoice to an existing document."""
        move.ensure_one()
        values = self._read_xml(content)
        company = move.company_id
        direction = self._get_direction(values, company)
        self._check_document(direction, move)

        existing = self._find_by_key(values, company)
        if existing and existing.move_id and existing.move_id.state != "cancel":
            raise UserError(
                _(
                    "E-invoice %(name)s is already attached to %(document)s.",
                    name=existing.name,
                    document=existing.move_id.display_name,
                )
            )
        current = move.l10n_vn_einvoice_ids
        if current and current != existing:
            raise UserError(
                _(
                    "%(document)s already carries e-invoice %(name)s.",
                    document=move.display_name,
                    name=current[:1].name,
                )
            )

        if existing:
            einvoice = self.browse(existing.id)
            einvoice.move_id = move
        else:
            einvoice = self.create(
                {
                    **values,
                    "company_id": company.id,
                    "direction": direction,
                    "move_id": move.id,
                }
            )
            einvoice.attachment_id = self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "raw": content,
                    "mimetype": "application/xml",
                    "res_model": self._name,
                    "res_id": einvoice.id,
                }
            )

        move.message_post(
            body=_("E-invoice %(name)s attached.", name=einvoice.name),
            attachments=[(filename, content)],
        )
        return einvoice

    # ----------------------------------------------------------------------
    # Actions
    # ----------------------------------------------------------------------

    def action_open_document(self):
        self.ensure_one()
        xmlid = (
            "account.action_move_in_invoice_type"
            if self.direction == "received"
            else "account.action_move_out_invoice_type"
        )
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action.update(
            {
                "res_id": self.move_id.id,
                "views": [(False, "form")],
                "view_mode": "form",
            }
        )
        return action
