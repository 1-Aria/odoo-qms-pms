# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation

from odoo import _, api, fields, models

from odoo.addons.l10n_vn_einvoice.models.l10n_vn_einvoice import (
    normalise_number,
    normalise_symbol,
    normalise_vat,
)

# --------------------------------------------------------------------------
# Parsing the list's text (design §5.4)
# --------------------------------------------------------------------------


def trim_number_text(value):
    """Stripped text, without a trailing ".0" ("25.0" -> "25")."""
    value = str(value or "").strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value


def parse_amount(value):
    """The amount as a float; empty is 0.0. Raises ValueError."""
    value = trim_number_text(value).replace(",", "")
    if not value:
        return 0.0
    try:
        return float(Decimal(value))
    except InvalidOperation as exc:
        raise ValueError(value) from exc


def parse_date(value):
    """dd/mm/yyyy, or yyyy-mm-dd with or without a time; empty is False.
    Raises ValueError."""
    value = str(value or "").strip()
    if not value:
        return False
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    raise ValueError(value)


def _fold(text):
    text = unicodedata.normalize("NFC", str(text or ""))
    return re.sub(r"\s+", " ", text).strip().casefold()


STATUS_KINDS = {
    _fold("Hóa đơn mới"): "new",
    _fold("Hóa đơn thay thế"): "replacing",
    _fold("Hóa đơn điều chỉnh"): "adjusting",
    _fold("Hóa đơn đã bị thay thế"): "replaced",
    _fold("Hóa đơn đã bị điều chỉnh"): "adjusted",
    _fold("Hóa đơn đã bị hủy"): "cancelled",
}


class RowError(Exception):
    """A row that cannot be grouped; its message goes to the row's error."""


class L10nVnEinvoicePortal(models.Model):
    _name = "l10n_vn.einvoice.portal"
    _description = "E-Invoice on the Portal"
    _order = "invoice_date, symbol, number, id"

    name = fields.Char(compute="_compute_name", store=True)
    batch_id = fields.Many2one(
        comodel_name="l10n_vn.einvoice.batch",
        string="Portal List",
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
    direction = fields.Selection(related="batch_id.direction", store=True)
    seller_vat = fields.Char(string="Seller Tax Code", index=True)
    form = fields.Char(index=True)
    symbol = fields.Char(index=True)
    number = fields.Char(index=True)
    invoice_date = fields.Date()
    seller_name = fields.Char(string="Seller")
    buyer_vat = fields.Char(string="Buyer Tax Code")
    buyer_name = fields.Char(string="Buyer")
    currency_id = fields.Many2one(comodel_name="res.currency")
    amount_untaxed = fields.Monetary(string="Untaxed Amount")
    amount_tax = fields.Monetary(string="VAT")
    amount_discount = fields.Monetary(string="Commercial Discount")
    amount_total = fields.Monetary(string="Total")
    status = fields.Char()
    status_kind = fields.Selection(
        selection=[
            ("new", "New"),
            ("replacing", "Replacing"),
            ("adjusting", "Adjusting"),
            ("replaced", "Replaced"),
            ("adjusted", "Adjusted"),
            ("cancelled", "Cancelled"),
            ("unknown", "Unknown"),
        ],
        string="Status Kind",
        compute="_compute_status_kind",
        store=True,
        index=True,
    )
    check_result = fields.Char()
    row_ids = fields.One2many(
        comodel_name="l10n_vn.einvoice.portal.row",
        inverse_name="invoice_id",
        string="Rows",
    )
    row_count = fields.Integer(string="Rows on the List")
    rows_disagree = fields.Boolean()

    _sql_constraints = [
        (
            "key_unique_per_batch",
            "unique(batch_id, seller_vat, form, symbol, number)",
            "An invoice appears once per list.",
        ),
    ]

    @api.depends("symbol", "number")
    def _compute_name(self):
        for invoice in self:
            invoice.name = f"{invoice.symbol or ''}-{invoice.number or ''}"

    @api.depends("status")
    def _compute_status_kind(self):
        for invoice in self:
            invoice.status_kind = STATUS_KINDS.get(_fold(invoice.status), "unknown")

    # ----------------------------------------------------------------------
    # Grouping
    # ----------------------------------------------------------------------

    @api.model
    def _parse_row(self, row, batch):
        """The values of one row, or RowError naming what does not parse."""
        key_parts = {
            "seller_vat": (normalise_vat(trim_number_text(row.col_seller_vat)), _("seller tax code")),
            "form": (trim_number_text(row.col_form), _("form")),
            "symbol": (normalise_symbol(row.col_symbol), _("symbol")),
            "number": (normalise_number(trim_number_text(row.col_number)), _("number")),
        }
        values = {}
        for field, (value, label) in key_parts.items():
            if not value:
                raise RowError(_("No %(column)s.", column=label))
            values[field] = value

        try:
            values["invoice_date"] = parse_date(row.col_date)
        except ValueError as exc:
            raise RowError(_("Unreadable date %(value)s.", value=row.col_date)) from exc

        amounts = {}
        for field, column, label in (
            ("amount_untaxed", "col_untaxed", _("untaxed amount")),
            ("amount_tax", "col_tax", _("VAT")),
            ("amount_discount", "col_discount", _("discount")),
            ("amount_total", "col_total", _("total")),
        ):
            try:
                amounts[field] = parse_amount(row[column])
            except ValueError as exc:
                raise RowError(
                    _(
                        "Unreadable amount %(value)s in %(column)s.",
                        value=row[column],
                        column=label,
                    )
                ) from exc
        if values["form"] == "2":
            # A sales invoice gives only its total (D12).
            amounts["amount_untaxed"] = amounts["amount_total"]
            amounts["amount_tax"] = 0.0
        values.update(amounts)

        currency_code = str(row.col_currency or "").strip()
        if currency_code:
            currency = self.env["res.currency"].search([("name", "=", currency_code)], limit=1)
            if not currency:
                raise RowError(_("Unknown currency %(value)s.", value=currency_code))
        else:
            currency = batch.company_id.currency_id
        values["currency_id"] = currency.id

        values.update(
            {
                "seller_name": (row.col_seller_name or "").strip() or False,
                "buyer_vat": normalise_vat(trim_number_text(row.col_buyer_vat)) or False,
                "buyer_name": (row.col_buyer_name or "").strip() or False,
                "status": (row.col_status or "").strip() or False,
                "check_result": (row.col_check or "").strip() or False,
            }
        )
        return values

    @api.model
    def _group_rows(self, batch):
        """One portal invoice per key; rows that do not parse keep their error
        (D10, D11, D13)."""
        batch.invoice_ids.unlink()
        groups = {}
        for row in batch.row_ids:
            try:
                values = self._parse_row(row, batch)
            except RowError as exc:
                row.write({"error": str(exc), "invoice_id": False})
                continue
            row.error = False
            key = (values["seller_vat"], values["form"], values["symbol"], values["number"])
            groups.setdefault(key, []).append((row, values))

        for items in groups.values():
            rows = self.env["l10n_vn.einvoice.portal.row"].concat(*(row for row, _values in items))
            values = dict(items[0][1])
            values.update({"batch_id": batch.id, "row_count": len(items)})
            if len(items) > 1:
                # Never summed by guess (design D7).
                for field in ("amount_untaxed", "amount_tax", "amount_discount", "amount_total"):
                    values[field] = 0.0
                values["rows_disagree"] = any(
                    (other["invoice_date"], _fold(other["status"]), _fold(other["check_result"]))
                    != (values["invoice_date"], _fold(values["status"]), _fold(values["check_result"]))
                    for _row, other in items[1:]
                )
            invoice = self.create(values)
            rows.write({"invoice_id": invoice.id})
        return True
