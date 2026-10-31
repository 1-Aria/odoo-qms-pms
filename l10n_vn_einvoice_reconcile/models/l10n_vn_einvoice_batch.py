# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import re
import unicodedata
from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_vn_einvoice.models.l10n_vn_einvoice import normalise_vat

from .l10n_vn_einvoice_portal import trim_number_text

# The cells read by the module itself (D4): the frame of both lists (design §4).
TITLE_CELL = "A3"
PERIOD_CELL = "A4"
CASH_REGISTER_MARK = "MÁY TÍNH TIỀN"

# The headers checked (D6), keyed by the row column they stand above. Both lists
# write them alike.
EXPECTED_HEADERS = {
    "col_form": ("header_form", "Ký hiệu mẫu số"),
    "col_symbol": ("header_symbol", "Ký hiệu hóa đơn"),
    "col_number": ("header_number", "Số hóa đơn"),
    "col_seller_vat": ("header_seller_vat", "MST người bán/MST người xuất hàng"),
    "col_buyer_vat": ("header_buyer_vat", "MST người mua/MST người nhận hàng"),
    "col_total": ("header_total", "Tổng tiền thanh toán"),
    "col_status": ("header_status", "Trạng thái hóa đơn"),
}

TEMPLATES = {
    "ordinary": "l10n_vn_einvoice_reconcile.xlsx_template_portal_list",
    "cash_register": "l10n_vn_einvoice_reconcile.xlsx_template_cash_register_list",
}


def fold(text):
    """Text compared regardless of Unicode form, case and spacing (D9)."""
    text = unicodedata.normalize("NFC", str(text or ""))
    return re.sub(r"\s+", " ", text).strip().casefold()


class L10nVnEinvoiceBatch(models.Model):
    _name = "l10n_vn.einvoice.batch"
    _description = "E-Invoice Portal List"
    _inherit = ["mail.thread"]
    _order = "date_from desc, id desc"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    direction = fields.Selection(
        selection=[("purchase", "Purchases"), ("sale", "Sales")],
        required=True,
        default="purchase",
        tracking=True,
    )
    list_kind = fields.Selection(
        selection=[("ordinary", "Ordinary"), ("cash_register", "Cash register")],
        string="List",
        required=True,
        default="ordinary",
        tracking=True,
    )
    template_id = fields.Many2one(
        comodel_name="xlsx.template",
        string="Template",
        required=True,
        compute="_compute_template_id",
        store=True,
        readonly=False,
        # Required and computed: computed before the INSERT, as core does for the
        # move's date (account/models/account_move.py:145).
        precompute=True,
        domain="[('res_model', '=', 'l10n_vn.einvoice.batch')]",
        ondelete="restrict",
    )
    filename = fields.Char(string="Imported File", readonly=True, copy=False)
    import_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    list_title = fields.Char(readonly=True, copy=False)
    period_text = fields.Char(string="Period", readonly=True, copy=False)
    header_form = fields.Char(readonly=True, copy=False)
    header_symbol = fields.Char(readonly=True, copy=False)
    header_number = fields.Char(readonly=True, copy=False)
    header_seller_vat = fields.Char(readonly=True, copy=False)
    header_buyer_vat = fields.Char(readonly=True, copy=False)
    header_total = fields.Char(readonly=True, copy=False)
    header_status = fields.Char(readonly=True, copy=False)
    date_from = fields.Date(compute="_compute_period", store=True)
    date_to = fields.Date(compute="_compute_period", store=True)
    row_ids = fields.One2many(
        comodel_name="l10n_vn.einvoice.portal.row",
        inverse_name="batch_id",
        string="Rows",
    )
    invoice_ids = fields.One2many(
        comodel_name="l10n_vn.einvoice.portal",
        inverse_name="batch_id",
        string="Invoices",
    )
    row_count = fields.Integer(compute="_compute_counts")
    invoice_count = fields.Integer(compute="_compute_counts")
    error_count = fields.Integer(string="Rows with Errors", compute="_compute_counts")

    @api.depends("direction", "list_kind", "date_from", "date_to")
    def _compute_name(self):
        directions = dict(self._fields["direction"].selection)
        for batch in self:
            label = directions.get(batch.direction, "")
            if batch.list_kind == "cash_register":
                label = _("%(direction)s (cash register)", direction=label)
            if batch.date_from and batch.date_to:
                batch.name = "%s %s – %s" % (
                    label,
                    batch.date_from.strftime("%d/%m/%Y"),
                    batch.date_to.strftime("%d/%m/%Y"),
                )
            else:
                batch.name = _("%(list)s (not imported)", list=label)

    @api.depends("list_kind")
    def _compute_template_id(self):
        for batch in self:
            batch.template_id = self.env.ref(
                TEMPLATES.get(batch.list_kind, TEMPLATES["ordinary"]),
                raise_if_not_found=False,
            )

    @api.depends("period_text")
    def _compute_period(self):
        for batch in self:
            dates = re.findall(r"\d{2}/\d{2}/\d{4}", batch.period_text or "")
            batch.date_from = batch.date_to = False
            if len(dates) >= 2:
                try:
                    batch.date_from = fields.Date.to_date(
                        "-".join(reversed(dates[0].split("/")))
                    )
                    batch.date_to = fields.Date.to_date("-".join(reversed(dates[1].split("/"))))
                except ValueError:
                    batch.date_from = batch.date_to = False

    @api.depends("row_ids", "row_ids.error", "invoice_ids")
    def _compute_counts(self):
        for batch in self:
            batch.row_count = len(batch.row_ids)
            batch.invoice_count = len(batch.invoice_ids)
            batch.error_count = len(batch.row_ids.filtered("error"))

    # ----------------------------------------------------------------------
    # Import
    # ----------------------------------------------------------------------

    def action_import(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_vn_einvoice_reconcile.l10n_vn_einvoice_batch_import_action"
        )
        action["context"] = {"default_batch_id": self.id}
        return action

    def _import_file(self, content_b64, filename):
        """Read the portal's list into rows and portal invoices. The file is
        not kept (D1). Every refusal raises, which rolls the import back."""
        self.ensure_one()
        self._check_layout(self._read_layout(content_b64))
        self.env["xlsx.import"].import_xlsx(
            content_b64, self.template_id, self._name, self.id
        )
        self.invalidate_recordset()
        self._check_company_side()
        self.env["l10n_vn.einvoice.portal"]._group_rows(self)
        self.write({"filename": filename, "import_date": fields.Datetime.now()})
        self.message_post(
            body=_(
                "Imported %(file)s: %(rows)s rows, %(invoices)s invoices, %(errors)s "
                "rows with errors.",
                file=filename,
                rows=self.row_count,
                invoices=self.invoice_count,
                errors=self.error_count,
            )
        )
        return True

    def _template_columns(self):
        """The cell of each row column in the template's instruction."""
        self.ensure_one()
        instruction = literal_eval((self.template_id.instruction or "{}").strip())
        sheets = instruction.get("__IMPORT__", {})
        for sheet in sheets.values():
            for row_field, cells in sheet.items():
                if row_field.replace("_NODEL_", "") == "row_ids":
                    return {field: cell for cell, field in cells.items()}
        return {}

    def _read_layout(self, content_b64):
        """The title, period and checked header cells, read with openpyxl.
        excel_import_export cannot read head cells from an .xlsx: it passes the
        cell's value where its converter reads .value
        (excel_import_export/models/xlsx_import.py:209, models/common.py:301)."""
        from openpyxl import load_workbook

        self.ensure_one()
        try:
            workbook = load_workbook(io.BytesIO(base64.b64decode(content_b64)), data_only=True)
        except Exception as exc:
            raise UserError(_("The file is not an Excel (.xlsx) workbook.")) from exc
        sheet = workbook.worksheets[0]
        columns = self._template_columns()
        layout = {
            "title": sheet[TITLE_CELL].value,
            "period": sheet[PERIOD_CELL].value,
            "headers": {},
        }
        for column, (field, _expected) in EXPECTED_HEADERS.items():
            cell = columns.get(column)
            if not cell:
                raise UserError(
                    _(
                        "The template %(template)s has no cell for %(column)s.",
                        template=self.template_id.name,
                        column=column,
                    )
                )
            letters, row = re.match(r"([A-Z]+)(\d+)", cell.upper()).groups()
            header_cell = f"{letters}{int(row) - 1}"
            layout["headers"][field] = (header_cell, sheet[header_cell].value)
        workbook.close()
        return layout

    def _check_layout(self, layout):
        """D5, D6: the title fits the batch's list, the headers the template."""
        self.ensure_one()
        title = str(layout["title"] or "").strip()
        is_cash_register = fold(CASH_REGISTER_MARK) in fold(title)
        if self.list_kind == "ordinary" and is_cash_register:
            raise UserError(
                _(
                    "This is the cash-register list (%(title)s). Set the list to Cash "
                    "register and import it again.",
                    title=title,
                )
            )
        if self.list_kind == "cash_register" and not is_cash_register:
            raise UserError(
                _(
                    "This is not the cash-register list (%(title)s). Set the list to "
                    "Ordinary and import it again.",
                    title=title or "?",
                )
            )
        values = {
            "list_title": title or False,
            "period_text": str(layout["period"] or "").strip() or False,
        }
        for _column, (field, expected) in EXPECTED_HEADERS.items():
            cell, found = layout["headers"][field]
            found = str(found or "").strip()
            if fold(found) != fold(expected):
                raise UserError(
                    _(
                        "The list's columns do not match the template: %(cell)s holds "
                        "%(found)s, where %(expected)s was expected. Check the template's "
                        "instruction.",
                        cell=cell,
                        found=found or _("nothing"),
                        expected=expected,
                    )
                )
            values[field] = found
        self.write(values)

    def _check_company_side(self):
        """D7: every row's tax code on the company's side is the company's."""
        self.ensure_one()
        company_vat = normalise_vat(self.company_id.vat)
        column = "col_buyer_vat" if self.direction == "purchase" else "col_seller_vat"
        directions = dict(self._fields["direction"].selection)
        for row in self.row_ids:
            vat = normalise_vat(trim_number_text(row[column]))
            if vat and vat != company_vat:
                raise UserError(
                    _(
                        "Row %(row)s names %(vat)s on the company's side, but %(company)s "
                        "has tax code %(company_vat)s. Is this %(company)s's %(direction)s "
                        "list?",
                        row=row.col_stt or row.id,
                        vat=vat,
                        company=self.company_id.name,
                        company_vat=self.company_id.vat or "?",
                        direction=directions[self.direction].lower(),
                    )
                )
