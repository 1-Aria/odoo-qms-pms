# VN E-Invoice Reconciliation — Design

Oct 24, 2026 · @Peter · Revised Oct 31, 2026 · Status: draft

Checks the e-invoices in Odoo against the tax authority's list of the same invoices, for sales and
purchases. A module of its own, `l10n_vn_einvoice_reconcile`, depending on `l10n_vn_einvoice`
(`VN E-Invoice — Design.md`) and on OCA's `excel_import_export`.

**Revisions.** The first version (*Design Note*, Oct 24) was written before any export had been seen.
It matched portal rows straight to `account.move` through three supplier-invoice fields on vendor
bills. The Oct 28 revision replaced that with the e-invoice record of `l10n_vn_einvoice`, which holds
the key. The Oct 31 revision rests on official exports: the layout, the value formats and the
statuses are now known, and a simpler rule handles invoices spread over several rows. §11 lists what
changed.

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
| Import of the portal's list, sales and purchases | In | R1 |
| Grouping a list's rows into invoices (§5.3) | In | One invoice can span several rows |
| Matching portal invoices to e-invoices; booking state through the e-invoice | In | R2, R4 |
| The Odoo-only lists | In | R3 |
| Portal-only invoices booked from the list | **Not needed** | The accountant downloads that invoice from the portal, unzips it, and uploads its XML (`l10n_vn_einvoice`); the next match finds it |
| Summing the amounts of an invoice spread over several rows | Later | No export has shown one yet (§5.3, O2) |
| The cash-register list | Later | Only a recreation has been seen (§4, O1) |
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
- **Export: an Excel list, and one invoice at a time as a ZIP** (`invoice.xml` with an HTML viewer).
  No bulk XML. This module reads the list; an invoice's XML is unzipped outside Odoo and goes through
  `l10n_vn_einvoice`.
- **The samples** are kept outside the repo, in `Odoo-Build/accounting-samples/`: `new/` holds the
  official exports and ZIPs, `old/` the first samples and the recreated cash-register list. They hold
  lookup codes and the personal data of private buyers, so they are not committed.

**The list (*DANH SÁCH HÓA ĐƠN*), from three official exports** (Oct 2026 purchases, 14 rows; Oct 2026
sales, 213 rows; Apr 2026 sales, 177 rows). **Sales and purchases share one layout:** one sheet
(*sheet 1*), the title in A3, the period in A4 (*Từ ngày 01/10/2026 đến ngày 31/10/2026*), the headers on
row 6 and data from row 7 down to the first empty row.

| Col | Header | Content |
|---|---|---|
| A | STT | Row number (a number) |
| B | Ký hiệu mẫu số | Form, text (`1`, `2`) |
| C | Ký hiệu hóa đơn | Symbol, text (`C26TQP`) |
| D | Số hóa đơn | Number, text, without leading zeros (`2001`) |
| E | Ngày lập | Date, text `dd/mm/yyyy` |
| F | MST người bán/MST người xuất hàng | Seller tax code, text |
| G | Tên người bán/Tên người xuất hàng | Seller name |
| H | MST người mua/MST người nhận hàng | Buyer tax code, text; **empty for consumers**, and a 12-digit citizen ID for some individuals |
| I | Tên người mua/Tên người nhận hàng | Buyer name |
| J | Địa chỉ người mua | Buyer address |
| K | Tổng tiền chưa thuế | Untaxed amount; **empty on a sales invoice (form 2)** |
| L | Tổng tiền thuế | VAT; empty on form 2 |
| M | Tổng tiền chiết khấu thương mại | Commercial discount; 0 or empty |
| N | Tổng tiền phí | Fees; empty in every row seen |
| O | Tổng tiền thanh toán | Total |
| P | Đơn vị tiền tệ | Currency (`VND`) |
| Q | Tỷ giá | Rate, text (`1.0`) |
| R | Trạng thái hóa đơn | Status (§5.5) |
| S | Kết quả kiểm tra hóa đơn | Check result: *Đã cấp mã hóa đơn* in every row seen |

- **No invoice spans several rows** in any of the three exports (§5.3).
- **The list shows each invoice's status on the day of the export.** Invoice `C26TQP-950` (April) was
  replaced in May, and the April list exported in October already shows it *đã bị thay thế*. A month
  re-imported later therefore carries the corrections made since.
- **An information-only adjustment shows zero amounts** (`881`, `958`): the adjusting invoice's own
  totals, which its XML also gives as 0.
- **The cash-register list** (*Hóa đơn có mã khởi tạo từ máy tính tiền*) is known only from a recreation:
  the same structure with some headers different (a seller address, a citizen-ID column, no currency,
  rate or fees). Its template waits for an official export (O1).
- **One account per company,** so each import belongs to one company.

## 5. Design

### 5.1 Import: through `excel_import_export`

OCA's `excel_import_export` (`server-tools`, installed) imports an Excel file into a record through
an **XLSX template** whose *instruction* maps cells to fields. From its source:

- **Columns are mapped by cell position** (`A7`, `B7`…), read down to the first row where all mapped
  cells are empty (`models/xlsx_import.py:101-143`). The sheet is named by index, so its name does not
  matter.
- **Existing lines are deleted before an import** unless `_NODEL_` is set
  (`models/xlsx_import.py:80-96`), so re-importing a batch replaces its rows.
- **Date conversion assumes `.xls` cells** (`models/common.py:270-271` reads `cell.ctype`, which
  `openpyxl` cells for `.xlsx` files lack). So **every column is imported into a text field,** and the
  module parses dates and amounts itself (§5.4). This also keeps the raw values as the evidence.
- **The import wizard keeps no copy of the file** (`wizard/import_xlsx_wizard.py:140-160`). So the
  batch holds the file and calls the importer itself (`xlsx.import.import_xlsx`,
  `models/xlsx_import.py:360-378`), then runs the grouping and matching. The wizard is not used.

**One template ships with the module** for the list above, targeting the batch's rows; the
cash-register list gets its own when an official export exists. The template is a data record with
`noupdate="1"`. If the portal changes its columns, the accountant edits the instruction in
*Settings → Technical → Excel Import/Export → XLSX Templates*, and an upgrade does not overwrite the
edit. A layout that changes beyond editing gets a new template; the old one is archived, and batches
imported with it keep it.

### 5.2 Data model (working names)

| Model | One record per | Content |
|---|---|---|
| **`l10n_vn.einvoice.batch`** | import | `company_id`; `direction` (sale / purchase); `template_id` (which list); `date_from`, `date_to`; `file`, `filename`, `import_date`; `row_ids`, `invoice_ids`; counts per match state |
| **`l10n_vn.einvoice.portal.row`** | row of the file | `batch_id`; every column as text, as imported (§4); `invoice_id` (its group, §5.3) |
| **`l10n_vn.einvoice.portal`** | invoice of the list | `batch_id`; the normalised key (seller tax code, form, symbol, number), date, buyer tax code; untaxed, VAT, total; status and check result; `row_count`; `row_ids`; `einvoice_id`; `match_state` and the differences (§5.5) |

Rows and invoices are separate because they answer different questions. **Rows are the evidence:**
exactly what the file said. **Invoices are what gets matched:** one per legal invoice, whatever number
of rows it took.

On `l10n_vn.einvoice` (from the base module): the inverse `portal_ids`, so an e-invoice shows the
portal lists that confirmed it.

### 5.3 Invoices on several rows

The portal is reported to split an invoice with several VAT rates into one row per rate. No export
has shown it, and such invoices are expected to be rare. So v1 takes the safe route: it never guesses
how the rows combine.

1. **Rows are grouped by key:** seller tax code + form + symbol + number, normalised (§5.4). The key
   is the same on every row of an invoice, so grouping is never ambiguous, and **matching uses only the
   key.** A split invoice is found like any other.
2. **An invoice on one row** — every invoice seen so far — takes its amounts, status and other columns
   from that row and is compared in full (§5.5).
3. **An invoice on several rows** is matched by key, and its amounts are **not compared**: its state
   is `amounts_to_check`, and the accountant sees its rows beside the e-invoice. Its status and check
   result are still read, from its first row; rows that disagree on them are shown.
4. **When a real case appears,** its rows show how the amounts combine, and a summing rule is added
   then. Rows are stored as imported, so nothing has to be re-imported, only matched again.

The rule cannot produce a wrong match or a false difference: the worst case is one invoice the
accountant checks by hand.

### 5.4 Normalisation

The key follows the base module's rules (`VN E-Invoice — Design.md` §4). The list's own formats:

| Value | Treatment |
|---|---|
| Tax code | As in the base module: whitespace removed, the branch suffix kept. Ten digits for a business, twelve for an individual's citizen ID, empty for a consumer |
| Form, symbol, number | As in the base module. A trailing `.0`, which the recreated lists had and the official ones do not, is removed first, at no cost |
| Date | `dd/mm/yyyy` text |
| Amounts | Parsed as decimals; empty = 0. **Form 2:** untaxed = total, VAT = 0, as the base module stores a sales invoice (its divergence 3), so the two compare like with like |

A key value that does not parse leaves its row out of matching, with the reason shown on the row.

### 5.5 Matching

For each portal invoice of a batch, the e-invoice of the batch's company with the same key, in the
batch's direction (purchase list → received; sales list → issued).

| `match_state` | When |
|---|---|
| `matched` | e-invoice found and **booked** (base module: linked to a posted document); amounts equal; portal status normal |
| `not_booked` | e-invoice found, but its document is a draft, cancelled or missing |
| `amount_diff` | e-invoice found; untaxed, VAT or total differs (the differences are stored) |
| `status_diff` | the portal shows the invoice replaced, adjusted or cancelled while its e-invoice is booked |
| `amounts_to_check` | the invoice spans several rows (§5.3); the key match is shown, the amounts are not compared |
| `portal_only` | no e-invoice with that key: the XML has not been read into Odoo. The action is to download it from the portal, unzip it and upload it |

**Amounts** are compared between the portal and the e-invoice, both read from the tax documents. The
base module already compares the e-invoice with its bill. VND has no decimals; the tolerance is 1 đồng
per amount (O4).

**Statuses**, as the exports write them, read through a table in the code:

| Status | Reading |
|---|---|
| *Hóa đơn mới* | Normal |
| *Hóa đơn thay thế* | Normal: this invoice replaces another |
| *Hóa đơn điều chỉnh* | Normal: this invoice adjusts another |
| *Hóa đơn đã bị thay thế* | Replaced: `status_diff` when booked |
| *Hóa đơn đã bị điều chỉnh* | Adjusted: `status_diff` when booked |
| *Hóa đơn đã bị hủy* | Cancelled: `status_diff` when booked. Expected, not yet seen (O3) |

An unknown value is shown as such and makes the invoice `status_diff`, so a change on the portal is
noticed rather than misread. The check result is stored and shown; only *Đã cấp mã hóa đơn* has been
seen.

**Odoo-only** (R3) is two searches, shown as smart buttons on the batch:

- **E-invoices without a portal invoice:** e-invoices of the batch's company and direction, dated in
  the batch's period, with no `portal_ids`.
- **Documents without an e-invoice:** posted vendor bills (purchase) or customer invoices (sale) of the
  company and period whose partner has a Vietnamese tax code, with no e-invoice. These are bills whose
  XML was never attached.

**The period** is the invoice date, not the accounting date, because the portal lists invoices by
issue date. **Earlier months** are re-imported to pick up their later corrections (§4): a replacement
or adjustment issued this month changes the status of last month's original.

### 5.6 Views and access

- **Batches:** list and form. The form holds the file, the template, *Import* and *Match again*, the
  portal invoices grouped by `match_state`, and the two Odoo-only smart buttons.
- **Portal invoices:** list with filters per `match_state` and direction; a record shows its rows and
  opens its e-invoice.
- **E-invoice form** (base module): the portal lists that confirmed it.
- **Menu:** *Accounting → Accounting → E-Invoice Reconciliation* (core's `account.menu_finance_entries`).
- **Access:** importing and matching for `account.group_account_manager`; reading for
  `account.group_account_user`. Record rules by company. A sales list's buyer columns hold private
  customers' names, addresses and citizen IDs, as the issued invoices themselves do; the rows carry
  the same access as the batch.

## 6. Decisions

| # | Decision |
|---|---|
| D1 | **The GDT export is the source; Odoo does not download it** (§4) |
| D2 | **The input is the Excel list;** an invoice's XML, unzipped outside Odoo, goes through `l10n_vn_einvoice` (§4) |
| D3 | **The import uses `excel_import_export`, one template per layout, editable and kept across upgrades** (§5.1) |
| D4 | **Every column is imported as text** and parsed by the module (§5.1, §5.4) |
| D5 | **The batch keeps the file and runs the importer itself;** the wizard is not used (§5.1) |
| D6 | **Rows and portal invoices are separate records:** rows are the evidence, invoices are matched (§5.2) |
| D7 | **Rows are grouped by key, and an invoice on several rows is never summed by guess:** it is matched by key and marked `amounts_to_check` until a real case shows how its rows combine (§5.3; Peter, 2026-10-31) |
| D8 | **Portal invoices match e-invoices, not documents;** booking is read through the e-invoice (§5.5) |
| D9 | **Both sides, one model:** sales and purchases differ only by `direction` |
| D10 | **Odoo-only is a search, not a record** (§5.5) |
| D11 | **Re-importing a batch replaces its rows and re-matches;** earlier months are re-imported to pick up later corrections (§4, §5.5) |
| D12 | **A form-2 row's empty untaxed amount and VAT read as total and 0,** the base module's rule (§5.4) |

## 7. Steps (provisional)

| # | Scope | Waits on |
|---|---|---|
| 1 | Models, access, views; the template for the list; import from the batch | — |
| 2 | Normalisation, grouping (§5.3), matching and `match_state`, the Odoo-only searches | — |
| 3 | The cash-register template | An official cash-register export (O1) |
| 4 | Summing an invoice spread over several rows | A real case (O2) |
| 5 | Later: a check at posting time against the last import | step 2 in use |

Tests build their lists from the official layout with made-up values, so no export is committed; the
multi-row case is a made-up list of its own, into the trading company.

## 8. References

| Source | Used for |
|---|---|
| `VN E-Invoice — Design.md` | The e-invoice record, the key, normalisation |
| `Odoo-Build/accounting-samples/new/*.xlsx` (outside the repo) | The layout, formats and statuses (§4, §5.5) |
| `oca/server-tools/excel_import_export` | Positional mapping and end of data (`models/xlsx_import.py:101-143`), line replacement (`:80-96`), date conversion (`models/common.py:265-310`), the importer and the wizard (§5.1) |
| [MISA meInvoice, input-invoice software](https://www.meinvoice.vn/tin-tuc/10905/phan-mem-hoa-don-dien-tu-dau-vao-misa-meinvoice/) | How the market handles purchase invoices (§3) |
| [MISA SME, input invoices from the tax portal](https://sme.misa.vn/351069/cach-lay-hoa-don-dau-vao-tren-trang-thue-dien-tu/) | The portal's sales and purchase lookup (§4) |
| [EY, changes from 1 June 2025](https://www.ey.com/en_vn/technical/tax/tax-and-law-updates/tax-alert-april-2025-changes-to-invoicing-regulations-effective-from-1-june-2025) | Decree 70/2025 amending Decree 123 |

## 9. Open questions

| # | Question | Settles |
|---|---|---|
| O1 | An official export of the **cash-register list**. The ordinary list is settled (§4) | The cash-register template (step 3) |
| O2 | **An invoice spread over several rows:** which columns repeat, which vary, how the amounts combine | The summing rule (step 4); until then §5.3 |
| O3 | The wording for a **cancelled** invoice, and any check result besides *Đã cấp mã hóa đơn* | The status table (§5.5) |
| O4 | Whether 1 đồng per amount is the right tolerance, or exact equality | `amount_diff` |
| O6 | With the accountant: the buyer's obligations and the consequences of booking an invalid invoice | §1 |

O5 (whether a later correction changes an earlier month's list) is settled: it does (§4).

## 10. Prerequisites

- `l10n_vn_einvoice` steps 1 and 2 (done): the e-invoice record, its key, bills from XML.
- `excel_import_export` installed (it is).

## 11. Changes

**From the first version (Oct 24) to Oct 28**

| First version | Oct 28 | Why |
|---|---|---|
| Portal rows matched to `account.move` | Portal invoices matched to e-invoices; booking read through them | The e-invoice record holds the key, uniquely (base module, D1) |
| Three supplier-invoice fields on vendor bills | None; the key lives on the e-invoice | As above |
| One record per row | Rows and portal invoices separate; rows grouped by key | One invoice can span several rows (§5.3) |
| `duplicate` match state | Removed | The key is unique on e-invoices |
| Draft bills from portal-only rows (later) | Not needed | The portal gives each invoice's XML; the base module reads it |
| The import wizard with a post-import hook | The batch keeps the file and runs the importer | The wizard keeps no copy of the file (R5) |
| Columns typed by field | All text, parsed by the module | Date conversion fails on `.xlsx` cells; raw values are the evidence |

**From Oct 28 to Oct 31**

| Oct 28 | Oct 31 | Why |
|---|---|---|
| Layout from recreated lists, two templates | Layout from three official exports; one template for the ordinary list, the cash-register one later | Official exports of the ordinary list, sales and purchases; none of the cash-register list |
| Repairs for lost leading zeros and `25.0` numbers | Kept as a no-cost trim; the official values are text | The repairs answered the recreation's formats |
| A self-checking rule summing an invoice's rows, `amounts_unclear` otherwise | No summing; a multi-row invoice is matched by key and marked `amounts_to_check` | No case seen; the safe rule never guesses (D7) |
| Statuses expected | Statuses confirmed from the April export; only *đã bị hủy* still unseen | Peter's April export, Oct 31 |
| Form 2 not considered | Empty untaxed and VAT read as total and 0 (D12) | The October purchase list |
| O5 open | Settled: the list shows the status at export, so earlier months are re-imported | Invoice 950 in the April list |
| Per-invoice XML | Per-invoice ZIP, unzipped outside Odoo | The portal's download; no ZIP support in the modules (Peter, Oct 31) |
