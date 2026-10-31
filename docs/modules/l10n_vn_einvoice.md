# l10n_vn_einvoice

Vietnamese e-invoices as records, read from their XML: one record per legal invoice per company,
holding its key, parties, totals and the original file, linked to the bill or invoice that books it.
Step 1 reads the XML and attaches it to existing documents; step 2 creates vendor bills from it.
Design: `docs/Accounting/VN E-Invoice — Design.md`. Format reference:
`docs/Accounting/vn_einvoice_field_dictionary.json`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `l10n_vn.einvoice` and its key; `l10n_vn.einvoice.tax` (the VAT-code table, used from step 2); the reader for 2.1.0 and 2.1.1; the attach wizard and the re-import rules; the e-invoice on the bill and invoice forms; access, record rules, menus | done | 2026-10-28, three runs. First: `exit=255` before any test, the tests' import of `AccountTestInvoicingCommon` failing on the image (see *Tests*); the base rebuilt on `TransactionCase`. Second run: installed; UI check as an *Invoicing* user found *Attach* failing with `binascii.Error` — the preview decoded the file's size, the web client reading the saved wizard with `bin_size=True`; fixed with `_file_content` and `test_wizard_read_as_web_client`. Third: `-u`, `exit=0`, 26 tests, 0 failures; UI checked as an *Invoicing* user: the preview of `C26TQL394.xml` beside a draft bill with the total warning, *Attach* linking it, the *E-Invoice* smart button and the chatter copy, `C26TQL-394` *Draft* under *Vendors → E-Invoices*, the same file on a second bill refused |
| 2 | Vendor bills from XML through core's import hook (design §5.4, §6.2): lines, VAT through the VAT-code table, the per-rate tax correction, the totals check; the duplicate refusal as a `RedirectWarning`; partner by tax code and *Create Supplier*; the posting check (design D7); the amounts banner on the e-invoice | done | 2026-10-28/29, two runs. First: `-u`, 46 tests, 0 failures. Its log showed core's chatter hook trying to import the XML that *Attach* posts (D25): silent on step 1's empty draft, but with step 2's decoder an empty draft would be filled and a bill with lines or a posted one noted as not updated; fixed with `no_new_invoice` and `test_attach_never_imports`. Second: `-u`, `exit=0`, 47 tests, 0 failures; UI checked as an *Invoicing* user on the trading company: the VAT codes `8%` and `KKKNT` added by an administrator; *Upload* of `1_001_C26TAA_21013_8446.xml` giving five lines at 8% and 5,843,880 ₫ without a supplier and the chatter naming `0314071202`; *Create Supplier* setting the new partner; `K26TDB122621.xml` as 1 × 5,500,000 ₫ without VAT, the label holding the original figures; the second upload of `1_001…` refused with *Open E-Invoice* and no new bill; posting refused for a partner with another tax code; *Attach* on an empty draft leaving it empty with one message |
| 3 | Replacement and adjustment invoices (`TTHDLQuan`, design §9) | planned | |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §5.1: `direction` computed | a stored selection, set once when the XML is read | The company's tax code can change (the garment company moves to `1602237713`); a compute would flip the direction of every past record. The direction is a fact of the import |
| 2 | §6.3: a duplicate is refused with a `RedirectWarning` | step 1: `UserError` naming the e-invoice and its document | Only the step-2 upload needs to abort a whole import; the wizard creates nothing before it fails. The `RedirectWarning` comes with the decoder |
| 3 | §5.1: form 2 "has only the total" | form 2 stores `amount_untaxed` = total and `amount_tax` = 0 | A sales invoice carries no VAT (dictionary, `KHMSHDon` 2), and every comparison — the wizard's, step 2's, reconciliation's — reads the three amounts |
| 4 | §5.2: at posting, a partner with no tax code receives the e-invoice's | only when no other partner holds that tax code; otherwise the posting is refused, naming them (step 2) | A partner without a tax code picked while another holds it is most likely the wrong partner, and filling it would leave two partners with one tax code, which the next import then cannot resolve (§5.2's *several*) |
| 5 | §6.2: a file dropped on the purchases journal or a draft bill creates the bill | only for vendor bills (`in_invoice`); a file uploaded as a refund or a customer document is refused, and so is a replacement or adjustment invoice (step 2) | Refunds and adjustments are step 3 (design §9); customer invoices are issued by the provider, not read back into new documents (design §1) |

## Decisions

| # | Decision |
|---|---|
| D1 | **Tags are read without regard to namespace,** through lxml's `{*}` wildcard (`{*}DLHDon/{*}TTChung/{*}PBan`). The samples have none on `HDon`, the signatures use xmldsig's, and 2.1.1 files have not been seen |
| D2 | **The XML is parsed with core's options:** `etree.XMLParser(remove_comments=True, resolve_entities=False)`, as `account/models/ir_attachment.py:47` does for every imported file |
| D3 | **Amounts are parsed as `Decimal` from their text,** then stored as floats: providers write `5411000.0` and `795000.000000` (dictionary, `TgTTTBSo`). An empty or absent amount is 0 |
| D4 | **The normalisation helpers are module-level functions** in `models/l10n_vn_einvoice.py` — `normalise_vat`, `normalise_symbol`, `normalise_number` — so `l10n_vn_einvoice_reconcile` imports the same rules |
| D5 | **One reader method, `_read_v2_1`, is registered for both versions.** The tags step 1 reads are the same in 2.1.0 and 2.1.1 (design §7); a version that changes them gets its own method beside it |
| D6 | **Direction: seller first.** The company's tax code equal to the seller's makes the invoice *issued*, else equal to the buyer's makes it *received*; neither is refused |
| D7 | **The e-invoice owns the file;** the document gets a copy in its chatter, posted with the message announcing the link (design §5.1) |
| D8 | **The wizard reads the file as soon as it is chosen** and shows what it read beside the document. A refusal is shown as text in the wizard, and *Attach* is hidden while there is one; *Attach* reads the file again and raises the same refusal, so nothing depends on the preview |
| D9 | **Re-linking keeps the existing record and its file.** The new file is only posted on the new document. Two files with the same key are the same legal invoice |
| D10 | **`name` is `<symbol>-<number>`, stored** — `C26TQL-394`, the bill reference step 2 writes (design §5.4) |
| D11 | **Menus by direction:** *Customers → E-Invoices* lists issued ones, *Vendors → E-Invoices* received ones; both menus are visible to *Invoicing* users, who attach and (from step 2) upload. The VAT codes sit under *Configuration → Accounting*, beside the taxes |
| D12 | **Access mirrors `account.move`** (`account/security/ir.model.access.csv:40-42`): *Readonly* reads, *Invoicing* reads, writes and creates, *Administrator* also deletes. An e-invoice is evidence, so only the administrator removes one |
| D13 | **The decoder claims a file whose root is `HDon`** (step 2): `account.move._get_edi_decoder` returns `l10n_vn.einvoice._import_document` for it, else `super()`. The UBL override returns nothing for such a root (`account_edi_ubl_cii/models/account_move.py:248-314`: no `CrossIndustryInvoice` tag, no `CustomizationID`, no `UBLVersionID`), so the two do not compete whatever their order |
| D14 | **Upload refusals are `UserError`s, a duplicate is a `RedirectWarning`** (step 2, design §2). Core turns a decoder's `UserError` into a message on the empty draft bill, which keeps the uploaded file (`account/models/account_move.py:4466-4482`, `account/models/account_journal.py:971-984`); once the cause is fixed, the file dropped on that bill's chatter runs the decoder again (`account_move.py:6490-6502`). A `RedirectWarning` is re-raised (`:4467-4468`), so the request fails and nothing is created; the dialog's button opens the e-invoice (an action dict, as `account/models/company.py:521-530` passes one) |
| D15 | **The partner is found by exact tax code** (step 2): `res.partner` searched with `vat` equal to the normalised tax code, `parent_id` empty, within `_check_company_domain(company)`. Core's `_retrieve_partner` is not used: it falls back to e-mail, phone and name (`account/models/partner.py:1104-1129`), and names are unreliable (dictionary, `NBan/Ten`). A partner whose stored tax code holds spaces is not found |
| D16 | **A line's untaxed amount is `ThTien`, exactly** (step 2, design D9). Quantity, unit price and discount are kept when, rounded to Odoo's precisions (`Product Unit of Measure`, `Product Price`; the discount unrounded under `_disable_discount_precision`, `account_move.py:4347-4356`), they give `ThTien` in the currency's rounding; otherwise the line is 1 × `ThTien` with the original figures in its label. Decided before the line is written, so no line is ever rewritten |
| D17 | **The per-rate correction is applied per mapped tax** (step 2, design §5.4): the `TThue` of every `LTSuat` row whose code maps to the same tax are summed, compared with that tax's lines, and the difference added to the first of them inside `_get_edi_creation`, as UBL does (`account_edi_ubl_cii/models/account_edi_xml_ubl_20.py:968-995`). It is applied when it is at most one unit of the currency's rounding per product line carrying that tax — 1 đồng per line in VND — and reported otherwise. Codes mapped to no tax have nothing to correct |
| D18 | **Totals are reported, not enforced** (step 2): a difference goes into the bill's import message and shows on the e-invoice as a banner (`amounts_differ`), and the bill stays a draft for the accountant |
| D19 | **The posting check runs before `super()._post()`** (step 2), on the documents that carry an e-invoice: vendor documents against the seller's tax code, customer documents against the buyer's; an issued invoice to a consumer, without a buyer tax code, is not checked. Filling a partner's empty tax code is done with `sudo()`, since writing partners needs *Contact Creation* (`odoo/odoo/addons/base/security/ir.model.access.csv:73`) and the fill follows from the check rather than from the user's edit; it is logged on the partner |
| D20 | ***Create Supplier* uses the user's own rights** (step 2): creating a partner is an ordinary edit, and a user without *Contact Creation* gets Odoo's usual refusal |
| D21 | **The VAT-code table takes purchase taxes that exclude VAT from the price** (step 2): lines are written with `ThTien`, an untaxed amount. A constraint refuses a sale tax and a price-included one (`account.tax.price_include`, `account/models/account_tax.py:127`) |
| D22 | **Lines are read by a second per-version registry,** `_l10n_vn_einvoice_line_readers` (step 2), beside the header readers of D5, so step 1's header reading is unchanged |
| D23 | **Core's purchase-order match is left to run** (step 2). After a decoder succeeds, core links the bill to purchase orders (`account_move.py:4457-4460`); with `purchase` installed and no order reference, its last resort takes the one open order of that vendor with the same total and replaces the bill's lines with the order's (`purchase/models/account_invoice.py:432-442`, `:461-465`). An uploaded e-invoice of a PO purchase thus lands on its order when the supplier is found and the totals agree. The import message and the corrections describe the lines as read, before that replacement; the e-invoice's `amounts_differ` is computed live and shows the result |
| D24 | **An uploaded file is not posted twice** (step 2): core already posts it on the new bill (`account_journal.py:981-984`), so `_import_document` calls `_link_or_create` with `notify=False` and writes its own import message instead |
| D25 | **The attach message is posted with `no_new_invoice`** (step 2). Core's chatter hook reads every file posted on a draft or posted bill as a possible import (`account_move.py:6452-6502`) and stops only on that flag (`:6491`), which core's own upload sets for the same reason (`account_journal.py:981-984`). Without it, attaching to an empty draft would run the decoder and fill the bill, against design §6.1; a bill with lines or a posted one would get core's "not updated from the attachment" note |

## Folder structure

```
l10n_vn_einvoice/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── l10n_vn_einvoice.py
│   ├── l10n_vn_einvoice_tax.py
│   └── account_move.py
├── wizard/
│   ├── __init__.py
│   ├── l10n_vn_einvoice_attach.py
│   └── l10n_vn_einvoice_attach_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── l10n_vn_einvoice_security.xml
├── views/
│   ├── l10n_vn_einvoice_views.xml
│   ├── l10n_vn_einvoice_tax_views.xml
│   └── account_move_views.xml
├── tests/
│   ├── __init__.py, common.py
│   ├── test_l10n_vn_einvoice_read.py
│   ├── test_l10n_vn_einvoice_attach.py
│   ├── test_l10n_vn_einvoice_bill.py                     # 2
│   └── data/   1602181122_1C26TTD_130.xml, 1_001_C26TAA_21013_8446.xml,
│               2_001_C26TMX_41_10860.xml, C26TQL394.xml, K26TDB122621.xml,
│               invoice_xml_0317253698_C26TQP_2160.xml
└── readme/ DESCRIPTION.md, USAGE.md
```

The files in `tests/data/` are copies of the first six samples (kept outside the repo in `Odoo-Build/accounting-samples/old/`), lookup codes redacted.

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - E-Invoice Records` |
| `summary` | `Vietnamese e-invoices read from their XML, one record per legal invoice, linked to bills and invoices` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Accounting/Localizations` |
| `countries` | `["vn"]` |
| `depends` | `account`, `l10n_vn` |
| `data` | `security/l10n_vn_einvoice_security.xml`, `security/ir.model.access.csv`, `wizard/l10n_vn_einvoice_attach_views.xml`, `views/l10n_vn_einvoice_views.xml`, `views/l10n_vn_einvoice_tax_views.xml`, `views/account_move_views.xml` |
| `installable` | `True` |

The wizard's views load before `account_move_views.xml`, whose button calls the wizard's action.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models`, `from . import wizard` |
| `models/__init__.py` | `from . import l10n_vn_einvoice`, `from . import l10n_vn_einvoice_tax`, `from . import account_move` |
| `wizard/__init__.py` | `from . import l10n_vn_einvoice_attach` |
| `tests/__init__.py` | `from . import test_l10n_vn_einvoice_read`, `from . import test_l10n_vn_einvoice_attach`, `from . import test_l10n_vn_einvoice_bill` (step 2) |

## Access — `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_l10n_vn_einvoice_readonly` | `model_l10n_vn_einvoice` | `account.group_account_readonly` | 1 | 0 | 0 | 0 |
| `access_l10n_vn_einvoice_invoice` | `model_l10n_vn_einvoice` | `account.group_account_invoice` | 1 | 1 | 1 | 0 |
| `access_l10n_vn_einvoice_manager` | `model_l10n_vn_einvoice` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_tax_readonly` | `model_l10n_vn_einvoice_tax` | `account.group_account_readonly` | 1 | 0 | 0 | 0 |
| `access_l10n_vn_einvoice_tax_invoice` | `model_l10n_vn_einvoice_tax` | `account.group_account_invoice` | 1 | 0 | 0 | 0 |
| `access_l10n_vn_einvoice_tax_manager` | `model_l10n_vn_einvoice_tax` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_l10n_vn_einvoice_attach` | `model_l10n_vn_einvoice_attach` | `account.group_account_invoice` | 1 | 1 | 1 | 1 |

D12. *Administrator* implies *Invoicing* (`account/security/account_security.xml:78-82`).

## Record rules — `security/l10n_vn_einvoice_security.xml`

| XML id | Model | Domain | Global |
|---|---|---|---|
| `l10n_vn_einvoice_company_rule` | `model_l10n_vn_einvoice` | `[('company_id', 'in', company_ids)]` | yes |
| `l10n_vn_einvoice_tax_company_rule` | `model_l10n_vn_einvoice_tax` | `[('company_id', 'in', company_ids)]` | yes |

## Models

### `l10n_vn.einvoice` — `models/l10n_vn_einvoice.py`

`_name = "l10n_vn.einvoice"`, `_description = "Vietnamese E-Invoice"`, `_inherit = ["mail.thread"]`,
`_order = "invoice_date desc, id desc"`, `_check_company_auto = True`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `compute="_compute_name"`, `store=True`, `index="trigram"` (D10) |
| `company_id` | Many2one → `res.company` | `required=True`, `readonly=True`, `index=True`, `default=lambda self: self.env.company` |
| `direction` | Selection `[("received", "Received"), ("issued", "Issued")]` | `required=True`, `readonly=True` (divergence 1) |
| `move_id` | Many2one → `account.move` | `string="Document"`, `readonly=True`, `index=True`, `copy=False`, `ondelete="set null"`, `check_company=True`, `tracking=True` |
| `state` | Selection `[("not_booked", "Not Booked"), ("draft", "Draft"), ("booked", "Booked")]` | `compute="_compute_state"`, `store=True`, `index=True` |
| `format_version` | Char | `string="Format Version"`, `required=True`, `readonly=True` — `PBan` |
| `form` | Char | `string="Form"`, `required=True`, `readonly=True` — `KHMSHDon` |
| `symbol` | Char | `string="Symbol"`, `required=True`, `readonly=True` — `KHHDon` |
| `number` | Char | `string="Number"`, `required=True`, `readonly=True` — `SHDon`, leading zeros removed |
| `invoice_date` | Date | `string="Invoice Date"`, `required=True`, `readonly=True` — `NLap` |
| `tax_authority_code` | Char | `string="Tax Authority Code"`, `readonly=True` — `MCCQT` |
| `seller_vat` | Char | `string="Seller Tax Code"`, `required=True`, `readonly=True`, `index=True` — `NBan/MST` |
| `seller_name` | Char | `string="Seller"`, `readonly=True` — `NBan/Ten` |
| `buyer_vat` | Char | `string="Buyer Tax Code"`, `readonly=True`, `index=True` — `NMua/MST` |
| `buyer_name` | Char | `string="Buyer"`, `readonly=True` — `NMua/Ten` |
| `provider_vat` | Char | `string="Provider Tax Code"`, `readonly=True` — `MSTTCGP` |
| `currency_id` | Many2one → `res.currency` | `required=True`, `readonly=True` — `DVTTe` |
| `exchange_rate` | Float | `string="Exchange Rate"`, `readonly=True` — `TGia`; 1.0 when absent |
| `amount_untaxed` | Monetary | `string="Untaxed Amount"`, `readonly=True` — `TgTCThue` (divergence 3) |
| `amount_tax` | Monetary | `string="VAT"`, `readonly=True` — `TgTThue` |
| `amount_total` | Monetary | `string="Total"`, `readonly=True` — `TgTTTBSo` |
| `attachment_id` | Many2one → `ir.attachment` | `string="XML File"`, `readonly=True`, `copy=False`, `ondelete="restrict"` (D7): the file cannot be deleted while its record exists. Deleting the record deletes the file, since `unlink` removes a record's rows before its attachments (`odoo/odoo/models.py:4579`, `:4598`, `:4670`) |

| `move_partner_id` | Many2one → `res.partner` | step 2; `related="move_id.partner_id"`, `string="Document Partner"` — read by the form's *Create Supplier* button |
| `amounts_differ` | Boolean | step 2; `compute="_compute_amounts_differ"`, not stored |

`readonly=True` binds the views only; the reader writes the fields through the ORM.

| SQL constraint | Definition | Message |
|---|---|---|
| `key_unique` | `unique(company_id, seller_vat, form, symbol, number)` | `This e-invoice has already been read into this company.` |
| `move_unique` | `unique(move_id)` | `A document can carry only one e-invoice.` |

PostgreSQL lets several rows hold a NULL `move_id` under `move_unique`, which is what unlinked
e-invoices need.

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_name` | `@api.depends("symbol", "number")` | `f"{symbol}-{number}"` |
| `_compute_state` | `@api.depends("move_id", "move_id.state")` | `booked` when `move_id.state == "posted"`, `draft` when `"draft"`, else `not_booked` — no document, or a cancelled one |
| `_l10n_vn_einvoice_readers` | `@api.model` | `{"2.1.0": self._read_v2_1, "2.1.1": self._read_v2_1}` (D5) |
| `_read_xml` | `@api.model` | `_read_xml(content)` → a dict of field values: parse (D2), refuse a root that is not `HDon`; read `PBan` and pick its reader, refuse an unknown one; run the reader; `_check_read_values`; return the values without `company_id`, `direction`, `move_id` |
| `_read_v2_1` | `@api.model` | `_read_v2_1(root)` → the values in the table below |
| `_read_amount` | `@api.model` | `_read_amount(root, path, default=0.0)`: the tag's text through the module-level `_decimal(text, tag)` (D3), as a float; `default` when empty; an unparseable value refused. `_decimal` also reads the line amounts (step 2) |
| `_check_read_values` | `@api.model` | refuses, in this order: a form other than `1` or `2`; a missing date, symbol, number or seller tax code; a symbol starting with `C` and no `tax_authority_code` |
| `_get_direction` | `@api.model` | `_get_direction(values, company)` → `"issued"` or `"received"` by D6, comparing `normalise_vat(company.vat)`; refuses when neither matches |
| `_check_document` | `@api.model` | `_check_document(direction, move)`: refuses a cancelled document, and a document whose type does not fit the direction (`_attach_xml` step 3) |
| `_find_by_key` | `@api.model` | `_find_by_key(values, company)` → the e-invoice of `company` with the same `seller_vat`, `form`, `symbol` and `number`, searched with `sudo()` so a record rule cannot hide a duplicate |
| `_attach_xml` | `@api.model` | `_attach_xml(content, filename, move)` → the e-invoice. Steps below |
| `_parse_xml` | `@api.model` | step 2, taken out of `_read_xml`: `_parse_xml(content)` → `(root, version)` — parse (D2), refuse a root that is not `HDon`, read `PBan`. `_read_xml` calls it, then picks the header reader |
| `_get_reader` | `@api.model` | step 2; `_get_reader(readers, version)` → the version's reader from either registry, an unknown version refused |
| `_l10n_vn_einvoice_line_readers` | `@api.model` | step 2; `{"2.1.0": self._read_lines_v2_1, "2.1.1": self._read_lines_v2_1}` (D22) |
| `_read_xml_lines` | `@api.model` | step 2; `_read_xml_lines(content)` → `(lines, tax_rows)` through `_parse_xml` and the line reader of the version; an unknown version refused as in `_read_xml` |
| `_read_lines_v2_1` | `@api.model` | step 2; `_read_lines_v2_1(root)` → the lines and tax rows in the tables below |
| `_read_party` | `@api.model` | step 2; `_read_party(content, role)` → `{"name", "vat", "street", "phone", "email"}` from `DLHDon/NDHDon/<role>/` `Ten`, `MST` (normalised), `DChi`, `SDThoai`, `DCTDTu`; `role` `NBan` or `NMua` |
| `_tax_map` | `@api.model` | step 2; `_tax_map(company)` → `{code: tax}` over the company's `l10n_vn.einvoice.tax` rows, the tax an empty recordset for a row without one |
| `_find_partner` | `@api.model` | step 2; `_find_partner(vat, company)` → the partners found by D15 (any number) |
| `_link_or_create` | `@api.model` | step 2, taken out of `_attach_xml` steps 5–8: `_link_or_create(values, direction, content, filename, move, existing, notify=True)` → the e-invoice; the message with the file copy only when `notify` (D24): the already-carries check, the re-link or the creation with its file, the message on the document. `_attach_xml` and `_import_document` both call it; the duplicate check stays with the callers, each raising its own kind (divergence 2, D14) |
| `_import_document` | `@api.model` | step 2; the decoder: `_import_document(invoice, file_data, new)` → `True`. Steps below |
| `_line_gives_amount` | `@api.model` | step 2; `_line_gives_amount(quantity, price, discount, amount, currency)`: quantity and price rounded to `Product Unit of Measure` and `Product Price` (`float_round`), the subtotal rounded by the currency, compared with `amount` (D16) |
| `_bill_line_values` | `@api.model` | step 2; `_bill_line_values(line, taxes, currency)` → `(values, note)`: the `invoice_line_ids` values of one read line by the line table below, and the note for the import message when the line fell back to 1 × `ThTien`, else `None` |
| `_correct_taxes` | `@api.model` | step 2; `_correct_taxes(move, tax_rows, tax_map)` → the notes for the corrections not applied (D17). Runs inside `move._get_edi_creation()`; `sign` is 1 for a vendor bill (`account_edi_xml_ubl_20.py:992`) |
| `_compute_amounts_differ` | `@api.depends("move_id.amount_untaxed", "move_id.amount_tax", "move_id.amount_total", "move_id.currency_id", "amount_untaxed", "amount_tax", "amount_total", "currency_id")` | step 2; true when `move_id` is set and its currency differs, or any of the three amounts differs in `currency_id.compare_amounts` |
| `action_create_partner` | — | step 2; `ensure_one`; `received` only. `_read_party(attachment_id.raw, "NBan")` → a `res.partner` with `name`, `vat`, `street`, `phone`, `email`, `is_company=True`, `country_id` `base.vn`, created with the user's rights (D20); set as `move_id.partner_id` when the document is a draft without a partner; returns the partner's form |
| `action_open_document` | — | `ensure_one`; the `move_id`'s form (`account.action_move_in_invoice_type` or `account.action_move_out_invoice_type` by direction, read with `_for_xml_id`, `res_id` set, form view only) |

**Values read by `_read_v2_1`** — paths below `HDon`, each step `{*}`-prefixed (D1); text stripped,
empty treated as absent.

| Field | Path | Treatment |
|---|---|---|
| `format_version` | `DLHDon/TTChung/PBan` | as is |
| `form` | `DLHDon/TTChung/KHMSHDon` | as is |
| `symbol` | `DLHDon/TTChung/KHHDon` | `normalise_symbol` |
| `number` | `DLHDon/TTChung/SHDon` | `normalise_number` |
| `invoice_date` | `DLHDon/TTChung/NLap` | `fields.Date.to_date` of the first 10 characters; an unparseable date refused |
| `tax_authority_code` | `MCCQT` | as is |
| `seller_vat` | `DLHDon/NDHDon/NBan/MST` | `normalise_vat` |
| `seller_name` | `DLHDon/NDHDon/NBan/Ten` | as is |
| `buyer_vat` | `DLHDon/NDHDon/NMua/MST` | `normalise_vat`; absent for consumers |
| `buyer_name` | `DLHDon/NDHDon/NMua/Ten` | as is |
| `provider_vat` | `DLHDon/TTChung/MSTTCGP` | `normalise_vat` |
| `currency_id` | `DLHDon/TTChung/DVTTe` | the active `res.currency` of that `name`; none refused here, before `_check_read_values` |
| `exchange_rate` | `DLHDon/TTChung/TGia` | D3; 1.0 when absent |
| `amount_total` | `DLHDon/NDHDon/TToan/TgTTTBSo` | D3 |
| `amount_untaxed` | `DLHDon/NDHDon/TToan/TgTCThue` | D3; form 2: `amount_total` (divergence 3) |
| `amount_tax` | `DLHDon/NDHDon/TToan/TgTThue` | D3; form 2: 0 |

**`_attach_xml(content, filename, move)`**

1. `values = _read_xml(content)`.
2. `direction = _get_direction(values, move.company_id)`.
3. `_check_document(direction, move)`: the document must fit the direction —
   `move.is_purchase_document()` for *received*, `move.is_sale_document()` for *issued*, receipts
   excluded, the default of both (`account/models/account_move.py:5889-5900`). A cancelled document
   is refused.
4. `existing = _find_by_key(values, move.company_id)`. With a `move_id` that is not cancelled, it is
   refused, naming the e-invoice and its document (divergence 2).
5. A document already carrying another e-invoice is refused, before `move_unique` would raise.
6. An existing record is re-linked: `existing.move_id = move` (D9).
7. No existing record: create the e-invoice with `values`, `company_id`, `direction` and `move_id`;
   then an `ir.attachment` with `name=filename`, `raw=content`, `mimetype="application/xml"`,
   `res_model="l10n_vn.einvoice"`, `res_id` the new record; write it to `attachment_id`.
8. `move.with_context(no_new_invoice=True).message_post(body=…, attachments=[(filename, content)])` —
   body `"E-invoice %(name)s attached."` with the e-invoice's `name` (D7, D25).

**`_import_document(invoice, file_data, new)`** (step 2)

1. `content = file_data["content"]`, `filename = file_data["filename"]`; `values = _read_xml(content)`.
2. `direction = _get_direction(values, invoice.company_id)`. Unless it is `received` and
   `invoice.move_type == "in_invoice"`, refused (divergence 5).
3. Refused when the root holds `DLHDon/TTChung/TTHDLQuan` (divergence 5).
4. `existing = _find_by_key(...)`. With a `move_id` that is not cancelled and is not `invoice`:
   `RedirectWarning` with the message below, the e-invoice's form as action (`res_model`, `res_id`,
   `views` form), button *Open E-Invoice* (D14).
5. `lines, tax_rows = _read_xml_lines(content)`; `tax_map = _tax_map(company)`. Form `1`: every
   line other than a note must have a code, and every code a row; the codes without a row are
   refused together. Form `2`: no codes are read.
6. `partners = _find_partner(values["seller_vat"], company)`: one is used; none or several are noted.
7. Within `invoice._get_edi_creation()`: write `partner_id` (when one), `ref` = the e-invoice name,
   `invoice_date`, `currency_id`, and `invoice_line_ids` from `_bill_line_values` for each line, in
   `STT` order, document order when `STT` is absent.
8. Within a second `invoice._get_edi_creation()`: `_correct_taxes` (D17).
9. The totals compared with `values` (D18).
10. `_link_or_create(values, "received", content, filename, invoice, existing, notify=False)` (D24).
11. One message on the bill: `"Created from e-invoice %(name)s."`, then the notes of 6–9 as a list.

Core then marks the new lines `is_imported` (`account_move.py:4456`), which keeps their taxes and
prices when the partner is changed later (`account/models/account_move_line.py:863`, `:883`).

**Lines read by `_read_lines_v2_1`** — each `DLHDon/NDHDon/DSHHDVu/HHDVu`; numbers as `Decimal` (D3),
absent ones as `None`.

| Key | Tag | Treatment |
|---|---|---|
| `kind` | `TChat` | as is |
| `sequence` | `STT` | `int`, else the line's position |
| `name` | `THHDVu` | as is |
| `uom` | `DVTinh` | as is, for the label only |
| `quantity`, `price` | `SLuong`, `DGia` | `Decimal`; their text kept as `quantity_text`, `price_text` for the label |
| `discount` | `TLCKhau` | `Decimal` percentage |
| `discount_amount` | `STCKhau` | `Decimal` |
| `amount` | `ThTien` | `Decimal`; 0 when absent (notes) |
| `code` | `TSuat` | stripped, upper case |

**Tax rows** — each `DLHDon/NDHDon/TToan/THTTLTSuat/LTSuat`: `code` (`TSuat`, as above), `amount`
(`ThTien`), `tax` (`TThue`, 0 when absent).

**Line values by `_bill_line_values`**

| `kind` | Values |
|---|---|
| `4` (note) | `display_type="line_note"`, `name` |
| `3` (commercial discount) | `name`, `quantity` 1, `price_unit` minus the absolute `amount`, the taxes |
| `1`, `2`, `5` | `name`, the taxes, and `quantity`, `price_unit`, `discount` by D16 — the discount is `discount` when present, else `discount_amount / (quantity × price) × 100` when both are positive, else 0 |

The D16 fallback is `quantity` 1, `price_unit` = `amount`, `discount` 0, and the label
`"<name> (<quantity_text> <uom> × <price_text>)"`; its note is
`"Line %(line)s: quantity × price does not give %(amount)s; entered as 1 × %(amount)s."` Taxes:
`[Command.set(tax_map[code].ids)]` on form 1, `[Command.clear()]` on form 2.

**Messages added to the bill's import message**

| Case | Text |
|---|---|
| No partner | `"No partner has tax code %(vat)s (%(seller)s). Choose the supplier, or use Create Supplier on the e-invoice."` |
| Several partners | `"Several partners have tax code %(vat)s: %(names)s. Choose the supplier."` |
| Correction not applied | `"VAT %(tax)s: the e-invoice says %(xml)s, the bill %(bill)s; the difference is more than rounding and was not corrected."` |
| Totals differ | `"The bill's totals differ from the e-invoice: untaxed %(untaxed)s / %(xml_untaxed)s, VAT %(tax)s / %(xml_tax)s, total %(total)s / %(xml_total)s."` |

**Refusals** are `UserError`s, with these messages:

| Case | Message |
|---|---|
| Not XML, or root not `HDon` | `"This file is not a Vietnamese e-invoice XML."` |
| Unknown version | `"E-invoice format version %(version)s is not supported."` |
| Form | `"Invoice form %(form)s is not supported: only VAT invoices (1) and sales invoices (2) are read."` |
| Coded symbol without code | `"Invoice %(symbol)s-%(number)s has a coded symbol but no tax authority code: this is not the tax authority's version of the file."` |
| Currency | `"Currency %(code)s is not active."` |
| Missing value | `"The e-invoice has no %(tag)s."` with the tag's name |
| No matching party | `"This e-invoice is between %(seller)s and %(buyer)s; neither is the tax code of %(company)s (%(vat)s)."` |
| Direction against the document | `"A received e-invoice can only be attached to a vendor bill or refund."` / `"An issued e-invoice can only be attached to a customer invoice or credit note."` |
| Cancelled document | `"An e-invoice cannot be attached to a cancelled document."` |
| Document already carries another | `"%(document)s already carries e-invoice %(name)s."` |
| Unreadable amount | `"The e-invoice has an unreadable amount in %(tag)s: %(value)s"` |
| Unreadable date | `"The e-invoice has an unreadable date: %(value)s"` |
| Duplicate | `"E-invoice %(name)s is already attached to %(document)s."` |
| Not a received vendor bill (step 2) | `"Only received e-invoices create vendor bills. Attach this one to its document with Attach E-Invoice."` |
| Replacement or adjustment (step 2) | `"E-invoice %(name)s replaces or adjusts another invoice, which is not created as a bill yet. Enter the bill by hand and attach the XML."` |
| Line without a code (step 2) | `"Line %(line)s of e-invoice %(name)s has no VAT code."` |
| Codes without a row (step 2) | `"VAT codes %(codes)s have no row in E-Invoice VAT Codes for %(company)s."` |
| Duplicate on upload (step 2) | `RedirectWarning`: `"E-invoice %(name)s is already on %(document)s."` |

**Normalisation helpers** (D4, design §4), all returning `""` for an empty value:

| Function | Behaviour | Examples |
|---|---|---|
| `normalise_vat(value)` | every whitespace removed; the branch suffix kept | `" 0317 253698-001 "` → `0317253698-001` |
| `normalise_symbol(value)` | whitespace removed, upper case | `" c26tql "` → `C26TQL` |
| `normalise_number(value)` | stripped; leading zeros removed, `"0"` kept | `00029704` → `29704`; `0` → `0` |

### `l10n_vn.einvoice.tax` — `models/l10n_vn_einvoice_tax.py`

`_name = "l10n_vn.einvoice.tax"`, `_description = "E-Invoice VAT Code"`, `_order = "company_id, code"`,
`_rec_name = "code"`, `_check_company_auto = True`

| Field | Type | Attributes |
|---|---|---|
| `company_id` | Many2one → `res.company` | `required=True`, `index=True`, `default=lambda self: self.env.company` |
| `code` | Char | `string="VAT Code"`, `required=True`, help: the rate code as the e-invoice writes it in TSuat — 0%, 5%, 8%, 10%, KCT, KKKNT, KHAC:… |
| `tax_id` | Many2one → `account.tax` | `string="Tax"`, `check_company=True`, `domain="[('type_tax_use', '=', 'purchase')]"`, `ondelete="restrict"`, help: the purchase tax for lines with this code; leave empty for lines that carry no VAT |

| SQL constraint | Definition | Message |
|---|---|---|
| `code_unique` | `unique(company_id, code)` | `This VAT code is already mapped in this company.` |

| Method | Decorator | Behaviour |
|---|---|---|
| `create` | `@api.model_create_multi` | `code` stripped and upper-cased in each values dict, then `super()` |
| `write` | — | the same when `code` is present |

| `_check_tax` | `@api.constrains("tax_id")` | step 2; a tax that is not `type_tax_use == "purchase"`, or is `price_include`, raises `ValidationError`: `"%(tax)s is not a purchase tax."` / `"%(tax)s includes VAT in the price, while e-invoice lines are untaxed amounts. Choose a tax that excludes it."` (D21) |

No rows are seeded (design §5.3, D8). Step 2 reads the table.

### `account.move` — `models/account_move.py`

`_inherit = "account.move"`

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_einvoice_ids` | One2many → `l10n_vn.einvoice` | inverse `move_id`, `string="E-Invoices"`, `copy=False` |
| `l10n_vn_einvoice_id` | Many2one → `l10n_vn.einvoice` | `compute="_compute_l10n_vn_einvoice_id"`, not stored, `string="E-Invoice"` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_l10n_vn_einvoice_id` | `@api.depends("l10n_vn_einvoice_ids")` | the first of `l10n_vn_einvoice_ids` (at most one, by `move_unique`) |
| `action_l10n_vn_einvoice_attach` | — | `ensure_one`; the wizard's action (`l10n_vn_einvoice.l10n_vn_einvoice_attach_action`, read with `_for_xml_id`) with `context` `{"default_move_id": self.id}` |
| `action_l10n_vn_einvoice_open` | — | `ensure_one`; the e-invoice's form, `res_id` `l10n_vn_einvoice_id` |
| `_get_edi_decoder` | — | step 2; `_get_edi_decoder(file_data, new=False)`: when `file_data["type"] == "xml"` and the root's local name is `HDon`, `self.env["l10n_vn.einvoice"]._import_document`; else `super()` (D13) |
| `_post` | — | step 2; `_post(soft=True)`: `self._l10n_vn_einvoice_check_partners()`, then `super()` |
| `_l10n_vn_einvoice_check_partners` | — | step 2; for each document with an e-invoice (D19): the tax code to hold is `seller_vat` (vendor documents) or `buyer_vat` (customer documents), none skipped; with `normalise_vat(commercial_partner_id.vat)` equal, nothing; empty, the partners holding that tax code (`_find_partner`) other than this one refuse the posting, else the code is written with `sudo()` and the partner gets `"Tax code %(vat)s set from e-invoice %(name)s when %(document)s was posted."`; different, the posting is refused |

**Posting refusals** (step 2), `UserError`:

| Case | Message |
|---|---|
| Different tax code | `"%(document)s: its partner %(partner)s has tax code %(partner_vat)s, but e-invoice %(name)s names %(vat)s. Choose the partner with that tax code, or correct the partner's."` |
| Code held elsewhere | `"%(document)s: its partner %(partner)s has no tax code, while %(others)s already hold %(vat)s, the tax code on e-invoice %(name)s. Choose that partner."` |

### `l10n_vn.einvoice.attach` — `wizard/l10n_vn_einvoice_attach.py`

`_name = "l10n_vn.einvoice.attach"`, `_description = "Attach E-Invoice"` (TransientModel)

| Field | Type | Attributes |
|---|---|---|
| `move_id` | Many2one → `account.move` | `string="Document"`, `required=True`, `readonly=True` |
| `file` | Binary | `string="XML File"`, `required=True` |
| `filename` | Char | |
| `error` | Text | `compute="_compute_preview"` |
| `preview_name`, `preview_seller_vat`, `preview_seller_name`, `preview_buyer_vat`, `preview_invoice_date`, `preview_amount_untaxed`, `preview_amount_tax`, `preview_amount_total` | Char, Char, Char, Char, Date, Monetary × 3 | `compute="_compute_preview"`; what was read; the amounts with `currency_field="preview_currency_id"` |
| `preview_currency_id` | Many2one → `res.currency` | `compute="_compute_preview"` |
| `partner_vat` | Char | `related="move_id.commercial_partner_id.vat"` |
| `partner_differs` | Boolean | `compute="_compute_preview"`: the document's partner tax code, normalised, differs from the seller's (vendor documents) or the buyer's (customer documents) |
| `date_differs` | Boolean | `compute="_compute_preview"`: `invoice_date` differs from the document's |
| `amounts_differ` | Boolean | `compute="_compute_preview"`: the total differs from the document's `amount_total` in the document's currency, beyond the currency's rounding |

| Method | Decorator | Behaviour |
|---|---|---|
| `_file_content` | — | `ensure_one`; the file's bytes, `base64.b64decode` of `file` read with `bin_size=False` and `bin_size_file=False`. A saved wizard is read back by the web client with `bin_size=True`, under which a Binary field holds its size, not its content (`odoo/odoo/fields.py:2532`, `:2604-2605`) |
| `_compute_preview` | `@api.depends("file", "move_id")` | empty values without a file; otherwise `_read_xml` on `_file_content()`, `_get_direction` and `_check_document`, a `UserError`'s message going to `error` and the preview fields left empty (D8). The duplicate and already-carries checks run only at *Attach* |
| `action_attach` | — | `ensure_one`; `self.env["l10n_vn.einvoice"]._attach_xml(self._file_content(), self.filename or "einvoice.xml", self.move_id)`; returns `{"type": "ir.actions.act_window_close"}` |

The comparisons inform; they do not block (design §6.1). Step 2's posting check is what stops a
mismatched partner.

## Views — `views/l10n_vn_einvoice_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_einvoice_view_list` | list | `name`, `invoice_date`, `seller_name`, `seller_vat`, `buyer_name`, `buyer_vat`, `amount_total`, `currency_id` (`column_invisible="True"`), `move_id`, `state` (badge: `decoration-success="state == 'booked'"`, `decoration-info="state == 'draft'"`, `decoration-warning="state == 'not_booked'"`), `company_id` (`groups="base.group_multi_company"`); `create="0"` |
| `l10n_vn_einvoice_view_form` | form | `create="0"`, `edit="0"`. Header: `state` as statusbar. Button box: `action_open_document` (`invisible="not move_id"`, icon `fa-file-text-o`, text *Document*). Title: `name`. Group *Invoice*: `direction`, `form`, `symbol`, `number`, `invoice_date`, `tax_authority_code`, `format_version`, `provider_vat`. Group *Parties*: `seller_name`, `seller_vat`, `buyer_name`, `buyer_vat`. Group *Amounts*: `amount_untaxed`, `amount_tax`, `amount_total`, `currency_id`, `exchange_rate`. Group *Booking*: `move_id`, `attachment_id`, `company_id` (`groups="base.group_multi_company"`). Chatter. Step 2: header button *Create Supplier* (`action_create_partner`, `groups="account.group_account_invoice"`, `invisible="direction != 'received' or state != 'draft' or move_partner_id"`); an `alert-warning` between the header and the sheet, `invisible="not amounts_differ"`: *The amounts differ from the document's.*; `move_partner_id` and `amounts_differ` invisible in the sheet |
| `l10n_vn_einvoice_view_search` | search | `name`, `seller_vat`, `seller_name`, `buyer_vat`, `tax_authority_code`; filters *Not booked* / *Draft* / *Booked* by `state`; group by `state`, `seller_name`, `invoice_date` (month) |
| `l10n_vn_einvoice_received_action` | window action | *E-Invoices*, `domain="[('direction', '=', 'received')]"` |
| `l10n_vn_einvoice_issued_action` | window action | *E-Invoices*, `domain="[('direction', '=', 'issued')]"` |

| Menu | Parent | Action | Sequence |
|---|---|---|---|
| `l10n_vn_einvoice_received_menu` | `account.menu_finance_payables` | received action | 90 |
| `l10n_vn_einvoice_issued_menu` | `account.menu_finance_receivables` | issued action | 90 |

## Views — `views/l10n_vn_einvoice_tax_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_einvoice_tax_view_list` | list | `editable="bottom"`: `code`, `tax_id`, `company_id` (`groups="base.group_multi_company"`) |
| `l10n_vn_einvoice_tax_action` | window action | *E-Invoice VAT Codes* |
| `l10n_vn_einvoice_tax_menu` | menu | parent `account.account_account_menu` (*Configuration → Accounting*, administrators, `account/views/account_menuitem.xml:49-51`), sequence 3 |

## Views — `views/account_move_views.xml`

One record, `view_move_form`, inheriting `account.view_move_form`.

| Position | Content |
|---|---|
| `//header` inside, last | button `action_l10n_vn_einvoice_attach`, `string="Attach E-Invoice"`, `type="object"`, `groups="account.group_account_invoice"`, `invisible="l10n_vn_einvoice_id or state == 'cancel' or move_type not in ('in_invoice', 'in_refund', 'out_invoice', 'out_refund')"` |
| `//div[@name='button_box']` inside | button `action_l10n_vn_einvoice_open`, `class="oe_stat_button"`, `icon="fa-file-code-o"`, `type="object"`, `invisible="not l10n_vn_einvoice_id"`, showing *E-Invoice*; the field `l10n_vn_einvoice_id` invisible beside it |

## Views — `wizard/l10n_vn_einvoice_attach_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_einvoice_attach_view_form` | form | `move_id` (readonly); `file` with `filename="filename"`; `filename` invisible; an `alert-danger` div holding `error`, `invisible="not error"`; group *Read from the file* (`invisible="not preview_name"`): `preview_name`, `preview_seller_name`, `preview_seller_vat`, `preview_buyer_vat`, `preview_invoice_date`, `preview_amount_untaxed`, `preview_amount_tax`, `preview_amount_total`, `preview_currency_id` invisible; beside it `partner_vat`; warnings as `alert-warning` divs: `partner_differs` — *The document's partner has a different tax code from the e-invoice.*; `date_differs` — *The invoice date differs from the document's.*; `amounts_differ` — *The total differs from the document's.* Footer: *Attach* (`action_attach`, `class="btn-primary"`, `invisible="error or not file"`), *Cancel* (`special="cancel"`) |
| `l10n_vn_einvoice_attach_action` | window action | `res_model="l10n_vn.einvoice.attach"`, `view_mode="form"`, `target="new"`, *Attach E-Invoice* |

## Tests

Both classes derive from `EInvoiceCase(TransactionCase)` in `tests/common.py`, which holds no test
methods. Both are `@tagged("post_install", "-at_install")`: the fixtures create a company and a
partner, core records later modules extend.

**Not `AccountTestInvoicingCommon`.** Importing anything from `odoo.addons.account.tests` runs that
package's `__init__`, which imports test files importing `odoo.addons.mail.tests.common`; mail's
`tests/__init__.py` imports its `discuss` subfolder, which the image's build deletes
(`images/odoo/Dockerfile:49`). The whole `-i` run then fails with
`ModuleNotFoundError: No module named 'odoo.addons.mail.tests.discuss'` (step 1, first run).

**Fixtures:** `_create_company(name, vat, chart=True)` creates a Vietnamese company (`base.vn`,
`base.VND`), links it to the test user's companies and loads the `vn` chart through
`account.chart.template.try_loading(..., install_demo=False)`, as core's helpers do
(`odoo/odoo/addons/base/tests/common.py:124-131`, `account/tests/common.py:295-303`). `setUpClass`
creates the test company with `vat` `0317253698`, the trading company's, to which four of the six
samples are addressed; puts it in the env's `allowed_company_ids`; and creates `partner_a`. The tests
run as the superuser, so they never meet the instance's e-invoices, taxes or journals; access is
tested with a user of its own. **Helpers:** `_sample(name)` returns the bytes of `tests/data/<name>`
through `file_open("l10n_vn_einvoice/tests/data/<name>", "rb")`; `_edited(name, old, new)` returns
them with one text replacement, asserting it occurred once; `_document(move_type, **values)` creates
a draft for `partner_a` dated 2026-10-01 with one untaxed line of 1,000, and `_bill()` /
`_customer_invoice()` call it; `_wizard(name_or_bytes, move)` creates `l10n_vn.einvoice.attach` with
`move_id` and the base64 `file`; `_attach(name_or_bytes, move)` runs it and returns the move's
`l10n_vn_einvoice_id`.

### `tests/test_l10n_vn_einvoice_read.py`

`TestEInvoiceRead(EInvoiceCase)`

| Test | Asserts |
|---|---|
| `test_normalise_helpers` | the three helpers on the examples of their table, and `""` for `None` and `"  "` |
| `test_read_vat_invoice` | `C26TQL394.xml`: version `2.1.0`, form `1`, symbol `C26TQL`, number `394`, date 2026-10-21, the code `0061B2D1564D8848E0B3F42D7B2A7D513A`, seller `0308965730`, buyer `0317253698`, provider `0100109106`, VND, rate 1.0, amounts 439,815,200 / 35,185,216 / 475,000,416 |
| `test_read_decimal_text` | `1_001_C26TAA_21013_8446.xml` writes `5411000.0`: read as 5,411,000 / 432,880 / 5,843,880 |
| `test_read_sales_invoice` | `2_001_C26TMX_41_10860.xml`, form `2` with only a total: untaxed 48,960,000, VAT 0, total 48,960,000 (divergence 3) |
| `test_read_uncoded` | `K26TDB122621.xml`, symbol `K…`: read, `tax_authority_code` empty |
| `test_read_version_2_1_1` | `C26TQL394.xml` with `<PBan>2.1.0</PBan>` replaced by `2.1.1`: read, `format_version` `2.1.1`, the same key and amounts |
| `test_unknown_version_refused` | version `9.9.9`: `UserError` naming it |
| `test_form_refused` | `<KHMSHDon>1</KHMSHDon>` replaced by `7`: `UserError` naming the form |
| `test_coded_without_code_refused` | `C26TQL394.xml` with its `MCCQT` element removed: `UserError` |
| `test_not_an_einvoice_refused` | `b"<Invoice/>"` and `b"not xml"`: `UserError` |
| `test_inactive_currency_refused` | `<DVTTe>VND</DVTTe>` replaced by a code of an inactive currency: `UserError` |

### `tests/test_l10n_vn_einvoice_attach.py`

`TestEInvoiceAttach(EInvoiceCase)`

| Test | Asserts |
|---|---|
| `test_attach_received_to_bill` | `C26TQL394.xml` on a draft bill: one e-invoice, `received`, linked, `state` `draft`, `name` `C26TQL-394`; its `attachment_id` belongs to the e-invoice (`res_model`, `res_id`) and holds the file; the bill's chatter has a message with a copy; the bill's partner, amount and `ref` unchanged |
| `test_state_follows_document` | after the bill is posted the e-invoice is `booked`; after `button_draft` and `button_cancel`, `not_booked` |
| `test_attach_issued_to_invoice` | `invoice_xml_0317253698_C26TQP_2160.xml` on a draft customer invoice: `issued`, linked; buyer empty |
| `test_wrong_company_refused` | `1602181122_1C26TTD_130.xml` (buyer `0317253698-001`) on a bill: `UserError`, no e-invoice |
| `test_direction_against_document_refused` | `C26TQL394.xml` on a customer invoice, and the issued sample on a bill: `UserError` each |
| `test_cancelled_document_refused` | on a cancelled bill: `UserError` |
| `test_duplicate_on_live_document_refused` | the same file on a second bill while the first is a draft: `UserError`; still one e-invoice, on the first bill |
| `test_relink_after_cancel` | the first bill cancelled, the file attached to a second: the same e-invoice record (same id), now on the second bill, its `attachment_id` unchanged (D9) |
| `test_document_deleted` | the draft bill deleted: the e-invoice remains, `move_id` empty, `not_booked`, file kept |
| `test_key_normalised` | `C26TQL394.xml` with `<SHDon>394</SHDon>` replaced by `00394`, on a second bill: refused as a duplicate of the first |
| `test_key_unique_in_database` | creating a second record with the first's key directly raises `IntegrityError` (`mute_logger("odoo.sql_db")`); the same key in a second company (`_create_company(..., chart=False)`) is accepted |
| `test_wizard_preview` | the wizard on a bill dated 2026-10-01 for 1,000 with `partner_a`'s VAT `0100109106`: `preview_name` `C26TQL-394`, `partner_differs`, `date_differs`, `amounts_differ` all true, `error` empty; with `partner_a`'s VAT `0308965730`, `partner_differs` false; on a customer invoice, `error` holds the direction message and `preview_name` is empty |
| `test_wizard_read_as_web_client` | the wizard invalidated and read with `bin_size=True`, as the web client does after a save: no `error`, `preview_name` `C26TQL-394`; `action_attach` under the same context links the e-invoice |
| `test_access_invoicing_user` | a user with *Invoicing* only attaches a file to a bill (positive control) and reads the e-invoice; `unlink` on it raises `AccessError`; the VAT-code table is readable and not writable by that user |
| `test_vat_code_normalised_unique` | a row `" kct "` reads back `KCT`; a second `KCT` in the same company raises `IntegrityError` |

### `tests/test_l10n_vn_einvoice_bill.py` (step 2)

`TestEInvoiceBill(EInvoiceCase)`. **Fixtures:** a purchase tax *Test 8%* (`amount` 8, `type_tax_use`
`purchase`, price excluded) in the test company; VAT-code rows `8%` → that tax and `KKKNT` → no tax;
`supplier`, a partner with `vat` `0308965730` (the seller of `C26TQL394.xml`). **Helpers:**
`_upload(name_or_bytes, move_type="in_invoice")` creates an `ir.attachment` with the file and runs the
company's purchase journal's `create_document_from_attachment` with `default_move_type`, returning the
document of its action; `_replaced(content, old, new, count)` replaces every occurrence, asserting the
count.

| Test | Asserts |
|---|---|
| `test_upload_creates_bill` | `C26TQL394.xml`: one draft `in_invoice`; partner `supplier`; `ref` `C26TQL-394`; date 2026-10-21; one line `VẢI V.43771-A7+A0`, quantity 49,979, price 8,800, tax *Test 8%*, `is_imported`, the journal's default account; amounts 439,815,200 / 35,185,216 / 475,000,416; the e-invoice linked, `draft`, not `amounts_differ`; the import message starts *Created from e-invoice C26TQL-394* |
| `test_upload_lines_and_no_partner` | `1_001_C26TAA_21013_8446.xml`: five lines in `STT` order; amounts 5,411,000 / 432,880 / 5,843,880; no partner; the message names `0314071202` |
| `test_upload_fallback_line` | `K26TDB122621.xml` (180.92 × 30,400 = 5,499,968 against 5,500,000): one line of 1 × 5,500,000 whose label holds `180.92 Lít × 30400`, no tax (`KKKNT` → none); VAT 0, total 5,500,000; the message notes the line |
| `test_upload_sales_invoice` | `2_001_C26TMX_41_10860.xml`, form 2, with the VAT rows deleted: one line 2,040 × 24,000, no tax, total 48,960,000 |
| `test_tax_corrected_within_rounding` | `1_001…` with `432880.0` → `432881.0` (twice: the rate row and `TgTThue`) and `5843880.0` → `5843881.0`: VAT 432,881, total 5,843,881, no correction note, not `amounts_differ` |
| `test_tax_not_corrected_beyond_rounding` | the same with 432,890 and 5,843,890: VAT stays 432,880, the message notes the correction, the e-invoice `amounts_differ` |
| `test_missing_vat_code` | the `8%` row deleted, `C26TQL394.xml` uploaded: a draft bill without lines whose chatter names `8%`; no e-invoice. The row restored and the file posted on that bill's chatter: the bill is filled and linked |
| `test_duplicate_upload_redirects` | `C26TQL394.xml` uploaded twice: the second raises `RedirectWarning` (inside a savepoint); one e-invoice |
| `test_upload_after_cancelled_attach` | attached to a bill then cancelled; the upload links the same e-invoice record to the new bill |
| `test_attach_never_imports` | *Attach* on an empty draft, on a draft with one line, and on a posted bill: the empty draft stays without lines, and each document gains exactly one message, counted by a `mail.message` search, since core's notes are translated (D25) |
| `test_upload_refusals` | the issued sample, `1602181122_1C26TTD_130.xml` (another company), `C26TQL394.xml` with a `TTHDLQuan` block inserted after `HDCTTChinh`, and `C26TQL394.xml` uploaded with `default_move_type` `in_refund`: each a draft without lines whose chatter holds the refusal; no e-invoice |
| `test_partner_never_matched_by_name` | `supplier`'s tax code removed and a partner named exactly `CÔNG TY TNHH QUANG QUANG LINH` created: the bill has no partner |
| `test_several_partners` | a second partner with `0308965730`: no partner; the message says *Several partners* |
| `test_create_supplier` | `1_001…` uploaded; `action_create_partner`: a company partner `CÔNG TY CỔ PHẦN VIỆC LÀM 24H`, tax code `0314071202`, the seller's address and phone, country Vietnam; the bill's partner |
| `test_partner_change_keeps_taxes` | `1_001…` uploaded; `partner_a` set on the bill: the five lines keep *Test 8%* and their prices |
| `test_posting_fills_partner_vat` | `1_001…` uploaded; `partner_a` (no tax code) set; posting writes `0314071202` on `partner_a` and logs it there |
| `test_posting_refused_on_mismatch` | `C26TQL394.xml` uploaded; the partner changed to one with `0100000002`: posting raises `UserError`; the same through a bill with an attached e-invoice (step 1's path) |
| `test_posting_refused_when_code_held_elsewhere` | `1_001…` uploaded; a partner with `0314071202` created afterwards; `partner_a` set: posting raises `UserError` naming that partner |
| `test_posting_issued_to_consumer` | a customer invoice with the issued sample attached, buyer empty: it posts |
| `test_vat_table_refuses_unsuitable_taxes` | a row naming a sale tax, and one naming a price-included purchase tax: `ValidationError` each |
| `test_access_invoicing_user_upload` | a user with *Invoicing* only, no *Contact Creation*: uploads `1_001…`, sets `partner_a`, posts — the tax code is filled; *Create Supplier* raises `AccessError` for that user |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | What a Vietnamese e-invoice record is, that it is read from the invoice's XML (formats 2.1.0 and 2.1.1, forms 1 and 2), and that it links to the bill or invoice booking it |
| `readme/USAGE.md` | Attaching: *Attach E-Invoice* on a bill or invoice, choose the XML, check what was read, *Attach*. The lists under *Customers* and *Vendors*. The VAT codes under *Configuration → Accounting*. Step 2: *Upload* on the Bills list creates the draft bill; what to do when no supplier is found (*Create Supplier*, or choose one); the import message; the posting check |
