# VN E-Invoice — Design

Oct 28, 2026 · @Peter · Status: draft

Vietnamese e-invoices as records in Odoo, read from their XML. A module of its own,
`l10n_vn_einvoice`, outside the QMS-PMS and IE-MES suites, depending only on `account` and `l10n_vn`.
It is the base of `l10n_vn_einvoice_reconcile` (`VN E-Invoice Reconciliation — Design.md`), which
reads the shared rules from here: the e-invoice record, its key and how the key is normalised.

The XML format is described field by field in `vn_einvoice_field_dictionary.json` (from QĐ 1233/QĐ-CT,
format 2.1.1, and the samples in `samples/`). The dictionary is the format reference. This document
decides what Odoo stores and what it is called. Where the dictionary's *odoo* column names a field,
that is a proposal.

## 1. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| E1 | **A legal invoice is a record** | Each XML read into Odoo gives one e-invoice record holding its key, parties, totals and the original file |
| E2 | **A bill without a purchase order comes from its XML** | Uploading the XML on the Bills list creates the draft bill: supplier, reference, date, lines, VAT, totals checked |
| E3 | **Every bill can carry its e-invoice** | The XML can be attached to an existing bill, including one created from a purchase order, without changing it |
| E4 | **An invoice is read once** | Importing the same invoice twice into one company is refused and points to the first |
| E5 | **Old invoices survive format changes** | An invoice keeps the format version and the file it was read from; new versions add a reader, never replace one |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| The e-invoice record, its key, the original XML | In | E1, E4, E5 |
| Formats 2.1.0 and 2.1.1 | In | E5; the tax system stops accepting 2.1.0 after 31/12/2026 (§7) |
| Forms 1 (VAT) and 2 (sales), with their cash-register variants | In | What suppliers send a garment company |
| Attaching an XML to an existing vendor bill or customer invoice | In | E3 |
| Creating a draft vendor bill from an XML | In | E2 |
| VAT codes mapped to Odoo taxes, per company | In | E2; §5.3 |
| Replacement and adjustment invoices (`TTHDLQuan`) | Step 3 | Rare; a sample of each is needed first (§9) |
| E-invoices created from Viettel's files for invoices Odoo issued | Later | A bridge module with `l10n_vn_edi_viettel` (§9) |
| Product matching, units, supplier bank accounts | Later | Lines are text in v1 (§5.4) |
| Signature checking | Later | No XML-signature library in the image; the portal list confirms each invoice (§9) |
| Intake by e-mail, ZIP files, provider links | Later | Upload only in v1 |
| Forms 3–9 (public assets, reserves, tickets, delivery notes, commercial, receipts) | Out | Not received by this business. Form 7 returns with the issued side |

## 2. Facts that shape the design

Checked against the running code and database on 2026-10-28.

| Fact | Consequence |
|---|---|
| Odoo turns an attached file into a bill through one hook, `account.move._get_edi_decoder` (`account/models/account_move.py:4357`), which the UBL import also extends (`account_edi_ubl_cii/models/account_move.py:305`). It is reached from the Bills list's *Upload*, the journal dashboard and a journal's mail alias (`account/models/account_journal.py:944-984`) | **Creating a bill (E2) is one decoder** for files whose root is `HDon`. The alias path comes with it, untested |
| The hook skips a bill that already has lines (`account_move.py:4439-4441`), and the chatter path refuses a posted bill (`account_move.py:6493-6498`) | **Attaching to an existing bill (E3) needs its own entry:** a button with a small upload wizard |
| A `UserError` raised by a decoder leaves the empty draft bill with the error in its chatter; a `RedirectWarning` aborts the whole upload (`account_move.py:4466-4482`) | A duplicate raises a `RedirectWarning` to the existing e-invoice, so nothing is created. Other refusals are `UserError`s, as in the UBL import |
| Core's partner lookup falls back to e-mail, phone and name when the VAT does not match (`account/models/partner.py:1104-1129`) | **Not used.** The supplier is found by tax code only (§5.2) |
| **2 of 395 active partners have a tax code** on this database | Most first imports will not find their supplier. The bill is left without one until the accountant picks or creates it (§5.2). Filling in the tax codes of the regular suppliers once makes later imports automatic |
| Purchase taxes per company: `0%`, `VAT EXEMPTION`, `5%`, `8%`, `10%`, `10% (Asset)` (company 1 only) and `… Import` variants | A rate does not name one tax. **The mapping is configured, not guessed** (§5.3) |
| Both companies round tax per line; VND has 0 decimals; *Product Price* and *Discount* have 2 | Odoo's VAT can differ from the invoice by a few đồng, and a unit price with more decimals does not fit (§5.4) |
| UBL import overwrites the computed tax with the document's per-rate tax after creating the bill (`account_edi_ubl_cii/models/account_edi_xml_ubl_20.py:968-995`) | The same correction is applied with the XML's `LTSuat` rows (§5.4) |
| `_get_edi_creation` and `_disable_discount_precision` let an import build lines without recomputing at each one and without rounding the discount (`account_move.py:4330-4356`) | Lines are written inside it |
| Company tax codes: trading company `0317253698`; garment company `0317253698-001` on this database, `1602237713` in production | The buyer's tax code is checked against the company's own. Tests use the trading company, to which 4 of the 5 received samples are addressed |

## 3. The e-invoice record

**One record per legal invoice per company.** It is what the invoice says, read from the XML, and
holds the XML. The bill is Odoo's booking of it. They are linked, and live separately:

- the bill can be cancelled and recreated while the e-invoice stays;
- the key is unique in the database, which a field on `account.move` could not be, since a cancelled
  bill and its replacement would share it;
- reconciliation compares like with like: the tax office's row with the e-invoice. The e-invoice's link
  shows whether it is booked;
- the same record serves both directions: invoices received and invoices issued.

**One legal invoice may exist in both companies.** An invoice from the trading company to the garment
company is *issued* in one and *received* in the other. Each company holds its own record.

**What is stored is what something uses.** The dictionary lists about 110 tags. The rest stay in the
XML, which is the legal original, and become fields when a feature needs them. In particular, v1
stores none of the buyer's personal identifiers (`CCCDan`, `SHChieu`) and none of the free `TTKhac`
blocks, which can hold lookup codes (dictionary, *Extension*).

## 4. The key and its normalisation

**The key is company + seller tax code + form + symbol + number** (`NBan/MST`, `KHMSHDon`, `KHHDon`,
`SHDon`). A unique constraint holds it.

| Part | Normalised |
|---|---|
| Tax code | Spaces removed; the branch suffix kept (`0317253698-001` ≠ `0317253698`) |
| Form | One digit, as text |
| Symbol | Upper case, spaces removed |
| Number | Leading zeros removed (`00029704` = `29704`), stored as text |

The reconciliation module normalises the portal's columns the same way before comparing.

## 5. Data model and rules (working names)

### 5.1 `l10n_vn.einvoice`

| Field | From | Note |
|---|---|---|
| `company_id` | the bill's company, or the wizard's | |
| `direction` | computed: received when the buyer's tax code is the company's, issued when the seller's is | Neither: refused |
| `move_id` | | The bill or invoice; unique when set, `ondelete="set null"` |
| `state` | computed, stored: *not booked* (no document, or a cancelled one), *draft*, *booked* | Read by reconciliation |
| `format_version` | `TTChung/PBan` | Decides the reader |
| `form` | `KHMSHDon` | Key |
| `symbol` | `KHHDon` | Key |
| `number` | `SHDon` | Key |
| `invoice_date` | `NLap` | |
| `tax_authority_code` | `MCCQT` | Required when the symbol starts with `C`, absent with `K` |
| `seller_vat`, `seller_name` | `NBan/MST`, `NBan/Ten` | |
| `buyer_vat`, `buyer_name` | `NMua/MST`, `NMua/Ten` | Absent for consumers |
| `provider_vat` | `MSTTCGP` | Which provider's quirks apply |
| `currency_id`, `exchange_rate` | `DVTTe`, `TGia` | |
| `amount_untaxed`, `amount_tax`, `amount_total` | `TgTCThue`, `TgTThue`, `TgTTTBSo` | Form 2 has only the total |
| `attachment_id` | the uploaded file | **The e-invoice owns its own copy.** A bill's attachments are deleted with it. The filestore stores identical content once |

On `account.move`: the inverse `l10n_vn_einvoice_ids` (at most one, by the unique `move_id`), shown as
a smart button, and the attach button (§6.1).

### 5.2 The partner

- **Found by tax code only:** an exact match of the normalised `seller_vat` (received) or `buyer_vat`
  (issued) on commercial partners. Never by name: one sample's signing certificate names a different
  company under the same tax code (dictionary, `NBan/Ten`).
- **One match:** used. **None or several:** the bill is left without a partner, and the chatter says
  why. The e-invoice form offers *Create supplier*: name, tax code, address, phone and e-mail from the
  XML.
- **When a bill linked to an e-invoice is posted:** a partner with no tax code receives the
  e-invoice's, with a note in its chatter. A partner with a different tax code blocks the posting (D7).

**A mismatch can only come from a manual choice,** since the module itself finds partners by tax code
only:

1. the XML is attached to an existing bill (§6.1), whose partner was chosen when the bill or its
   purchase order was made;
2. the accountant picks the partner of a bill that was imported without one;
3. the partner of a draft bill is changed after the import.

The posting check covers all three in one place. One legitimate case also lands here: a supplier's
branch invoices under its own tax code (`…-001`) while Odoo holds only the head office. The VAT return
needs the branch's code, so the fix is a partner for the branch.

### 5.3 VAT codes: `l10n_vn.einvoice.tax`

One row per company and VAT code (`TSuat`, dictionary *codes*: `0%`, `5%`, `8%`, `10%`, `KCT`,
`KKKNT`, `KHAC:…`, `CTTC`, `KTPVDC`, `KTGTT`), naming a purchase tax. **An empty tax means "no VAT"**
and is a choice, distinct from a missing row.

- A line whose code has no row stops the import, naming the code. The accountant adds the row and drops
  the file on the draft bill again. A bill with the wrong VAT is worse than no bill.
- Nothing is seeded. Which tax `10%` means (`10%` or `10% (Asset)`), and whether `KCT` is `VAT
  EXEMPTION` or no tax, is the accountant's call.
- Form 2 carries no VAT: its lines take no tax and need no rows.

### 5.4 Bill from XML

| Bill | From |
|---|---|
| Company, journal | the upload's journal. The buyer's tax code must be the company's |
| Partner | §5.2 |
| `ref` | `<symbol>-<number>`, e.g. `C26TQL-394` (the dictionary's proposal) |
| `invoice_date` | `NLap` |
| Currency | `DVTTe`; an inactive currency stops the import |

**Lines** follow the line type (`TChat`):

| `TChat` | Line |
|---|---|
| 1 goods/service, 5 special goods | ordinary line |
| 2 promotion | ordinary line, at its amount (usually 0) |
| 3 commercial discount | negative line: minus the absolute `ThTien` (O1) |
| 4 note | `display_type = line_note` |

- **Label** `THHDVu`; no product, so the account is the journal's default. The accountant adjusts
  it before posting.
- **The line's untaxed amount is `ThTien`,** exactly. Quantity `SLuong`, unit price `DGia` and the
  discount (`TLCKhau`, or `STCKhau` converted to a percentage) are used when they give `ThTien` at
  Odoo's precision. When they don't (fuel invoices differ by tens of đồng; prices with more than two
  decimals), the line becomes quantity 1 at `ThTien`, with the original quantity, unit and price in
  its label.
- **VAT:** the line's `TSuat` through §5.3.

**After the lines,** two checks:

1. **Tax per rate.** For each `LTSuat` row, the tax lines of the mapped tax are corrected to the row's
   `TThue`, as UBL does. The deductible input VAT is the amount on the invoice. A correction larger than
   1 đồng per line at that rate is not applied. It is reported instead (check 2).
2. **Totals.** `amount_untaxed`, `amount_tax` and `amount_total` are compared with the XML. A difference
   is written to the chatter and shown on the e-invoice. The bill stays a draft for the accountant.

The XML is attached to the bill, and the e-invoice keeps its own copy (§5.1).

## 6. Flows

### 6.1 Attach to an existing document (E3)

The button *Attach e-invoice* on a vendor bill, refund, customer invoice or credit note, in any state
except cancelled, opens a wizard with a file field.

1. The file is read (§7); refusals as in §8.
2. The wizard shows what was read beside the document: partner and tax code, date, untaxed amount,
   VAT and total, with differences highlighted.
3. *Attach* creates the e-invoice linked to the document. **The document is not changed.**

This is how bills from purchase orders get their e-invoice: the bill comes from the order as today,
then the supplier's XML is attached.

### 6.2 Create a bill (E2)

*Upload* on the Bills list, or a file dropped on the purchases journal or on a draft bill without
lines: the decoder (§2) reads the file, creates the e-invoice and fills the bill (§5.4).

### 6.3 Re-importing

| The key already has an e-invoice in this company… | Result |
|---|---|
| linked to a live document | Refused with a link to it (`RedirectWarning`); nothing is created |
| linked to a cancelled document, or to none | The existing e-invoice is linked to the new bill or document |

## 7. Format versions and schema changes

- **Each e-invoice keeps its `format_version` and its original XML.** Stored values are never re-read
  automatically.
- **One reader per version, kept forever.** The reader is chosen by `PBan`; an unknown version is
  refused with its number, never read by guess.
- **2.1.0 and 2.1.1 from the start.** QĐ 1233's transition: the tax system accepts both until
  31/12/2026 and only 2.1.1 after. The signature standard moves from DSig to XAdES by 09/04/2027.
  This doesn't affect v1, which doesn't check signatures. Between 2.1.0 and 2.1.1, the tags v1 reads
  are the same; those that differ (dictionary *status* `removed`, and `MNNNghe`, `LDDCTThe`) are not
  stored.
- **Fields are only added.** A tag dropped from a new version leaves its field empty on new records; a
  renamed tag feeds the same field.
- **Backfilling is possible.** When a later version needs data v1 did not store, a one-off script reads
  the kept XML files.

## 8. Refusals

| Case | Error |
|---|---|
| Root is not `HDon`, or the file is not XML | Not ours: the decoder returns nothing and core carries on |
| Unknown `PBan` | `UserError` naming the version |
| Form outside 1 and 2 | `UserError` naming the form |
| Neither party's tax code is the company's | `UserError` naming both tax codes |
| A received invoice uploaded as a customer invoice, or the reverse | `UserError` |
| Key already imported, linked to a live document | `RedirectWarning` to it (§6.3) |
| A VAT code without a mapping row (bill creation only) | `UserError` naming the code |
| Inactive currency | `UserError` |
| Coded symbol (`C…`) without `MCCQT` | `UserError`: the file is not the tax office's version |

## 9. Later

- **Viettel bridge (`l10n_vn_einvoice_viettel`, auto-install with `l10n_vn_edi_viettel`).** When
  Viettel returns the signed XML of an invoice Odoo sent (`l10n_vn_edi_sinvoice_xml_file_id`), the
  issued e-invoice is created and linked. Needs a Viettel XML sample (O3).
- **Replacement and adjustment invoices (step 3).** Stored relation (`TTHDLQuan`: nature, related form,
  symbol, number, date, reason); link to the related e-invoice when present; positive adjustments as
  bills, negative ones and commercial discounts as refunds against the original bill. The original bill
  is never cancelled automatically. Several related invoices (`TCHDon` 3, 4) are left to the accountant.
- **Products and units:** `MHHDVu` through the supplier's product codes, `DVTinh` through a mapping
  table.
- **Supplier bank accounts:** `STKNHang` proposed, never trusted automatically.
- **Signature checking:** `lxml` and `cryptography` are in the image, so DSig can be checked without
  new libraries; XAdES needs more. It is worth it only if the portal check proves not to be enough.

## 10. Decisions

| # | Decision |
|---|---|
| D1 | **One e-invoice record per legal invoice per company,** separate from the bill and linked to it (§3; Peter, 2026-10-28) |
| D2 | **The key is company + seller tax code + form + symbol + number,** normalised (§4), unique in the database |
| D3 | **The e-invoice owns the original XML;** stored fields are an index of it (§3, §7) |
| D4 | **One reader per format version, never removed;** unknown versions refused (§7) |
| D5 | **Bill creation is a decoder on core's import hook;** attaching is a wizard (§2, §6) |
| D6 | **Partners are found by tax code only,** never created silently (§5.2) |
| D7 | **Posting a bill whose partner's tax code differs from its e-invoice's seller is blocked** (§5.2). A wrong seller tax code in the VAT return is a compliance error, not a preference (Peter, 2026-10-28) |
| D8 | **VAT codes map to taxes through a per-company table, seeded empty** (§5.3) |
| D9 | **A line's untaxed amount is `ThTien`;** the per-rate tax is the XML's (§5.4) |

## 11. Steps (provisional)

| # | Scope |
|---|---|
| 1 | The e-invoice model, the VAT-code table, access and views; readers for 2.1.0 and 2.1.1; the attach wizard (§6.1); re-import rules (§6.3) |
| 2 | Bill creation (§6.2, §5.4); partner rules and the posting check (§5.2) |
| 3 | Replacement and adjustment invoices (§9) |
| 4 | Later: the Viettel bridge module |

Tests read the files in `samples/`, with the trading company (`0317253698`) as the buyer. The sample
addressed to `0317253698-001` tests the wrong-company refusal, and the trading company's own invoice
tests the issued direction. No 2.1.1 file exists yet, so 2.1.1 fixtures are 2.1.0 samples edited per
the dictionary, replaced when real ones arrive (O2). Tests that create partners or companies are
`post_install`.

## 12. References

| Source | Used for |
|---|---|
| `vn_einvoice_field_dictionary.json` | Every tag, its meaning, requirement per form, the code tables |
| `Quyết-định-1233-QĐ-CT.docx` | Format 2.1.1; the transition dates (§7) |
| `samples/` | Six XML invoices (2.1.0) and two recreated portal lists. The lookup codes in three files are replaced by `REDACTED`, so their signatures no longer verify |
| `odoo/addons/account/models/account_move.py` | Import hook, existing-line and posted-bill rules, error handling, EDI creation context (§2) |
| `odoo/addons/account/models/account_journal.py` | Upload entry point (§2) |
| `odoo/addons/account/models/partner.py` | Core partner lookup, not used (§5.2) |
| `odoo/addons/account_edi_ubl_cii` | Decoder pattern; per-rate tax correction (§5.4) |
| `odoo/addons/l10n_vn_edi_viettel` | Viettel's stored XML, for the bridge (§9) |

## 13. Open questions

| # | Question | Settles |
|---|---|---|
| O1 | Is `ThTien` on a commercial-discount line (`TChat` 3) written positive or negative? | §5.4; a sample with a discount line |
| O2 | Real 2.1.1 files, from suppliers after 01/01/2027 or from Viettel | The 2.1.1 fixtures (§11) |
| O3 | A Viettel XML sample | The bridge (§9) |
| O4 | Is "quantity 1 at `ThTien`" acceptable to the accountant when quantity × price does not give the amount? | §5.4 |
