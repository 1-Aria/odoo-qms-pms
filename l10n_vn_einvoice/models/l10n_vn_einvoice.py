# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from decimal import Decimal, InvalidOperation

from lxml import etree
from markupsafe import Markup

from odoo import Command, _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError
from odoo.tools import float_round, format_amount

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


def _decimal(text, tag):
    """Decimal of an amount's text, None when empty (D3)."""
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise UserError(
            _(
                "The e-invoice has an unreadable amount in %(tag)s: %(value)s",
                tag=tag,
                value=text,
            )
        ) from exc


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
    move_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Document Partner",
        related="move_id.partner_id",
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
    amounts_differ = fields.Boolean(compute="_compute_amounts_differ")
    # Step 3: the invoice this one replaces or adjusts (TTHDLQuan).
    relation_type = fields.Selection(
        selection=[
            ("1", "Replaces one invoice"),
            ("2", "Adjusts one invoice"),
            ("3", "Replaces several invoices"),
            ("4", "Adjusts several invoices"),
            ("5", "Commercial discount"),
        ],
        string="Correction",
        readonly=True,
    )
    related_regime = fields.Char(readonly=True)
    related_vat = fields.Char(string="Corrected Seller Tax Code", readonly=True, index=True)
    related_form = fields.Char(readonly=True, index=True)
    related_symbol = fields.Char(readonly=True, index=True)
    related_number = fields.Char(readonly=True, index=True)
    related_date = fields.Date(readonly=True)
    adjust_reason = fields.Char(readonly=True)
    related_einvoice_id = fields.Many2one(
        comodel_name="l10n_vn.einvoice",
        string="Corrects",
        readonly=True,
        index=True,
        copy=False,
        ondelete="set null",
        check_company=True,
    )
    correction_ids = fields.One2many(
        comodel_name="l10n_vn.einvoice",
        inverse_name="related_einvoice_id",
        string="Corrections",
    )
    correction_state = fields.Selection(
        selection=[("replaced", "Replaced"), ("adjusted", "Adjusted")],
        compute="_compute_correction_state",
        store=True,
        index=True,
    )
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

    @api.depends("correction_ids.relation_type")
    def _compute_correction_state(self):
        for einvoice in self:
            kinds = set(einvoice.correction_ids.mapped("relation_type"))
            if kinds & {"1", "3"}:
                einvoice.correction_state = "replaced"
            elif kinds & {"2", "4", "5"}:
                einvoice.correction_state = "adjusted"
            else:
                einvoice.correction_state = False

    def _document_sign(self):
        """-1 on a refund or credit note, whose totals are positive while a
        decreasing adjustment's are negative (D29)."""
        self.ensure_one()
        return -1 if self.move_id.move_type in ("in_refund", "out_refund") else 1

    @api.depends(
        "move_id.move_type",
        "move_id.amount_untaxed",
        "move_id.amount_tax",
        "move_id.amount_total",
        "move_id.currency_id",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
        "currency_id",
    )
    def _compute_amounts_differ(self):
        for einvoice in self:
            move = einvoice.move_id
            if not move:
                einvoice.amounts_differ = False
                continue
            currency = einvoice.currency_id
            sign = einvoice._document_sign()
            einvoice.amounts_differ = move.currency_id != currency or any(
                currency.compare_amounts(sign * ours, theirs)
                for ours, theirs in (
                    (einvoice.amount_untaxed, move.amount_untaxed),
                    (einvoice.amount_tax, move.amount_tax),
                    (einvoice.amount_total, move.amount_total),
                )
            )

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
    def _l10n_vn_einvoice_line_readers(self):
        return {
            "2.1.0": self._read_lines_v2_1,
            "2.1.1": self._read_lines_v2_1,
        }

    @api.model
    def _parse_xml(self, content):
        """Parse an e-invoice XML; return its root and format version."""
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
        return root, _text(root, "DLHDon/TTChung/PBan")

    @api.model
    def _get_reader(self, readers, version):
        reader = readers.get(version)
        if not reader:
            raise UserError(
                _(
                    "E-invoice format version %(version)s is not supported.",
                    version=version or "?",
                )
            )
        return reader

    @api.model
    def _read_xml(self, content):
        """Read an e-invoice XML into field values (no company, direction or
        document). Raises UserError when the file cannot be read."""
        root, version = self._parse_xml(content)
        values = self._get_reader(self._l10n_vn_einvoice_readers(), version)(root)
        self._check_read_values(values)
        return values

    @api.model
    def _read_xml_lines(self, content):
        """Read the lines and the per-rate tax rows of an e-invoice XML."""
        root, version = self._parse_xml(content)
        return self._get_reader(self._l10n_vn_einvoice_line_readers(), version)(root)

    @api.model
    def _read_amount(self, root, path, default=0.0):
        value = _decimal(_text(root, path), path.rsplit("/", 1)[-1])
        return default if value is None else float(value)

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

        relation = {
            "relation_type": False,
            "related_regime": False,
            "related_vat": False,
            "related_form": False,
            "related_symbol": False,
            "related_number": False,
            "related_date": False,
            "adjust_reason": False,
        }
        if root.find(_path("DLHDon/TTChung/TTHDLQuan")) is not None:
            base = "DLHDon/TTChung/TTHDLQuan/"
            related_date = _text(root, base + "NLHDCLQuan")
            try:
                related_date = fields.Date.to_date(related_date[:10]) if related_date else False
            except ValueError as exc:
                raise UserError(
                    _("The e-invoice has an unreadable date: %(value)s", value=related_date)
                ) from exc
            relation = {
                "relation_type": _text(root, base + "TCHDon") or False,
                "related_regime": _text(root, base + "LHDCLQuan") or False,
                "related_vat": normalise_vat(_text(root, base + "MSTCLQuan"))
                or normalise_vat(_text(root, "DLHDon/NDHDon/NBan/MST"))
                or False,
                "related_form": _text(root, base + "KHMSHDCLQuan") or False,
                "related_symbol": normalise_symbol(_text(root, base + "KHHDCLQuan")) or False,
                "related_number": normalise_number(_text(root, base + "SHDCLQuan")) or False,
                "related_date": related_date,
                "adjust_reason": _text(root, base + "LDDCTThe") or False,
            }
            if relation["relation_type"] not in dict(self._fields["relation_type"].selection):
                raise UserError(
                    _(
                        "The e-invoice has an unknown correction type: %(value)s",
                        value=relation["relation_type"] or "?",
                    )
                )

        return {
            **relation,
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
    def _read_lines_v2_1(self, root):
        lines = []
        for position, node in enumerate(
            root.findall(_path("DLHDon/NDHDon/DSHHDVu/HHDVu")), start=1
        ):

            def text(tag, node=node):
                return (node.findtext("{*}" + tag) or "").strip()

            stt = text("STT")
            lines.append(
                {
                    "kind": text("TChat") or "1",
                    "sequence": int(stt) if stt.isdigit() else position,
                    "position": position,
                    "name": text("THHDVu"),
                    "uom": text("DVTinh"),
                    "quantity": _decimal(text("SLuong"), "SLuong"),
                    "quantity_text": text("SLuong"),
                    "price": _decimal(text("DGia"), "DGia"),
                    "price_text": text("DGia"),
                    "discount": _decimal(text("TLCKhau"), "TLCKhau"),
                    "discount_amount": _decimal(text("STCKhau"), "STCKhau"),
                    "amount": _decimal(text("ThTien"), "ThTien") or Decimal(0),
                    "code": text("TSuat").upper(),
                }
            )
        lines.sort(key=lambda line: (line["sequence"], line["position"]))

        tax_rows = []
        for node in root.findall(_path("DLHDon/NDHDon/TToan/THTTLTSuat/LTSuat")):
            tax_rows.append(
                {
                    "code": (node.findtext("{*}TSuat") or "").strip().upper(),
                    "amount": _decimal((node.findtext("{*}ThTien") or "").strip(), "ThTien")
                    or Decimal(0),
                    "tax": _decimal((node.findtext("{*}TThue") or "").strip(), "TThue")
                    or Decimal(0),
                }
            )
        return lines, tax_rows

    @api.model
    def _read_party(self, content, role):
        """The details of a party (NBan or NMua), for creating its partner."""
        root, _version = self._parse_xml(content)
        base = f"DLHDon/NDHDon/{role}/"
        return {
            "name": _text(root, base + "Ten"),
            "vat": normalise_vat(_text(root, base + "MST")),
            "street": _text(root, base + "DChi"),
            "phone": _text(root, base + "SDThoai"),
            "email": _text(root, base + "DCTDTu"),
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
    # Company, document, key, partner, taxes
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
    def _find_partner(self, vat, company):
        """The commercial partners holding exactly this tax code (D15)."""
        Partner = self.env["res.partner"]
        if not vat:
            return Partner
        return Partner.search(
            [
                ("vat", "=", vat),
                ("parent_id", "=", False),
                *Partner._check_company_domain(company),
            ]
        )

    @api.model
    def _tax_map(self, company):
        rows = self.env["l10n_vn.einvoice.tax"].search([("company_id", "=", company.id)])
        return {row.code: row.tax_id for row in rows}

    # ----------------------------------------------------------------------
    # Linking
    # ----------------------------------------------------------------------

    @api.model
    def _link_or_create(self, values, direction, content, filename, move, existing, notify=True):
        """Link the e-invoice (existing, or created with its file) to a document.
        The duplicate check stays with the callers."""
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
                    "company_id": move.company_id.id,
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
            einvoice._link_related()
        if notify:
            # no_new_invoice: core's chatter hook would otherwise read the posted
            # XML as an import (account_move.py:6490-6502), filling an empty draft
            # or noting that a bill with lines or a posted one was not updated.
            move.with_context(no_new_invoice=True).message_post(
                body=_("E-invoice %(name)s attached.", name=einvoice.name),
                attachments=[(filename, content)],
            )
        return einvoice

    def _link_related(self):
        """Link this e-invoice to the invoice it corrects, and the corrections
        already read to it, in its company (D27). Searched as superuser, like
        _find_by_key; the links are written as the user."""
        Einvoice = self.sudo()
        for einvoice in self:
            pairs = []
            if einvoice.relation_type in ("1", "2", "5") and einvoice.related_number:
                original = Einvoice.search(
                    [
                        ("company_id", "=", einvoice.company_id.id),
                        ("seller_vat", "=", einvoice.related_vat),
                        ("form", "=", einvoice.related_form),
                        ("symbol", "=", einvoice.related_symbol),
                        ("number", "=", einvoice.related_number),
                        ("id", "!=", einvoice.id),
                    ],
                    limit=1,
                )
                if original:
                    pairs.append((einvoice, self.browse(original.id)))
            corrections = Einvoice.search(
                [
                    ("company_id", "=", einvoice.company_id.id),
                    ("related_einvoice_id", "=", False),
                    ("relation_type", "in", ("1", "2", "5")),
                    ("related_vat", "=", einvoice.seller_vat),
                    ("related_form", "=", einvoice.form),
                    ("related_symbol", "=", einvoice.symbol),
                    ("related_number", "=", einvoice.number),
                    ("id", "!=", einvoice.id),
                ]
            )
            pairs += [(self.browse(correction.id), einvoice) for correction in corrections]
            for correction, original in pairs:
                correction.related_einvoice_id = original
                if original.move_id:
                    verb = _("replaces") if correction.relation_type == "1" else _("adjusts")
                    original.move_id.with_context(no_new_invoice=True).message_post(
                        body=_(
                            "E-invoice %(correction)s %(verb)s the e-invoice of this "
                            "document, %(original)s.",
                            correction=correction.name,
                            verb=verb,
                            original=original.name,
                        )
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
        return self._link_or_create(values, direction, content, filename, move, existing)

    # ----------------------------------------------------------------------
    # Bills from XML (step 2)
    # ----------------------------------------------------------------------

    @api.model
    def _import_document(self, invoice, file_data, new=False):
        """The decoder registered in account.move._get_edi_decoder: fill a vendor
        bill from an e-invoice XML."""
        content = file_data["content"]
        filename = file_data.get("filename") or "einvoice.xml"
        values = self._read_xml(content)
        company = invoice.company_id
        name = f"{values['symbol']}-{values['number']}"

        direction = self._get_direction(values, company)
        if direction != "received" or invoice.move_type != "in_invoice":
            raise UserError(
                _(
                    "Only received e-invoices create vendor bills. Attach this one to "
                    "its document with Attach E-Invoice."
                )
            )
        if values["relation_type"] and values["relation_type"] != "1":
            # Only a replacement is a complete invoice (D28).
            raise UserError(
                _(
                    "E-invoice %(name)s adjusts an invoice or corrects several, which is "
                    "not created as a document. Enter the bill or refund by hand and "
                    "attach the XML.",
                    name=name,
                )
            )

        existing = self._find_by_key(values, company)
        if (
            existing
            and existing.move_id
            and existing.move_id.state != "cancel"
            and existing.move_id != invoice
        ):
            raise RedirectWarning(
                _(
                    "E-invoice %(name)s is already on %(document)s.",
                    name=existing.name,
                    document=existing.move_id.display_name,
                ),
                {
                    "type": "ir.actions.act_window",
                    "res_model": self._name,
                    "res_id": existing.id,
                    "views": [(False, "form")],
                    "view_mode": "form",
                },
                _("Open E-Invoice"),
            )

        lines, tax_rows = self._read_xml_lines(content)
        form = values["form"]
        Tax = self.env["account.tax"]
        tax_map = {}
        if form == "1":
            tax_map = self._tax_map(company)
            for line in lines:
                if line["kind"] != "4" and not line["code"]:
                    raise UserError(
                        _(
                            "Line %(line)s of e-invoice %(name)s has no VAT code.",
                            line=line["sequence"],
                            name=name,
                        )
                    )
            missing = sorted(
                {line["code"] for line in lines if line["kind"] != "4"} - set(tax_map)
            )
            if missing:
                raise UserError(
                    _(
                        "VAT codes %(codes)s have no row in E-Invoice VAT Codes for "
                        "%(company)s.",
                        codes=", ".join(missing),
                        company=company.name,
                    )
                )

        notes = []
        partners = self._find_partner(values["seller_vat"], company)
        if not partners:
            notes.append(
                _(
                    "No partner has tax code %(vat)s (%(seller)s). Choose the supplier, "
                    "or use Create Supplier on the e-invoice.",
                    vat=values["seller_vat"],
                    seller=values["seller_name"] or "?",
                )
            )
        elif len(partners) > 1:
            notes.append(
                _(
                    "Several partners have tax code %(vat)s: %(names)s. Choose the supplier.",
                    vat=values["seller_vat"],
                    names=", ".join(partners.mapped("display_name")),
                )
            )

        currency = self.env["res.currency"].browse(values["currency_id"])
        line_commands = []
        for line in lines:
            taxes = tax_map.get(line["code"], Tax) if form == "1" else Tax
            line_values, note = self._bill_line_values(line, taxes, currency)
            line_commands.append(Command.create(line_values))
            if note:
                notes.append(note)

        with invoice._get_edi_creation() as move:
            # The partner first: lines created after it keep the taxes given.
            header = {
                "ref": name,
                "invoice_date": values["invoice_date"],
                "currency_id": currency.id,
            }
            if len(partners) == 1:
                header["partner_id"] = partners.id
            move.write(header)
            move.write({"invoice_line_ids": line_commands})

        if form == "1":
            with invoice._get_edi_creation() as move:
                notes += self._correct_taxes(move, tax_rows, tax_map)

        if any(
            currency.compare_amounts(ours, theirs)
            for ours, theirs in (
                (invoice.amount_untaxed, values["amount_untaxed"]),
                (invoice.amount_tax, values["amount_tax"]),
                (invoice.amount_total, values["amount_total"]),
            )
        ):
            notes.append(
                _(
                    "The bill's totals differ from the e-invoice: untaxed %(untaxed)s / "
                    "%(xml_untaxed)s, VAT %(tax)s / %(xml_tax)s, total %(total)s / "
                    "%(xml_total)s.",
                    untaxed=format_amount(self.env, invoice.amount_untaxed, currency),
                    xml_untaxed=format_amount(self.env, values["amount_untaxed"], currency),
                    tax=format_amount(self.env, invoice.amount_tax, currency),
                    xml_tax=format_amount(self.env, values["amount_tax"], currency),
                    total=format_amount(self.env, invoice.amount_total, currency),
                    xml_total=format_amount(self.env, values["amount_total"], currency),
                )
            )

        einvoice = self._link_or_create(
            values, "received", content, filename, invoice, existing, notify=False
        )
        if values["relation_type"] == "1":
            if einvoice.related_einvoice_id:
                notes.insert(
                    0,
                    _(
                        "It replaces e-invoice %(original)s.",
                        original=einvoice.related_einvoice_id.name,
                    ),
                )
            else:
                notes.insert(
                    0,
                    _(
                        "It replaces invoice %(symbol)s-%(number)s of %(date)s, which is "
                        "not in Odoo.",
                        symbol=values["related_symbol"] or "?",
                        number=values["related_number"] or "?",
                        date=values["related_date"] or "?",
                    ),
                )
        body = Markup("<p>%s</p>") % _("Created from e-invoice %(name)s.", name=name)
        if notes:
            body += Markup("<ul>%s</ul>") % Markup().join(
                Markup("<li>%s</li>") % note for note in notes
            )
        invoice.message_post(body=body)
        return True

    @api.model
    def _line_gives_amount(self, quantity, price, discount, amount, currency):
        """Whether quantity × price less the discount, at Odoo's precisions,
        gives the line's amount (D16)."""
        precision = self.env["decimal.precision"]
        quantity = float_round(
            float(quantity),
            precision_digits=precision.precision_get("Product Unit of Measure"),
        )
        price = float_round(
            float(price), precision_digits=precision.precision_get("Product Price")
        )
        subtotal = currency.round(quantity * price * (1 - float(discount) / 100))
        return not currency.compare_amounts(subtotal, float(amount))

    @api.model
    def _bill_line_values(self, line, taxes, currency):
        """The invoice_line_ids values of one read line, and the note for the
        import message when the line falls back to 1 × its amount."""
        name = line["name"] or "/"
        if line["kind"] == "4":
            return {"display_type": "line_note", "name": name}, None
        tax_command = [Command.set(taxes.ids)]
        amount = line["amount"]
        if line["kind"] == "3":
            return {
                "name": name,
                "quantity": 1.0,
                "price_unit": -float(abs(amount)),
                "discount": 0.0,
                "tax_ids": tax_command,
            }, None

        quantity, price = line["quantity"], line["price"]
        discount = line["discount"]
        if discount is None:
            discount = Decimal(0)
            if line["discount_amount"] and quantity and price and quantity * price > 0:
                discount = line["discount_amount"] / (quantity * price) * 100
        if (
            quantity is not None
            and price is not None
            and self._line_gives_amount(quantity, price, discount, amount, currency)
        ):
            return {
                "name": name,
                "quantity": float(quantity),
                "price_unit": float(price),
                "discount": float(discount),
                "tax_ids": tax_command,
            }, None

        label = name
        if line["quantity_text"] or line["price_text"]:
            label = (
                f"{name} ({line['quantity_text']} {line['uom']} × {line['price_text']})"
            ).replace("  ", " ")
        formatted = format_amount(self.env, float(amount), currency)
        note = _(
            "Line %(line)s: quantity × price does not give %(amount)s; entered as "
            "1 × %(amount)s.",
            line=line["sequence"],
            amount=formatted,
        )
        return {
            "name": label,
            "quantity": 1.0,
            "price_unit": float(amount),
            "discount": 0.0,
            "tax_ids": tax_command,
        }, note

    @api.model
    def _correct_taxes(self, move, tax_rows, tax_map):
        """Set each mapped tax to the e-invoice's per-rate amount when the gap is
        rounding (D17). Runs inside move._get_edi_creation(); returns the notes
        for the corrections not applied."""
        totals = {}
        for row in tax_rows:
            tax = tax_map.get(row["code"])
            if not tax:
                continue
            entry = totals.setdefault(tax.id, {"tax": tax, "amount": Decimal(0)})
            entry["amount"] += row["tax"]

        notes = []
        currency = move.currency_id
        for entry in totals.values():
            tax = entry["tax"]
            xml_amount = float(entry["amount"])
            tax_lines = move.line_ids.filtered(lambda line, tax=tax: line.tax_line_id == tax)
            # A vendor bill's tax lines are debits: sign 1 (account_edi_xml_ubl_20.py:992).
            bill_amount = currency.round(sum(tax_lines.mapped("amount_currency")))
            difference = currency.round(xml_amount - bill_amount)
            if currency.is_zero(difference):
                continue
            product_lines = move.invoice_line_ids.filtered(
                lambda line, tax=tax: tax in line.tax_ids
            )
            tolerance = len(product_lines) * currency.rounding
            if tax_lines and abs(difference) <= tolerance + currency.rounding / 2:
                tax_lines[0].amount_currency += difference
                continue
            notes.append(
                _(
                    "VAT %(tax)s: the e-invoice says %(xml)s, the bill %(bill)s; the "
                    "difference is more than rounding and was not corrected.",
                    tax=tax.display_name,
                    xml=format_amount(self.env, xml_amount, currency),
                    bill=format_amount(self.env, bill_amount, currency),
                )
            )
        return notes

    # ----------------------------------------------------------------------
    # Actions
    # ----------------------------------------------------------------------

    def action_create_partner(self):
        self.ensure_one()
        if self.direction != "received":
            raise UserError(_("Only a received e-invoice names a supplier to create."))
        party = self._read_party(self.attachment_id.raw, "NBan")
        partner = self.env["res.partner"].create(
            {
                "name": party["name"] or self.seller_name,
                "vat": party["vat"] or self.seller_vat,
                "street": party["street"] or False,
                "phone": party["phone"] or False,
                "email": party["email"] or False,
                "is_company": True,
                "country_id": self.env.ref("base.vn").id,
            }
        )
        if self.move_id.state == "draft" and not self.move_id.partner_id:
            self.move_id.partner_id = partner
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "res_id": partner.id,
            "views": [(False, "form")],
            "view_mode": "form",
        }

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
