# l10n_vn_einvoice_reconcile

The tax portal's lists of invoices imported into Odoo and checked against the e-invoices: one batch
per imported list, the list's rows kept as imported, grouped into one portal invoice per legal
invoice, then matched to the e-invoices of `l10n_vn_einvoice`. Step 1 imports and groups both lists,
the ordinary one and the cash-register one; step 2 matches. Design:
`docs/Accounting/VN E-Invoice Reconciliation — Design.md`. Base module: `docs/modules/l10n_vn_einvoice.md`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `l10n_vn.einvoice.batch`, `l10n_vn.einvoice.portal.row`, `l10n_vn.einvoice.portal`; the import dialog `l10n_vn.einvoice.batch.import`; the templates for the ordinary list (*DANH SÁCH HÓA ĐƠN*) and the cash-register list (*DANH SÁCH HÓA ĐƠN MÁY TÍNH TIỀN*); the title, header and company checks; normalisation and grouping into portal invoices; status reading; access, record rules, views, menu | done | 2026-10-31, two runs. First: `-i`, 13 tests, all erroring on the insert of a batch: `template_id`, required and computed, was computed after the insert without `precompute=True`; fixed. Second: `-u`, `exit=0`, 13 tests, 0 failures; UI checked: the October purchase list (14 invoices, `C26TMX-41` untaxed = total, VAT 0), the April sales list with its replaced and adjusted invoices, the purchase file refused on a sales list, a non-administrator seeing no *Import*. Then opened to accountants (D14, Peter): the access below, the *Import* button and the menu, `col_citizen_id` without groups, `test_access` rewritten; to be confirmed by the next run |
| 2 | Matching portal invoices to e-invoices: `einvoice_id`, `match_state`, the differences; *Match again*; the Odoo-only smart buttons; `portal_ids` on the e-invoice | planned | |
| 3 | Summing an invoice spread over several rows (design O2) | planned | |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §7: grouping in step 2 with matching | grouping in step 1, with the import | A portal invoice is what every view and the matching show; an import that left only rows would have nothing to look at |
| 2 | §5.1 says nothing of checking the file | the import refuses a file whose title, header cells or tax codes do not fit its batch (D5–D7) | `excel_import_export` reads by position: the other list's layout, a changed layout or another company's list would be read without complaint into the wrong fields |
| 3 | §5.3 says nothing of a multi-row invoice's amounts | they are stored as 0, with `row_count` above 1 (D10) | The design never sums or guesses them (D7 there); storing the first row's would read as an invoice amount |

## Decisions

| # | Decision |
|---|---|
| D1 | **The file passes through an import dialog and is not kept** (design D5): `l10n_vn.einvoice.batch.import` holds it in a database column (`attachment=False`), so it never becomes an attachment, and Odoo's vacuum of transient records removes it. The batch keeps the filename, the import date and the rows, which hold every cell of the list (Peter, 2026-10-31) |
| D2 | **The dialog runs the importer itself:** `xlsx.import.import_xlsx(file, template, batch model, batch id)` (`oca/server-tools/excel_import_export/models/xlsx_import.py:356-378`), the file read with `bin_size=False` (`l10n_vn_einvoice` spec, `_file_content`). OCA's import wizard keeps no copy of the file either and is not used |
| D3 | **Every column is imported into a Char field** (design D4). Through `excel_import_export` and `base_import`, a number cell reaches a text field as its integer text when whole (`5411000`) and its float text otherwise (`base_import/models/base_import.py:472-478`); a 0 arrives empty (`excel_import_export/models/common.py:306-309`). The module parses the text |
| D4 | **Two templates, data with `noupdate="1"`,** each created from an `input_instruction` (`excel_import_export/models/xlsx_template.py:313-360` builds the import lines from it), the sheet named by index, `1` (`xlsx_template.py:385`, `xlsx_import.py:192-197`). No sample file is shipped: the import reads only the instruction. The cash-register template follows Peter's recreation of that list, whose values match the official exports; a header that turns out different on the first official file is refused by D6 and its expected text corrected |
| D5 | **The batch's layout picks its template** (`list_kind`), and **the title must fit it:** a title holding *MÁY TÍNH TIỀN* is the cash-register list, refused on an ordinary batch; a cash-register batch refuses a title without it |
| D6 | **Seven header cells are checked** against the expected headers (form, symbol, number, seller tax code, buyer tax code, total, status), compared after Unicode NFC and case folding. A mismatch is refused, naming the cell, what it holds and what was expected. The template's instruction names the cells, so an edited layout moves the check with it; the expected texts are the same in both lists |
| D7 | **The list must belong to the batch's company and direction:** every row's buyer tax code (purchases) or seller tax code (sales) is the company's, normalised; any other is refused, naming it. A wrong company's list or a sales list imported as purchases cannot pass |
| D8 | **Normalisation reuses the base module's helpers** (`normalise_vat`, `normalise_symbol`, `normalise_number` from `odoo.addons.l10n_vn_einvoice.models.l10n_vn_einvoice`), after a trailing `.0` is trimmed (design §5.4) |
| D9 | **Texts are compared in Unicode NFC.** Vietnamese can be written precomposed or decomposed; the statuses, titles and headers are matched after `unicodedata.normalize("NFC", …)` |
| D10 | **Grouping by key, never summing** (design D7): one portal invoice per normalised seller tax code + form + symbol + number in the batch; a single row gives its values; several rows give their shared values from the first row, amounts 0, `row_count` the number, and `rows_disagree` when date, status or check result differ |
| D11 | **A row whose key does not parse is kept and named,** not grouped: its `error` says which value, and the batch counts it |
| D12 | **Form 2 reads untaxed = total, VAT = 0** (design D12), whatever its untaxed and VAT cells hold |
| D13 | **Re-importing replaces rows and portal invoices** (design D11): `excel_import_export` deletes the batch's rows before loading (`xlsx_import.py:80-96`), and the grouping deletes the portal invoices before creating them again |
| D14 | **Accountants import** (Peter, 2026-10-31): importing creates only review records and replaces only the list's own rows, so `account.group_account_user` reads, creates and edits lists and imports them, and holds every right on rows and portal invoices, which re-importing deletes; `account.group_account_readonly` reads; `account.group_account_manager` also deletes lists. Record rules by company. `col_citizen_id` carries no `groups`: the import writes every column, and a field outside the user's groups cannot be written. On the cash-register purchase lists the company is the buyer, so the column stays empty in practice |
| D15 | **The title, the period and the header cells are read by the module with `openpyxl`,** before anything is imported, not through the template's `_HEAD_`: for an `.xlsx`, `excel_import_export` passes a head cell's *value* to its converter (`excel_import_export/models/xlsx_import.py:209`), which reads `.value` from it (`models/common.py:301`), so every head cell arrives empty. Rows are passed the cell itself and work. Each checked header is the cell above its column's first data cell in the template's `row_ids` mapping, so an edited layout still moves its check (D6) |

## Folder structure

```
l10n_vn_einvoice_reconcile/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── l10n_vn_einvoice_batch.py
│   ├── l10n_vn_einvoice_portal_row.py
│   └── l10n_vn_einvoice_portal.py
├── wizard/
│   ├── __init__.py
│   ├── l10n_vn_einvoice_batch_import.py
│   └── l10n_vn_einvoice_batch_import_views.xml
├── data/xlsx_template.xml
├── security/
│   ├── ir.model.access.csv
│   └── l10n_vn_einvoice_reconcile_security.xml
├── views/
│   ├── l10n_vn_einvoice_batch_views.xml
│   ├── l10n_vn_einvoice_portal_views.xml
│   └── menus.xml
├── tests/
│   ├── __init__.py, common.py
│   └── test_l10n_vn_einvoice_import.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - E-Invoice Reconciliation` |
| `summary` | `The tax portal's invoice lists imported and checked against the e-invoices in Odoo` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Accounting/Localizations` |
| `countries` | `["vn"]` |
| `depends` | `l10n_vn_einvoice`, `excel_import_export` |
| `external_dependencies` | `{"python": ["openpyxl"]}` (D15) |
| `data` | `security/l10n_vn_einvoice_reconcile_security.xml`, `security/ir.model.access.csv`, `data/xlsx_template.xml`, `wizard/l10n_vn_einvoice_batch_import_views.xml`, `views/l10n_vn_einvoice_portal_views.xml`, `views/l10n_vn_einvoice_batch_views.xml`, `views/menus.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models`, `from . import wizard` |
| `models/__init__.py` | `from . import l10n_vn_einvoice_batch`, `from . import l10n_vn_einvoice_portal_row`, `from . import l10n_vn_einvoice_portal` |
| `wizard/__init__.py` | `from . import l10n_vn_einvoice_batch_import` |
| `tests/__init__.py` | `from . import test_l10n_vn_einvoice_import` |

## Access — `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_l10n_vn_einvoice_batch_readonly` | `model_l10n_vn_einvoice_batch` | `account.group_account_readonly` | 1 | 0 | 0 | 0 |
| `access_l10n_vn_einvoice_batch_user` | `model_l10n_vn_einvoice_batch` | `account.group_account_user` | 1 | 1 | 1 | 0 |
| `access_l10n_vn_einvoice_batch_manager` | `model_l10n_vn_einvoice_batch` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_portal_row_readonly` | `model_l10n_vn_einvoice_portal_row` | `account.group_account_readonly` | 1 | 0 | 0 | 0 |
| `access_l10n_vn_einvoice_portal_row_user` | `model_l10n_vn_einvoice_portal_row` | `account.group_account_user` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_portal_row_manager` | `model_l10n_vn_einvoice_portal_row` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_portal_readonly` | `model_l10n_vn_einvoice_portal` | `account.group_account_readonly` | 1 | 0 | 0 | 0 |
| `access_l10n_vn_einvoice_portal_user` | `model_l10n_vn_einvoice_portal` | `account.group_account_user` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_portal_manager` | `model_l10n_vn_einvoice_portal` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_batch_import_user` | `model_l10n_vn_einvoice_batch_import` | `account.group_account_user` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_batch_import_manager` | `model_l10n_vn_einvoice_batch_import` | `account.group_account_manager` | 1 | 1 | 1 | 1 |

D14. *Administrator* implies only *Invoicing* (`account/security/account_security.xml:78-82`), so it has
rows of its own; on this instance the administrators also hold *Accountant* and *Read-only*.
`xlsx.template` is readable and writable by every internal user
(`excel_import_export/security/ir.model.access.csv:2-4`); `base_import.import` by every internal user
(core).

## Record rules — `security/l10n_vn_einvoice_reconcile_security.xml`

| XML id | Model | Domain | Global |
|---|---|---|---|
| `l10n_vn_einvoice_batch_company_rule` | `model_l10n_vn_einvoice_batch` | `[('company_id', 'in', company_ids)]` | yes |
| `l10n_vn_einvoice_portal_row_company_rule` | `model_l10n_vn_einvoice_portal_row` | `[('company_id', 'in', company_ids)]` | yes |
| `l10n_vn_einvoice_portal_company_rule` | `model_l10n_vn_einvoice_portal` | `[('company_id', 'in', company_ids)]` | yes |

## Data — `data/xlsx_template.xml`

`<odoo noupdate="1">`, two `xlsx.template` records, both with `res_model`
`l10n_vn.einvoice.batch`. Their instructions map the rows only; the title, period and header row are
read by the module (D15).

| XML id | `name` | `description` |
|---|---|---|
| `xlsx_template_portal_list` | `GDT portal invoice list (DANH SÁCH HÓA ĐƠN)` | `The portal's ordinary list of sales or purchase invoices: title in A3, period in A4, headers on row 6, data from row 7 (design §4)` |
| `xlsx_template_cash_register_list` | `GDT portal cash-register invoice list (DANH SÁCH HÓA ĐƠN MÁY TÍNH TIỀN)` | `The portal's list of invoices issued from cash registers, same frame; laid out from a recreation, to be checked against the first official file` |

**`xlsx_template_portal_list`**, `input_instruction`:

```python
{
    "__IMPORT__": {
        1: {
            "row_ids": {
                "A7": "col_stt",
                "B7": "col_form",
                "C7": "col_symbol",
                "D7": "col_number",
                "E7": "col_date",
                "F7": "col_seller_vat",
                "G7": "col_seller_name",
                "H7": "col_buyer_vat",
                "I7": "col_buyer_name",
                "J7": "col_buyer_address",
                "K7": "col_untaxed",
                "L7": "col_tax",
                "M7": "col_discount",
                "N7": "col_fees",
                "O7": "col_total",
                "P7": "col_currency",
                "Q7": "col_rate",
                "R7": "col_status",
                "S7": "col_check",
            },
        },
    },
}
```

**`xlsx_template_cash_register_list`**, `input_instruction`:

```python
{
    "__IMPORT__": {
        1: {
            "row_ids": {
                "A7": "col_stt",
                "B7": "col_form",
                "C7": "col_symbol",
                "D7": "col_number",
                "E7": "col_date",
                "F7": "col_seller_vat",
                "G7": "col_seller_name",
                "H7": "col_seller_address",
                "I7": "col_buyer_vat",
                "J7": "col_buyer_name",
                "K7": "col_citizen_id",
                "L7": "col_untaxed",
                "M7": "col_tax",
                "N7": "col_discount",
                "O7": "col_total",
                "P7": "col_status",
                "Q7": "col_check",
            },
        },
    },
}
```

## Models

### `l10n_vn.einvoice.batch` — `models/l10n_vn_einvoice_batch.py`

`_name = "l10n_vn.einvoice.batch"`, `_description = "E-Invoice Portal List"`, `_inherit = ["mail.thread"]`,
`_order = "date_from desc, id desc"`, `_check_company_auto = True`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `compute="_compute_name"`, `store=True` |
| `company_id` | Many2one → `res.company` | `required=True`, `index=True`, `default=lambda self: self.env.company` |
| `direction` | Selection `[("purchase", "Purchases"), ("sale", "Sales")]` | `required=True`, `default="purchase"`, `tracking=True` |
| `list_kind` | Selection `[("ordinary", "Ordinary"), ("cash_register", "Cash register")]` | `string="List"`, `required=True`, `default="ordinary"`, `tracking=True` (D5) |
| `template_id` | Many2one → `xlsx.template` | `string="Template"`, `required=True`, `compute="_compute_template_id"`, `store=True`, `readonly=False`, `precompute=True` (required and computed, so computed before the insert, as `account/models/account_move.py:145`), `domain="[('res_model', '=', 'l10n_vn.einvoice.batch')]"`, `ondelete="restrict"` |
| `filename` | Char | `string="Imported File"`, `readonly=True`, `copy=False` (D1) |
| `import_date` | Datetime | `readonly=True`, `copy=False`, `tracking=True` |
| `list_title`, `period_text` | Char | `readonly=True`, `copy=False` — A3, A4, read by `_read_layout` (D15) |
| `header_form`, `header_symbol`, `header_number`, `header_seller_vat`, `header_buyer_vat`, `header_total`, `header_status` | Char | `readonly=True`, `copy=False` — the checked header cells as found (D6, D15) |
| `date_from`, `date_to` | Date | `compute="_compute_period"`, `store=True` — the two `dd/mm/yyyy` dates in `period_text`, else empty |
| `row_ids` | One2many → `l10n_vn.einvoice.portal.row` | inverse `batch_id` |
| `invoice_ids` | One2many → `l10n_vn.einvoice.portal` | inverse `batch_id` |
| `row_count`, `invoice_count`, `error_count` | Integer | `compute="_compute_counts"` — rows, portal invoices, rows with an `error` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_name` | `@api.depends("direction", "list_kind", "date_from", "date_to")` | `"Purchases 01/10/2026 – 31/10/2026"`, the direction's label, *(cash register)* after it for that list, and the period in `dd/mm/yyyy`; without a period, `"Purchases (not imported)"` |
| `_compute_template_id` | `@api.depends("list_kind")` | the kind's template, `env.ref(..., raise_if_not_found=False)`: `xlsx_template_portal_list` or `xlsx_template_cash_register_list` |
| `_compute_period` | `@api.depends("period_text")` | the first two `\d{2}/\d{2}/\d{4}` of `period_text`, parsed day-first |
| `_compute_counts` | `@api.depends("row_ids", "row_ids.error", "invoice_ids")` | the three counts |
| `action_import` | — | `ensure_one`; the dialog's action (`l10n_vn_einvoice_reconcile.l10n_vn_einvoice_batch_import_action`, read with `_for_xml_id`), `context` `{"default_batch_id": self.id}` |
| `_import_file` | — | `_import_file(content_b64, filename)`: `_check_layout(_read_layout(content_b64))`; the importer (D2); `_check_company_side`; `_group_rows` (on the portal invoice model); `filename`, `import_date` = now; a message `"Imported %(file)s: %(rows)s rows, %(invoices)s invoices, %(errors)s rows with errors."` |
| `_template_columns` | — | the `{field: cell}` of the template's `row_ids` mapping, read from its `instruction` |
| `_read_layout` | — | `_read_layout(content_b64)` → the A3 title, the A4 period and, for each checked column, `(header cell, its value)` — the cell above the column's cell in `_template_columns` (D15). A file `openpyxl` cannot open: `"The file is not an Excel (.xlsx) workbook."`; a template without a checked column: `"The template %(template)s has no cell for %(column)s."` |
| `_check_layout` | — | `_check_layout(layout)`: D5, D6; writes `list_title`, `period_text` and the `header_*` fields; refusals below |
| `_check_company_side` | — | D7: the tax codes of the rows without an `error` on the company's side — `col_buyer_vat` for purchases, `col_seller_vat` for sales, through `normalise_vat` after the `.0` trim — each equal to `normalise_vat(company_id.vat)`; the first other refused |

The checks run after the importer, in the same transaction: a refusal rolls the whole import back.

**Expected headers** (D6), the module-level `EXPECTED_HEADERS` in `l10n_vn_einvoice_batch.py`, keyed by
the row column each stands above (`col_form` → `header_form`, …); texts compared through `fold`
(NFC, whitespace collapsed, case folded, D9):

| Field | Header |
|---|---|
| `header_form` | `Ký hiệu mẫu số` |
| `header_symbol` | `Ký hiệu hóa đơn` |
| `header_number` | `Số hóa đơn` |
| `header_seller_vat` | `MST người bán/MST người xuất hàng` |
| `header_buyer_vat` | `MST người mua/MST người nhận hàng` |
| `header_total` | `Tổng tiền thanh toán` |
| `header_status` | `Trạng thái hóa đơn` |

**Refusals**, `UserError`:

| Case | Message |
|---|---|
| A cash-register title on an ordinary batch (D5) | `"This is the cash-register list (%(title)s). Set the list to Cash register and import it again."` |
| Another title on a cash-register batch (D5) | `"This is not the cash-register list (%(title)s). Set the list to Ordinary and import it again."` |
| A header cell (D6) | `"The list's columns do not match the template: %(cell)s holds %(found)s, where %(expected)s was expected. Check the template's instruction."` — the cell's reference, `R6` for the status |
| Another company or direction (D7) | `"Row %(row)s names %(vat)s on the company's side, but %(company)s has tax code %(company_vat)s. Is this %(company)s's %(direction)s list?"` |

### `l10n_vn.einvoice.portal.row` — `models/l10n_vn_einvoice_portal_row.py`

`_name = "l10n_vn.einvoice.portal.row"`, `_description = "E-Invoice Portal List Row"`,
`_order = "batch_id, id"`

| Field | Type | Attributes |
|---|---|---|
| `batch_id` | Many2one → `l10n_vn.einvoice.batch` | `required=True`, `ondelete="cascade"`, `index=True` |
| `company_id` | Many2one → `res.company` | `related="batch_id.company_id"`, `store=True`, `index=True` |
| `col_stt` … `col_check` | Char | the columns of both instructions, as imported (D3): `col_stt`, `col_form`, `col_symbol`, `col_number`, `col_date`, `col_seller_vat`, `col_seller_name`, `col_seller_address`, `col_buyer_vat`, `col_buyer_name`, `col_buyer_address`, `col_citizen_id`, `col_untaxed`, `col_tax`, `col_discount`, `col_fees`, `col_total`, `col_currency`, `col_rate`, `col_status`, `col_check`; strings the headers' English names (design §4). No `groups` on any of them (D14) |
| `invoice_id` | Many2one → `l10n_vn.einvoice.portal` | `string="Portal Invoice"`, `ondelete="set null"`, `index=True` |
| `error` | Char | why the row is not grouped (D11) |

### `l10n_vn.einvoice.portal` — `models/l10n_vn_einvoice_portal.py`

`_name = "l10n_vn.einvoice.portal"`, `_description = "E-Invoice on the Portal"`,
`_order = "invoice_date, symbol, number, id"`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `compute="_compute_name"`, `store=True` — `<symbol>-<number>`, as the e-invoice's |
| `batch_id` | Many2one → `l10n_vn.einvoice.batch` | `required=True`, `ondelete="cascade"`, `index=True` |
| `company_id` | Many2one → `res.company` | `related="batch_id.company_id"`, `store=True`, `index=True` |
| `direction` | Selection | `related="batch_id.direction"`, `store=True` |
| `seller_vat`, `form`, `symbol`, `number` | Char | the normalised key (D8), `index=True` |
| `invoice_date` | Date | |
| `seller_name`, `buyer_vat`, `buyer_name` | Char | |
| `currency_id` | Many2one → `res.currency` | the active currency named in the row; the company's when the row names none (the cash-register list has no currency column) |
| `amount_untaxed`, `amount_tax`, `amount_discount`, `amount_total` | Monetary | 0 for an invoice on several rows (D10) |
| `status` | Char | as written |
| `status_kind` | Selection `[("new", "New"), ("replacing", "Replacing"), ("adjusting", "Adjusting"), ("replaced", "Replaced"), ("adjusted", "Adjusted"), ("cancelled", "Cancelled"), ("unknown", "Unknown")]` | `compute="_compute_status_kind"`, `store=True`, `index=True` |
| `check_result` | Char | as written |
| `row_ids` | One2many → `l10n_vn.einvoice.portal.row` | inverse `invoice_id` |
| `row_count` | Integer | number of rows, stored at grouping |
| `rows_disagree` | Boolean | several rows differing on date, status or check result (D10) |

| SQL constraint | Definition | Message |
|---|---|---|
| `key_unique_per_batch` | `unique(batch_id, seller_vat, form, symbol, number)` | `An invoice appears once per list.` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_name` | `@api.depends("symbol", "number")` | `f"{symbol}-{number}"` |
| `_compute_status_kind` | `@api.depends("status")` | the table below, after NFC and case folding (D9) |
| `_parse_row` | `@api.model` | `_parse_row(row, batch)` → the portal invoice's values by the table below, or `RowError` (a module-level exception) with the error text |
| `_group_rows` | `@api.model` | `_group_rows(batch)`: the batch's portal invoices deleted (D13); each row parsed (below), a failure written to its `error`; the parsed rows grouped by key, one portal invoice per group created with its values (D10) and the rows' `invoice_id` set |

**Statuses** (design §5.5):

| Status | `status_kind` |
|---|---|
| *Hóa đơn mới* | `new` |
| *Hóa đơn thay thế* | `replacing` |
| *Hóa đơn điều chỉnh* | `adjusting` |
| *Hóa đơn đã bị thay thế* | `replaced` |
| *Hóa đơn đã bị điều chỉnh* | `adjusted` |
| *Hóa đơn đã bị hủy* | `cancelled` |
| anything else | `unknown` |

**Parsing a row** — module-level helpers in `l10n_vn_einvoice_portal.py`:

| Helper | Behaviour |
|---|---|
| `trim_number_text(value)` | stripped; a trailing `.0` removed (`"25.0"` → `"25"`); empty → `""` |
| `parse_amount(value)` | `trim_number_text`, then `Decimal`, as a float; empty → 0.0; unparseable raises `ValueError` |
| `parse_date(value)` | `dd/mm/yyyy`; also `yyyy-mm-dd` with or without a time; unparseable raises `ValueError` |

| Value | From | Error when |
|---|---|---|
| key | `col_seller_vat`, `col_form`, `col_symbol`, `col_number` through `trim_number_text` and the base module's helpers (D8) | any part empty: `"No %(column)s."` — *seller tax code*, *form*, *symbol*, *number* |
| `invoice_date` | `col_date` by `parse_date`; empty: none | unparseable: `"Unreadable date %(value)s."` |
| amounts | `col_untaxed`, `col_tax`, `col_discount`, `col_total` by `parse_amount`; form 2: untaxed = total, VAT = 0 (D12) | unparseable: `"Unreadable amount %(value)s in %(column)s."` |
| `currency_id` | `col_currency`, searched by `name`; empty: the company's currency | none active: `"Unknown currency %(value)s."` |
| `buyer_vat` | `col_buyer_vat` through `trim_number_text` and `normalise_vat` | — |
| names, status, check result | as written, stripped | — |

### `l10n_vn.einvoice.batch.import` — `wizard/l10n_vn_einvoice_batch_import.py`

`_name = "l10n_vn.einvoice.batch.import"`, `_description = "Import a Portal List"` (TransientModel)

| Field | Type | Attributes |
|---|---|---|
| `batch_id` | Many2one → `l10n_vn.einvoice.batch` | `required=True`, `readonly=True`, `ondelete="cascade"` |
| `list_kind` | Selection | `related="batch_id.list_kind"` |
| `file` | Binary | `string="Portal List (.xlsx)"`, `required=True`, `attachment=False` (D1) |
| `filename` | Char | |

| Method | Behaviour |
|---|---|
| `action_import` | `ensure_one`; `batch_id._import_file(self.with_context(bin_size=False, bin_size_file=False).file, self.filename or "portal.xlsx")`; returns `{"type": "ir.actions.act_window_close"}` |

## Views — `views/l10n_vn_einvoice_portal_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_einvoice_portal_view_list` | list | `create="0"`: `name`, `invoice_date`, `seller_name`, `seller_vat`, `buyer_name` (optional hide), `buyer_vat` (optional hide), `amount_untaxed`, `amount_tax`, `amount_total`, `currency_id` (column invisible), `status_kind` (badge: `decoration-danger` for `replaced`, `adjusted`, `cancelled`, `unknown`), `row_count` (optional hide), `batch_id` (optional hide) |
| `l10n_vn_einvoice_portal_view_form` | form | `create="0"`, `edit="0"`; title `name`; group *Invoice*: `seller_vat`, `form`, `symbol`, `number`, `invoice_date`, `seller_name`, `buyer_vat`, `buyer_name`; group *Amounts*: the four amounts, `currency_id`; group *Status*: `status`, `status_kind`, `check_result`; an `alert-warning`, `invisible="row_count < 2"`: *This invoice spans several rows of the list; its amounts are not compared.*; an `alert-warning`, `invisible="not rows_disagree"`: *Its rows disagree on date, status or check result.*; a page *Rows* listing `row_ids` |
| `l10n_vn_einvoice_portal_view_search` | search | `name`, `seller_vat`, `seller_name`, `buyer_vat`; filters by `status_kind` (*Replaced*, *Adjusted*, *Cancelled*, *Unknown status*) and *Several rows* (`row_count > 1`); group by `status_kind`, `seller_name`, `batch_id` |
| `l10n_vn_einvoice_portal_row_view_list` | list | `create="0"`, `edit="0"`: the row's columns (the less used ones `optional="hide"`), `invoice_id`, `error` (`decoration-danger="error"`) |

## Views — `views/l10n_vn_einvoice_batch_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_einvoice_batch_view_list` | list | `name`, `direction`, `list_kind`, `date_from`, `date_to`, `import_date`, `invoice_count`, `error_count`, `company_id` (`groups="base.group_multi_company"`) |
| `l10n_vn_einvoice_batch_view_form` | form | header: button *Import* (`action_import`, `type="object"`, `class="btn-primary"`, `groups="account.group_account_user,account.group_account_manager"`, `invisible="not id"`). Sheet: title `name`; group: `direction`, `list_kind`, `company_id` (`groups="base.group_multi_company"`), `template_id`; group *Imported*: `filename`, `import_date`, `list_title`, `period_text`, `date_from`, `date_to`, `row_count`, `invoice_count`, `error_count`; notebook: *Invoices* (`invoice_ids`, the portal list view), *Rows* (`row_ids`, the row list view). Chatter |
| `l10n_vn_einvoice_batch_view_search` | search | `name`; filters *Purchases*, *Sales*, *Cash register*; group by `direction`, `list_kind`, `date_from` (month) |
| `l10n_vn_einvoice_batch_action` | window action | *Portal Lists* |
| `l10n_vn_einvoice_portal_action` | window action | *Portal Invoices* |

## Views — `wizard/l10n_vn_einvoice_batch_import_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_einvoice_batch_import_view_form` | form | `batch_id` (readonly), `list_kind`; `file` with `filename="filename"`; `filename` invisible; a note: *The file is read into rows and not kept.*; footer *Import* (`action_import`, `class="btn-primary"`), *Cancel* |
| `l10n_vn_einvoice_batch_import_action` | window action | `res_model="l10n_vn.einvoice.batch.import"`, `view_mode="form"`, `target="new"`, *Import Portal List* |

## Views — `views/menus.xml`

| Menu | Parent | Action | Groups | Sequence |
|---|---|---|---|---|
| `l10n_vn_einvoice_reconcile_menu` | `account.menu_finance_entries` | — (*E-Invoice Reconciliation*) | `account.group_account_readonly`, `account.group_account_manager` | 40 |
| `l10n_vn_einvoice_batch_menu` | the above | batch action | | 10 |
| `l10n_vn_einvoice_portal_menu` | the above | portal action | | 20 |

## Tests

`tests/common.py`: `PortalListCase(EInvoiceCase)`, `EInvoiceCase` imported from
`odoo.addons.l10n_vn_einvoice.tests.common` (the test company with tax code `0317253698` and the `vn`
chart); no test methods. **Helpers:** `LAYOUTS` holds both official layouts, `(key, header)` per column. `_row(**values)` is a
row dict of made-up defaults (a supplier `0314071202` invoicing the test company, 1,000,000 + 80,000,
*Hóa đơn mới*); `_portal_list(rows, kind="ordinary", title=None, period=…, headers=None)` builds an
`.xlsx` with `openpyxl` in the kind's layout — the title in A3 (the kind's own when `None`), the period
in A4, the kind's headers on row 6 (`headers` overrides some, by key), one row per dict from row 7 —
and returns it base64-encoded; `_new_batch(direction, kind, user=None)` creates a batch, as `user` when
given; `_import(batch, content)` runs the dialog in the batch's environment; `_batch(direction,
content, kind)` does both. Every value is made up; no export is committed (design §7).

### `tests/test_l10n_vn_einvoice_import.py`

`TestPortalImport(PortalListCase)`, `@tagged("post_install", "-at_install")`.

| Test | Asserts |
|---|---|
| `test_import_purchase_list` | three rows (two form-1 invoices, one form 2): three rows with their text as written, period 01/10/2026 – 31/10/2026, name *Purchases 01/10/2026 – 31/10/2026*; three portal invoices, keys normalised, amounts parsed; the form-2 one untaxed = total, VAT 0; `filename` and `import_date` set |
| `test_file_not_kept` | after an import: no `ir.attachment` of the batch or of the dialog holds the file, and the dialog model's `file` column is not an attachment field |
| `test_number_cells` | number cells for STT, number and amounts (`25`, `5411000`, `0`): read as text and parsed; a 0 VAT arrives empty and reads 0 |
| `test_reimport_replaces` | a second import of a two-row list: two rows and two portal invoices, none of the first |
| `test_several_rows_grouped` | two rows with one key: one portal invoice, `row_count` 2, amounts 0; with different statuses, `rows_disagree` |
| `test_status_kinds` | one row per status of the table and one unknown: the `status_kind` of each; a status written decomposed (NFD) reads the same |
| `test_key_error_kept` | a row without a number: kept, `error` *No number.*, no portal invoice; `error_count` 1 |
| `test_wrong_company_refused` | a purchase list whose buyer is `0100000001`, and a sales list whose seller is `0100000001`: `UserError` each, naming it; no rows kept |
| `test_sales_list` | a sales list with a consumer row (buyer empty) and a citizen-ID buyer (`091185007544`): imported; the buyer tax codes as written |
| `test_header_mismatch_refused` | the ordinary list with R6 reading `Trạng thái`: `UserError` naming `R6` |
| `test_cash_register_list` | a cash-register purchase list of two rows on a cash-register batch: rows with the seller's address and the citizen-ID column, two portal invoices, currency the company's |
| `test_layout_title_refused` | a cash-register file on an ordinary batch, and an ordinary file on a cash-register batch: `UserError` each |
| `test_access` | an accountant creates a cash-register list and imports it (positive control), the citizen ID stored, and cannot delete the list (`AccessError`); a read-only user reads the list's invoices and rows and cannot create a list; an administrator deletes it |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Imports the tax portal's lists of sales or purchase invoices, ordinary and cash-register; keeps their rows as imported, not the file; groups them into one portal invoice per legal invoice with its status; (step 2) matches them to the e-invoices |
| `readme/USAGE.md` | Export the month's list from the portal (*Tra cứu HĐĐT mua vào / bán ra*, *Xuất Excel*); create a *Portal List* under *Accounting → E-Invoice Reconciliation*, choose purchases or sales and the list (ordinary or cash register), *Import* and choose the file; what the refusals mean; re-importing a month to pick up later corrections |
