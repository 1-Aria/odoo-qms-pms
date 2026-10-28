# VN E-Invoice Reconciliation — Design

Oct 24, 2026 · @Peter · Revised Oct 28, 2026 · Status: draft

Checks the e-invoices in Odoo against the tax authority's list of the same invoices, for sales and
purchases. A module of its own, `l10n_vn_einvoice_reconcile`, depending on `l10n_vn_einvoice`
(`VN E-Invoice — Design.md`) and on OCA's `excel_import_export`.

**Revision.** The first version (*Design Note*, Oct 24) was written before any export had been seen.
It matched portal rows straight to `account.move` through three supplier-invoice fields on vendor
bills. Two things replaced that: the e-invoice record of `l10n_vn_einvoice`, which now holds the key,
and the sample lists, which settle the input. §11 lists what changed.

## 1. Why

Under Decree 123/2020 (amended by Decree 70/2025), each e-invoice reaches the tax authority (GDT)
through the **seller's** provider when it is issued. The GDT's record is the reference for both sides:

- **Purchases:** a supplier's invoice the GDT does not hold, or holds as cancelled or replaced, is
  not valid for input VAT. An invoice the GDT holds under our tax code that is missing from our books
  raises questions in an audit. Only the seller can issue, cancel, adjust or replace, so the buyer can
  only find the gap and chase the supplier.
- **Sales:** invoices are issued through a provider: I-CA for the trading company today, Viettel
  SInvoice for both companies after the move. Gaps arise from invoices posted in Odoo but never sent,
  invoices issued on the provider's website, and cancellations or replacements made at the provider
  but not in Odoo.

The check is done by hand today, before the monthly VAT return. This module automates the comparison,
so the accountant reviews only the exceptions.

**Not legal advice.** The buyer-side consequences (loss of input VAT, penalties under Decree
125/2020) are to be confirmed with the accountant (O6).

## 2. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| R1 | **The GDT's list is in Odoo** | A month's list of sales or purchase invoices from the portal is imported in one step |
| R2 | **Every portal invoice is matched or flagged** | Each is linked to its e-invoice, or marked as missing from Odoo |
| R3 | **Odoo's own gaps show** | E-invoices of the period with no portal invoice, and posted documents with no e-invoice, are listed |
| R4 | **Differences are named** | Amount and status differences are flagged per invoice, not just "unmatched" |
| R5 | **The check is evidence** | Each import keeps its file, date and results |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| Import of both portal lists, sales and purchases | In | R1 |
| Grouping a list's rows into invoices (§5.3) | In | One invoice can span several rows |
| Matching portal invoices to e-invoices; booking state through the e-invoice | In | R2, R4 |
| The Odoo-only lists | In | R3 |
| Portal-only invoices booked from the list | **Not needed** | The accountant downloads that invoice's XML from the portal and uploads it (`l10n_vn_einvoice`); the next match finds it |
| A validity check when a bill is posted, against the last import | Later | Builds on v1's data |
| Downloading from the portal automatically | **Out** | §4: no public API, captcha-protected login |
| Imports, foreign suppliers, purchases from individuals | Out | Not Vietnamese e-invoices, so absent from the portal |

## 3. How other systems do it

MISA sells input-invoice processing as part of **meInvoice**, separate from its issuing service. It
collects supplier invoices from e-mail and files, checks validity and books them. Bizzi and xCyber sell
similar services. The common pattern is **collect → check → book → compare with the GDT's list**.
`l10n_vn_einvoice` covers collecting, checking and booking; this module covers the comparison.

## 4. The data source: the GDT portal

- **`hoadondientu.gdt.gov.vn`**, logged in with the company's account: *Tra cứu → Tra cứu HĐĐT bán
  ra / mua vào* lists every sales or purchase invoice the GDT holds for the company in a period.
- **Export: an Excel list, and the XML of one invoice at a time.** No bulk XML. So this module reads
  the list, and an invoice's XML goes through `l10n_vn_einvoice`.
- **Two lists, two layouts** (`samples/`, recreated by Peter from the portal; to be confirmed against a
  real export, O1). Both have the title in A3, the period in A4 (*Từ ngày … đến ngày …*), the headers on
  row 6 and data from row 7.

| Column | *Hóa đơn điện tử* (ordinary) | *Hóa đơn có mã khởi tạo từ máy tính tiền* (cash register) |
|---|---|---|
| STT | A | A |
| Ký hiệu mẫu số (form) | B | B |
| Ký hiệu hóa đơn (symbol) | C | C |
| Số hóa đơn (number) | D | D |
| Ngày lập (date) | E | E |
| MST người bán (seller tax code) | F | F |
| Tên người bán (seller name) | G | G |
| Địa chỉ người bán (seller address) | — | H |
| MST người mua (buyer tax code) | H | I |
| Tên người mua (buyer name) | I | J |
| Địa chỉ người mua (buyer address) | J | — |
| Căn cước công dân (ID card) | — | K |
| Tổng tiền chưa thuế (untaxed) | K | L |
| Tổng tiền thuế (VAT) | L | M |
| Tổng tiền chiết khấu thương mại (discount) | M | N |
| Tổng tiền phí (fees) | N | — |
| Tổng tiền thanh toán (total) | O | O |
| Đơn vị tiền tệ (currency) | P | — |
| Tỷ giá (rate) | Q | — |
| Trạng thái hóa đơn (status) | R | P |
| Kết quả kiểm tra hóa đơn (check result) | S | Q |

- **Values seen:** status *Hóa đơn mới*, check result *Đã cấp mã hóa đơn*. The other values are
  expected but not yet seen (O3).
- **Number formats:** in both lists the buyer tax code reads `601304027`, nine digits with its leading
  zero lost (a number in the ordinary list, text in the other), and form and number come as `1.0` and
  `25.0`. Normalisation repairs both (§5.4).
- **One account per company,** so each import belongs to one company.

## 5. Design

### 5.1 Import: through `excel_import_export`

OCA's `excel_import_export` (`server-tools`, installed) imports an Excel file into a record through
an **XLSX template** whose *instruction* maps cells to fields. From its source:

- **Columns are mapped by cell position** (`A7`, `B7`…), read down to the first row where all mapped
  cells are empty (`models/xlsx_import.py:101-143`). A sheet can be named by index, so a renamed sheet
  does not matter.
- **Existing lines are deleted before an import** unless `_NODEL_` is set
  (`models/xlsx_import.py:80-96`), so re-importing a batch replaces its rows.
- **Date conversion assumes `.xls` cells** (`models/common.py:270-271` reads `cell.ctype`, which
  `openpyxl` cells for `.xlsx` files lack). So **every column is imported into a text field,** and the
  module parses dates and amounts itself (§5.4). This also keeps the raw values as the evidence.
- **The import wizard keeps no copy of the file** (`wizard/import_xlsx_wizard.py:140-160`). So the
  batch holds the file and calls the importer itself (`xlsx.import.import_xlsx`, `models/xlsx_import.py:360-378`),
  then runs the grouping and matching. The wizard is not used.

**Two templates ship with the module, one per layout,** both targeting the batch's rows. They are
data records with `noupdate="1"`. If the portal changes its columns, the accountant edits the
instruction in *Settings → Technical → Excel Import/Export → XLSX Templates*, and an upgrade does not
overwrite the edit. A layout that changes beyond editing gets a new template; the old one is archived,
and batches imported with it keep it.

### 5.2 Data model (working names)

| Model | One record per | Content |
|---|---|---|
| **`l10n_vn.einvoice.batch`** | import | `company_id`; `direction` (sale / purchase); `template_id` (which list); `date_from`, `date_to`; `file`, `filename`, `import_date`; `row_ids`, `invoice_ids`; counts per match state |
| **`l10n_vn.einvoice.portal.row`** | row of the file | `batch_id`; every column as text, as imported (§4); `invoice_id` (its group, §5.3) |
| **`l10n_vn.einvoice.portal`** | invoice of the list | `batch_id`; the normalised key (seller tax code, form, symbol, number), date, buyer tax code; untaxed, VAT, total; status and check result; `row_ids`; `einvoice_id`; `match_state` and the differences (§5.5) |

Rows and invoices are separate because they answer different questions. **Rows are the evidence:**
exactly what the file said. **Invoices are what gets matched:** one per legal invoice, whatever number
of rows it took.

On `l10n_vn.einvoice` (from the base module): the inverse `portal_ids`, so an e-invoice shows the
portal lists that confirmed it.

### 5.3 Grouping rows into invoices

The portal is reported to split an invoice with several VAT rates into several rows, one per rate,
with some columns repeated and others varying. **No sample shows it yet** (O2), and neither layout has
a rate column. The design does not depend on the exact shape:

1. **Rows are grouped by key**: seller tax code + form + symbol + number, normalised (§5.4). The key
   is the same on every row of an invoice, so grouping is never ambiguous, and **matching uses only the
   key.**
2. **The amounts are combined by a rule that checks itself.** A row is *self-consistent* when its total
   equals its untaxed amount + VAT + fees, within 1 đồng.
   - Every row self-consistent: the rows are parts of the invoice. **Untaxed, VAT, fees and total are
     summed.**
   - Every row has the same total, equal to the sum of all rows' untaxed + VAT + fees: the total is
     repeated. **Untaxed, VAT and fees are summed; the total is taken once.**
   - A single row fits both rules.
   - Neither: **`amounts_unclear`.** The invoice is still matched by key; only the amount comparison is
     skipped, and the accountant reviews it.
3. **The other columns must agree across rows:** date, names, buyer tax code, status, check result.
   If they disagree, the invoice is marked `amounts_unclear` and the disagreement is shown.

How the discount column enters the total is unknown (O2). Until a sample shows it, a row with a
discount that fits neither rule counts as not self-consistent.

When a real multi-rate export arrives, it shows which rule applies; the other is removed if it never
occurs. Tests cover both shapes with made-up rows.

### 5.4 Normalisation

The key follows the base module's rules (`VN E-Invoice — Design.md` §4). Repairs for the list's
formats come first:

| Value | Repair |
|---|---|
| Tax code | A trailing `.0` removed; the part before any `-` left-padded with zeros to 10 digits (`601304027` → `0601304027`) |
| Form, number | A trailing `.0` removed; then as in the base module |
| Date | `dd/mm/yyyy` text, or the date-time the cell held |
| Amounts | Parsed as decimals; empty = 0 |

A value that still does not parse marks its row, and its invoice is `amounts_unclear` or, for a key
part, left out of matching with the reason shown.

### 5.5 Matching

For each portal invoice of a batch, the e-invoice of the batch's company with the same key, in the
batch's direction (purchase list → received; sales list → issued).

| `match_state` | When |
|---|---|
| `matched` | e-invoice found and **booked** (base module: linked to a posted document); amounts equal; portal status normal |
| `not_booked` | e-invoice found, but its document is a draft, cancelled or missing |
| `amount_diff` | e-invoice found; untaxed, VAT or total differs (the differences are stored) |
| `status_diff` | the portal shows the invoice replaced, adjusted or cancelled while its e-invoice is booked |
| `portal_only` | no e-invoice with that key: the XML has not been read into Odoo. The action is to download it from the portal and upload it |
| `amounts_unclear` | the rows could not be combined (§5.3); the key match is shown, the amounts are not compared |

**Amounts** are compared between the portal and the e-invoice, both read from the tax documents. The
base module already compares the e-invoice with its bill. VND has no decimals; the tolerance is 1 đồng
per amount (O4).

**Statuses** are read through a small table in the code, with the expected values until a real export
confirms them (O3): *Hóa đơn mới* → normal; *thay thế*,
*điều chỉnh* → normal (the new invoice); *bị thay thế*, *bị điều chỉnh*, *đã bị hủy* → the states
behind `status_diff`. An unknown value is shown as such and makes the invoice `status_diff`, so a
change on the portal is noticed rather than misread.

**Odoo-only** (R3) is two searches, shown as smart buttons on the batch:

- **E-invoices without a portal invoice:** e-invoices of the batch's company and direction, dated in
  the batch's period, with no `portal_ids`.
- **Documents without an e-invoice:** posted vendor bills (purchase) or customer invoices (sale) of the
  company and period whose partner has a Vietnamese tax code, with no e-invoice. These are bills whose
  XML was never attached.

**The period** is the invoice date, not the accounting date, because the portal lists invoices by
issue date.

### 5.6 Views and access

- **Batches:** list and form. The form holds the file, the template, *Import* and *Match again*, the
  portal invoices grouped by `match_state`, and the two Odoo-only smart buttons.
- **Portal invoices:** list with filters per `match_state` and direction; a record shows its rows and
  opens its e-invoice.
- **E-invoice form** (base module): the portal lists that confirmed it.
- **Menu:** *Accounting → Accounting → E-Invoice Reconciliation* (core's `account.menu_finance_entries`).
- **Access:** importing and matching for `account.group_account_manager`; reading for
  `account.group_account_user`. Record rules by company. The cash-register list's ID-card column is
  personal data: imported into the rows, readable only by the managers' group.

## 6. Decisions

| # | Decision |
|---|---|
| D1 | **The GDT export is the source; Odoo does not download it** (§4) |
| D2 | **The input is the Excel list;** an invoice's XML goes through `l10n_vn_einvoice` (§4) |
| D3 | **The import uses `excel_import_export`, one template per layout, editable and kept across upgrades** (§5.1) |
| D4 | **Every column is imported as text** and parsed by the module (§5.1, §5.4) |
| D5 | **The batch keeps the file and runs the importer itself;** the wizard is not used (§5.1) |
| D6 | **Rows and portal invoices are separate records:** rows are the evidence, invoices are matched (§5.2) |
| D7 | **Rows are grouped by key; amounts are combined by a self-checking rule** (§5.3) |
| D8 | **Portal invoices match e-invoices, not documents;** booking is read through the e-invoice (§5.5) |
| D9 | **Both sides, one model:** sales and purchases differ only by `direction` |
| D10 | **Odoo-only is a search, not a record** (§5.5) |
| D11 | **Re-importing a batch replaces its rows and re-matches** |

## 7. Steps (provisional)

| # | Scope | Waits on |
|---|---|---|
| 1 | Models, access, views; the two templates; import from the batch | `l10n_vn_einvoice` step 1 |
| 2 | Normalisation, grouping (§5.3), matching and `match_state`, the Odoo-only searches | — |
| 3 | Adjust to a real export: columns, values, the multi-rate rule | O1–O3 |
| 4 | Later: a check at posting time against the last import | step 2 in use |

Tests import the two sample lists, and made-up lists for the grouping rules, into the trading company.

## 8. References

| Source | Used for |
|---|---|
| `VN E-Invoice — Design.md` | The e-invoice record, the key, normalisation |
| `samples/*.xlsx` | The two layouts (§4) |
| `oca/server-tools/excel_import_export` | Positional mapping and end of data (`models/xlsx_import.py:101-143`), line replacement (`:80-96`), date conversion (`models/common.py:265-310`), the importer and the wizard (§5.1) |
| [MISA meInvoice, input-invoice software](https://www.meinvoice.vn/tin-tuc/10905/phan-mem-hoa-don-dien-tu-dau-vao-misa-meinvoice/) | How the market handles purchase invoices (§3) |
| [MISA SME, input invoices from the tax portal](https://sme.misa.vn/351069/cach-lay-hoa-don-dau-vao-tren-trang-thue-dien-tu/) | The portal's sales and purchase lookup (§4) |
| [EY, changes from 1 June 2025](https://www.ey.com/en_vn/technical/tax/tax-and-law-updates/tax-alert-april-2025-changes-to-invoicing-regulations-effective-from-1-june-2025) | Decree 70/2025 amending Decree 123 |

## 9. Open questions

| # | Question | Settles |
|---|---|---|
| **O1** | **A real export of each list,** sales and purchases: whether the columns match the recreations, whether sales and purchases share a layout, and whether tax codes and numbers are stored as text or numbers | The templates; §5.4 |
| **O2** | **A multi-rate invoice in a real export:** which columns repeat, which vary, whether a rate column appears, and how the discount enters the total | §5.3 |
| O3 | The portal's status and check-result values beyond *Hóa đơn mới* and *Đã cấp mã hóa đơn* | The status table (§5.5) |
| O4 | Whether 1 đồng per amount is the right tolerance, or exact equality | `amount_diff` |
| O5 | Does an invoice cancelled or replaced in a later month change its row in the original month's list, or appear only in the later month's? | Whether earlier months need re-importing |
| O6 | With the accountant: the buyer's obligations and the consequences of booking an invalid invoice | §1 |

## 10. Prerequisites

- `l10n_vn_einvoice` step 1: the e-invoice record and its key.
- `excel_import_export` installed (it is).

## 11. Changes from the first version

| First version (Oct 24) | Now | Why |
|---|---|---|
| Portal rows matched to `account.move` | Portal invoices matched to e-invoices; booking read through them | The e-invoice record holds the key, uniquely (base module, D1) |
| Three supplier-invoice fields on vendor bills | None; the key lives on the e-invoice | As above |
| One record per row | Rows and portal invoices separate; rows grouped by key | One invoice can span several rows (§5.3) |
| `duplicate` match state | Removed | The key is unique on e-invoices |
| Draft bills from portal-only rows (later) | Not needed | The portal gives each invoice's XML; the base module reads it |
| The import wizard with a post-import hook | The batch keeps the file and runs the importer | The wizard keeps no copy of the file (R5) |
| Columns typed by field | All text, parsed by the module | Date conversion fails on `.xlsx` cells; raw values are the evidence |
| Open: export format, bulk XML | Settled: Excel list plus one XML per invoice; two layouts | Peter's samples, Oct 27 |
