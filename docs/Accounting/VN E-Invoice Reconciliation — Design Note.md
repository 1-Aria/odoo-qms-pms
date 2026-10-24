# VN E-Invoice Reconciliation — Design Note

Oct 24, 2026 · @Peter · Status: draft. **Waiting for a sample of the tax portal's export (§9, O1).**

This note checks the invoices in Odoo against the tax authority's record of the same invoices,
for sales and for purchases. A module of its own, `l10n_vn_einvoice_reconcile` (working name),
outside the QMS-PMS and IE-MES suites. This note is the reference to continue from once a real
export file is in hand. Every column name and status value below is provisional until then.

## 1. Why

Under Decree 123/2020 (amended by Decree 70/2025), each e-invoice reaches the tax authority (GDT)
through the **seller's** provider when it is issued. Most invoices are coded by the GDT before the
buyer receives them. The GDT's record is therefore the reference for both sides:

- **Purchases:** a supplier's invoice the GDT does not hold, or holds as cancelled or replaced, is
  not valid for input VAT. An invoice the GDT holds under our tax code that is missing from our books
  raises questions in an audit. The buyer cannot correct the GDT's data, since only the seller can
  issue, cancel, adjust or replace. The buyer can only find the gap and chase the supplier.
- **Sales:** `l10n_vn_edi_viettel` sends customer invoices to Viettel SInvoice, which forwards them
  to the GDT. Gaps can still arise:
  - invoices posted in Odoo but never sent (on the test database, 10 customer invoices sit in
    *Ready to send*);
  - invoices issued directly on the SInvoice website;
  - cancellations or replacements made at Viettel but not in Odoo.

The check is done by hand today, comparing the GDT portal's list with the books before the monthly
VAT return. This module automates the comparison, so the accountant only reviews the exceptions.

**Not legal advice.** The buyer-side consequences (loss of input VAT, penalties under Decree
125/2020) are to be confirmed with the accountant (O7).

## 2. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| R1 | **The GDT's list is in Odoo** | A month's export of sales or purchase invoices from the portal is imported in one step |
| R2 | **Every row is matched or flagged** | Each portal row is linked to its Odoo invoice, or marked as missing in Odoo |
| R3 | **Odoo's own gaps show** | Posted invoices in the period with no portal row are listed |
| R4 | **Differences are named** | Amount and status differences are flagged per row, not just "unmatched" |
| R5 | **The check is evidence** | Each import is kept with its date and file, so what was checked, and when, can be shown |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| Import of the portal's Excel export, sales and purchases | In | R1 |
| Matching against posted customer invoices, vendor bills and their credit notes | In | R2, R3 |
| Supplier invoice form, symbol and number as fields on vendor bills | In | The matching key (§5.2) |
| Draft vendor bills created from portal-only rows | Later | Needs the XML of each invoice, or enough columns in the list |
| Validity check when a bill is posted, against the last import | Later | Builds on v1's data |
| Downloading from the portal automatically | **Out** | §4: no public API, captcha-protected login |
| Imports, foreign suppliers, purchases from individuals | Out | Not Vietnamese e-invoices, so absent from the portal (§5.4) |

## 3. How other systems do it

MISA sells input-invoice processing as part of **meInvoice**, separate from its issuing service. It
collects supplier invoices from e-mail and files, checks validity (the seller's status; the buyer's
and seller's tax code, name and address), fetches originals, and pushes the data into its accounting
software. Bizzi and xCyber sell similar services. The common pattern is **collect → check → book →
compare with the GDT's list**. This module covers the last step, and later the booking (§2,
*Later*).

## 4. The data source: the GDT portal

- **`hoadondientu.gdt.gov.vn`**, logged in with the company's account: *Tra cứu → Tra cứu HĐĐT bán
  ra / mua vào* lists every sales or purchase invoice the GDT holds for the company in a period, for
  one counterparty or all of them.
- **Export:** the list is reported to export to Excel, and invoices to XML. **Not yet seen** (O1).
- **No public API.** Automating the download would mean scripting a captcha-protected government
  site, which is fragile and not pursued. The accountant downloads the export once a month; Odoo does
  the rest.
- **One account per company.** The instance has two companies, the garment company and the trading
  company, each with its own tax code, so each import belongs to one company.

## 5. Design

### 5.1 Import: through `excel_import_export`

OCA's `excel_import_export` (`server-tools`, installed on this instance) imports an Excel file into a
record through an **XLSX template** (*Settings → Technical → Excel Import/Export → XLSX Templates*).
From its source:

- **The template's instructions map cells to fields:** header cells (`_HEAD_`) to the target record,
  and table columns to its One2many lines.
- **Loading goes through Odoo's standard importer,** so values are converted per field type.
- **Lines are replaced by default:** existing lines are deleted before the import unless `_NODEL_`
  is set (`models/xlsx_import.py:80-96`).
- **A post-import hook runs a method** on the record afterwards (`post_import_hook`,
  `${object.method()}`, `models/xlsx_template.py:78-81`; run at `models/xlsx_import.py:376-377`).

So no parser needs writing:

- **Target record:** an *import batch* (§5.3), opened by the import wizard (`import.xlsx.wizard`) from
  the batch form.
- **Lines:** the batch's *portal invoices*, one per row of the export.
- **Template:** an `.xlsx` shaped exactly like the portal's export (sheet name, header row, column
  order), shipped in the module's data with its instructions. **This is the missing piece (O1).**
- **Post-import hook:** `${object.action_match()}`, so matching runs as soon as the rows land.

Re-importing the same batch replaces its rows and re-runs the matching. That's the right default when
a month is downloaded again after suppliers have corrected their invoices.

### 5.2 The matching key

A Vietnamese e-invoice is identified by **the seller's tax code + form (*mẫu số*) + symbol (*ký
hiệu*) + number (*số hóa đơn*)**.

| Side | Seller tax code | Form, symbol, number |
|---|---|---|
| **Sales** (Odoo customer invoices) | the company's VAT | already stored by `l10n_vn_edi_viettel`: `l10n_vn_edi_invoice_symbol` (with its template) and `l10n_vn_edi_invoice_number` |
| **Purchases** (Odoo vendor bills) | the vendor's VAT (`commercial_partner_id.vat`) | **not stored today.** Odoo has only the free-text *Bill Reference* (`ref`). Added as three fields on `account.move` (§5.3) |

**Normalisation before comparing:**
- tax codes without spaces or dashes;
- symbols in upper case;
- numbers compared as integers, so `0000123` = `123`.

How the portal writes the form, symbol and number is still unknown (O2): whether the form is a
single digit or a combined form-and-symbol column, and whether Viettel's template name matches the
portal's form.

### 5.3 Data model (working names)

| Model / field | Content |
|---|---|
| **`l10n_vn.einvoice.batch`** | one import: `company_id`, `direction` (sale / purchase), `date_from`, `date_to`, `import_date`, the imported file (attachment), `line_ids`; counts per match result |
| **`l10n_vn.einvoice.portal`** (the lines) | one GDT invoice: `batch_id`, seller tax code and name, buyer tax code and name, form, symbol, number, invoice date, untaxed amount, VAT amount, total, portal status, portal check result; **`move_id`** (the matched Odoo invoice); **`match_state`** (§5.4); amount differences |
| `account.move` (vendor bills) | `l10n_vn_supplier_invoice_form`, `l10n_vn_supplier_invoice_symbol`, `l10n_vn_supplier_invoice_number`; plus `l10n_vn_portal_ids`, the inverse of `move_id`, so a filter can find invoices with no portal row |

The portal rows are records of their own, not just transient matching results:
- **Evidence (R5):** what was checked and when.
- **Matching becomes a link,** so the reconciliation list is an ordinary list view.
- **A status that changes** shows when the period is re-imported.

The Odoo side needs no new record type: it is `account.move` as it stands.

### 5.4 Matching rules

For each portal row of a batch, look for a posted `account.move` of the batch's company with the same
key: customer invoices and credit notes for a sales batch, vendor bills and refunds for a purchase
batch.

| `match_state` | When |
|---|---|
| `matched` | key found; untaxed amount, VAT and total equal; portal status valid |
| `amount_diff` | key found; an amount differs (the differences are stored) |
| `status_diff` | key found; the portal shows the invoice cancelled, replaced or adjusted while Odoo holds it posted and unchanged |
| `portal_only` | no Odoo invoice with that key: missing from the books, or booked without its form, symbol or number |
| `duplicate` | the key matches more than one Odoo invoice |

**Odoo-only** (R3) is not a row state, since there is no portal row. It is a search on `account.move`:
posted in the batch's company and period, of the batch's direction, with **no `l10n_vn_portal_ids`**.
It is shown as a smart button on the batch.

To keep that list meaningful, the search covers only documents that can be on the portal:
- **Purchases:** vendor bills from partners with a Vietnamese tax code. Imports, foreign suppliers
  and purchases from individuals are excluded.
- **Sales:** customer invoices of companies that issue through SInvoice.

The exact filter is open question O5.

**Amounts:** VND has no decimals, so the comparison is exact. A tolerance of 1 VND per amount absorbs
rounding (O4). **The period** is the invoice date (`invoice_date`), not the accounting date, because
the portal lists invoices by issue date.

### 5.5 Views and access

- **Batches:** list and form. The form has an *Import* button (the `excel_import_export` wizard), the
  lines grouped by `match_state`, and an *Odoo only* smart button.
- **Portal invoices:** list with filters per `match_state` and direction. A row opens its matched
  invoice.
- **Vendor bill form:** the three supplier invoice fields beside *Bill Reference*. The portal rows
  linked to it go in a tab or a smart button.
- **Menu:** *Accounting → Review* (or *Reporting*): *E-Invoice Reconciliation*.
- **Access:** import and matching for `account.group_account_manager`; reading for
  `account.group_account_user`. Record rules by company, since each batch belongs to one company.

## 6. Decisions

| # | Decision |
|---|---|
| D1 | **The GDT export is the source; Odoo does not download it** (§4) |
| D2 | **The import uses `excel_import_export`,** with a template shaped like the portal's export and a post-import hook that runs the matching (§5.1). No parser of our own |
| D3 | **Portal rows are records,** grouped in import batches per company, direction and period (§5.3) |
| D4 | **Both sides, one model:** sales and purchases differ only by `direction` and the documents searched |
| D5 | **The key is seller tax code + form + symbol + number,** normalised (§5.2). Vendor bills gain the three fields |
| D6 | **Odoo-only is a search, not a record** (§5.4) |
| D7 | **Re-importing a batch replaces its rows and re-matches** (`excel_import_export`'s default) |

## 7. Steps (provisional)

| # | Scope | Waits on |
|---|---|---|
| 1 | Models, the supplier invoice fields on vendor bills, access, the batch and portal list views | — |
| 2 | The XLSX template and its instructions; the import from the batch form | **O1, the export sample** |
| 3 | Matching, `match_state`, the Odoo-only search, the smart buttons | O2–O5 |
| 4 | Later: draft vendor bills from portal-only rows; a check at posting time | step 3 in use |

## 8. References

| Source | Used for |
|---|---|
| `oca/server-tools/excel_import_export` (read from source) | Template import, line replacement, post-import hook (§5.1) |
| `odoo/addons/l10n_vn_edi_viettel` | Sales-side invoice number and symbol fields; seller-side scope only |
| [MISA meInvoice, input-invoice software](https://www.meinvoice.vn/tin-tuc/10905/phan-mem-hoa-don-dien-tu-dau-vao-misa-meinvoice/) | How the market handles purchase invoices (§3) |
| [MISA SME, input invoices from the tax portal](https://sme.misa.vn/351069/cach-lay-hoa-don-dau-vao-tren-trang-thue-dien-tu/) | The portal's sales and purchase lookup (§4) |
| [meInvoice, looking up e-invoices](https://www.meinvoice.vn/tin-tuc/771/tra-cuu-hoa-don-dien-tu/) | Export options reported (§4) |
| [LawNet, authenticated e-invoices](https://lawnet.vn/chinh-sach-thue/en/are-e-invoices-required-to-have-an-authentication-code-in-vietnam-9826.html) | Coded vs uncoded invoices (§1) |
| [EY, changes from 1 June 2025](https://www.ey.com/en_vn/technical/tax/tax-and-law-updates/tax-alert-april-2025-changes-to-invoicing-regulations-effective-from-1-june-2025) | Decree 70/2025 amending Decree 123 |

## 9. Open questions

| # | Question | Settles |
|---|---|---|
| **O1** | **The portal's export file:** sheet name, header row, column names and order, date and number formats, whether sales and purchases share one layout. *Missing: download one month of each and add them to this note* | The XLSX template (step 2), the portal model's fields |
| O2 | How the export writes the form, symbol and number; whether Viettel's template name matches the portal's form | The matching key (§5.2) |
| O3 | The portal's status and check-result values (e.g. *mới, thay thế, điều chỉnh, bị thay thế, bị điều chỉnh, đã hủy*; with code / without code) | `status_diff` (§5.4) |
| O4 | Whether a 1 VND tolerance per amount is right, or exact equality | `amount_diff` |
| O5 | Which vendor bills belong in the Odoo-only search: by partner country, by tax code, by journal | The Odoo-only list (§5.4) |
| O6 | Does an invoice cancelled or replaced in a later month change its row in the original month's export, or appear only in the later month? | Whether earlier months need re-importing |
| O7 | With the accountant: the buyer's obligations and the consequences of booking an invalid invoice | §1 |
| O8 | Whether each invoice's XML can be exported in bulk | Step 4's draft bills |
