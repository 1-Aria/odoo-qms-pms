# Material Ownership v2 — Processing Model

Nov 23, 2026 · @Peter · Status: draft for review (no spec, script or code yet)

Replaces the transfer model of `Material Ownership Transfer — Design.md` (v1). The trading company will not
sell or invoice the stock it left in the garment company. That stock stays its own, and the garment company
works it as a subcontractor (*gia công*). This note settles the model, the books, the Odoo mechanics and the
one-off conversion of today's mixed stock, and ends with a handoff for the next session.

---

## 1. Background

- The garment company (company 1, Công ty TNHH SX TM Quang Phương, MST 1602237713) was a branch of the trading
  company (company 2, Công ty TNHH DV TM Quang Phương, MST 0317253698) from about 2025 and became independent
  around 24 Oct 2026. The books were closed into 33889 and the stock revalued at that date (memory:
  *accounting-cutover-2026*, *stock-valuation-correction-2026*).
- v1 assumed the trading company would sell that stock to the garment company over time, invoicing per batch of
  sales orders (`sale_material_ownership`). On 22 Nov the trading company said it cannot: its own records do not
  separate the stock it uses from the stock it transferred, so it cannot sell or invoice it.
- It will instead move its purchasing to the garment company, so the garment company buys more and more of its
  own materials from suppliers, with their e-invoices. Over time the stock "purifies" into the garment
  company's.
- The garment company has issued no sales e-invoice of its own yet: the 14 customer invoices since the cutover
  were never sent to SInvoice and were deleted (Peter, 2026-11-18).

---

## 2. The model

### 2.1 Ownership

| Stock | Owner | In the garment company's books |
|---|---|---|
| Everything not bought by the garment company from a third party: the stock of 24 Oct, the trading company's goods received since | **Trading company** | Not valued; held in quantity for processing |
| Bought by the garment company from a third party (rule §5.3) | **Garment company** | Valued, AVCO, real time |

### 2.2 One owner per manufacturing order (D-V2-1)

Every MO belongs to one owner, and so does everything it produces. No finished good is split.

| MO type | Components | Finished goods | Who sells them |
|---|---|---|---|
| **Own production** | Garment-owned stock only | Garment-owned, valued | The garment company, with its e-invoice |
| **Processing for the trading company** | The trading company's stock first; garment stock only where the trading company's runs out | Trading-company-owned, not valued | The trading company, with its e-invoice. The garment company invoices it the processing fee and any garment material used |

The asymmetry is the point: garment material may go into the trading company's orders, because the garment
company invoices it; trading-company material never goes into the garment company's orders, because that would
be a purchase the trading company will not invoice. An own-production MO is made only when garment-owned stock
covers it in full (Peter, 2026-11-22).

### 2.3 Rejected: buying the trading company's material by journal entry

Peter's first idea (2026-11-22): for a sale to a third party, compute the trading company's material in it with
`sale_material_ownership` and "buy" it by a journal entry offset against the processing fees the trading company
owes. Rejected: a sale of goods between companies needs the seller's e-invoice; an entry records the economics
but is not a legal purchase, so the material in the output stays without legal input, and the trading company
would make sales it never declares. An offset agreement settles invoiced debts; it cannot replace the invoice.

---

## 3. Flows and entries (from the conversion on)

| Flow | Entry in the garment company's books |
|---|---|
| Trading-company goods received | None. Received with the trading company as owner |
| Garment purchase from a supplier, with e-invoice | Dr 1520 (via 3399) / Cr 331, Dr 1331 |
| Own-production MO | Dr 1541 / Cr 1520; Dr 1550 / Cr 1541, plus conversion (`mrp_bom_conversion_cost`) |
| Processing MO on trading-company material only | No stock entry. Labour and overhead stay in 622/627, matched by the processing fee |
| Processing MO also using garment material | That material's cost leaves stock (Dr 632 / Cr 1520, or through 1541); it is invoiced to the trading company |
| Delivering processed goods (to the trading company or to its customer on its instruction) | None. The trading company invoices its customer |
| Monthly settlement | Garment invoice to the trading company: processing fees per product + garment material used, VAT. Dr 131 / Cr 511, Cr 33311. Offset against what the garment company owes it, under the contract |
| Sale of own production | Ordinary customer invoice and delivery |

Valuation stays clean by owner: partner-owned goods create no valuation layer, so AVCO never mixes them. The
stock report grouped by *Owner* shows quantities per owner; the valuation report shows only the garment
company's stock (Peter's question, 2026-11-23).

---

## 4. Odoo mechanics (checked in the code)

| Fact | Reference |
|---|---|
| A move line whose owner is not the company's partner is left out of valuation | `odoo/addons/stock_account/models/stock_move_line.py:121-130`; `stock_move.py:700-706` |
| By default a move reserves from **any** owner's stock, oldest first: the reservation passes no owner, and the quant domain then has no owner filter | `odoo/addons/stock/models/stock_move.py:1957`; `odoo/addons/stock/models/stock_quant.py:761-787` |
| OCA `stock_owner_restriction` (available, not installed) restricts reservation per operation type: *Standard behavior*, *Unassigned owner* (company stock only), *Picking partner*, *Picking partner or unassigned owner* (partner first, then company). Default *Standard behavior*, so installing it changes nothing until types are set | `oca/stock-logistics-workflow/stock_owner_restriction/models/stock_picking_type.py:10-17`, `models/stock_move.py:27-79` |
| Its owner comes from the picking (or the destination picking); its own comment says MOs need extra logic | same file, `:38-46` |
| OCA `purchase_order_owner` (available, not installed) puts an owner on a PO and passes it to the receipt | `oca/purchase-workflow/purchase_order_owner` |
| `stock_picking_type_partner_owner` (ours, installed) makes an operation type's transfers owned by their partner, e.g. *Resupply From Customer* | `docs/modules/stock_picking_type_partner_owner.md` |
| Core sets no owner on an MO's finished goods (to confirm in the spec) | `odoo/addons/stock/models/stock_move.py` `_prepare_move_line_vals` |

**To build (one small module, working name `mrp_production_partner_owner`):** an owner on manufacturing operation
types; two types, *Own production* (reserve company stock only) and *Processing for the trading company* (owner
the trading company: reserve its stock first, then company stock; finished goods owned by it), applied to the
MO's component moves, its *Pick Components* transfer and its finished moves; and a record of garment material
consumed in processing MOs for the monthly invoice. It depends on `stock_owner_restriction`, which `-i` installs.

`sale_material_ownership` is superseded: ownership lives in stock by owner. It is not used by the conversion
(its rule counts e-invoices, the new rule counts the seller, §5.3) and is uninstalled after the run.

---

## 5. The conversion

### 5.1 Principle

One scripted run, check and commit modes, rehearsed on `prod_copy` like the revaluation and the P00097
correction. Past MOs and entries are not edited: correcting entries dated on the conversion date put every
balance where it belongs, and a register lists what to invoice the trading company.

### 5.2 Date and inputs

- **Date:** the day of the run (Peter, 2026-11-22), with a month-end accounting date (e.g. 30 Nov) for clean periods.
- **No physical count** (Peter): Odoo's quantities are taken as correct, after the fixes in §6.
- **Inputs:** the ownership rule (§5.3); optionally a list of POs in the trading company's name known to hold a
  real vendor's goods, kept garment-owned at the PO price (§5.3); accountant decisions marked *(acct)*.

### 5.3 Ownership of received quantities

| Received PO line quantity | Owner |
|---|---|
| PO vendor is a third party (not the trading company) | Garment, billed or not, e-invoice or not |
| PO vendor is the trading company, line billed to a third party (re-attributed: HTC, Việt Thành, Hoài Nguyễn) | Garment |
| PO vendor is the trading company, in the optional known-vendor list | Garment, at the PO price |
| PO vendor is the trading company, no third-party bill | Trading company |
| Stock on hand on 24 Oct (from before the separation) | Trading company |

Not yet received quantities are not stock: when they arrive after the run they come in through the ordinary
*Receipts* type, owned by the company and valued.

### 5.4 Replay per material (D-V2-2)

The history since 24 Oct is in Odoo, so the split uses **actual** consumption, not norms. Per material, in date
order from 24 Oct, using warehouse totals (not single locations):

1. Trading-company pool = on hand on 24 Oct + trading-company receipts since; garment pool = garment receipts (§5.3).
2. Every consumption (MO components, consumption transfers, scrap, raw material sold as such) is treated as
   processing for the trading company: it takes the trading-company pool first, then the garment pool.
3. Garment material taken in step 2 is **garment material used in the trading company's orders**: quantity and
   value at the garment cost, into the register.
4. End pools per material = the split of today's on-hand quantity. A difference between the pools and the
   on-hand quantity (losses, input errors) goes to the trading company first *(open: confirm)*.

All MOs since 24 Oct (687 done, 237 in progress, 62 confirmed on 18 Nov) are the trading company's (Peter, 2026-11-23).

### 5.5 Entries (all dated the conversion date)

Each valued quantity that turns out to be the trading company's carries a book value made of up to three parts,
each sent to its own place:

| Part of the value | Debit | Credit |
|---|---|---|
| Trading-company material (all of it for stock existing on 24 Oct) | 33889 | The asset it sits in: 1520, 1541, 1550, or 1599 for goods delivered without invoice |
| Trading-company material received since 24 Oct, still credited to 3399 | 3399 | 1520 |
| Garment material in the trading company's goods (register) | 632 | The same asset; matched by the garment invoice to the trading company |
| Garment conversion absorbed into those goods (`mrp_bom_conversion_cost`) | the production cost accounts it was absorbed from *(acct)* | The same asset; matched by the processing fees |

Then:

- The trading company's quantities become **owned by it, not valued**: per product and location, the
  company-owned quant is removed and a trading-company-owned quant created (inventory adjustment in inventory
  mode with owner; the valuation counterpart routed to the accounts above). Exact mechanism: in the script spec.
- **Remaining garment stock is revalued to its actual invoice prices** (Peter, 2026-11-23), against 632 or 33889 *(acct)*.
- **Open MOs** (in progress, confirmed) are unreserved and reserved again under the new rule, taking the trading
  company's stock first. Their WIP (1541: 238,854,669 on 18 Nov) follows the table above.
- **33889 after the run** holds the true open position with the trading company, expected small: the 6 Nov
  revaluation credits and any residue *(acct)*.

Balances on 18 Nov (`prod_copy` = production backup 18 Nov 02:00): 33889 −11,962,116,812; 1520 3,597,313,011;
1541 238,854,669; 1550 6,967,421,140; 1599 574,519,415; 3399 −563,429,844.

### 5.6 Outputs and checks

- A report per material (pools, split, garment material used in the trading company's orders, value), per open
  MO, and per account (before, entries, after).
- The register for the garment invoice to the trading company: garment material used, by order or MO and
  product; processing fees per product once the fee list exists.
- Checks: garment-owned quantities equal the garment pools; valued stock equals the ledger for 1520/1541/1550;
  1599 and the trading company's share of 3399 at zero; no negative quant; the uniform location outside the
  warehouse.

### 5.7 After the run: late attribution (D-V2-3)

A PO in the trading company's name that turns out to hold a real vendor's goods:

1. The vendor's bill goes on the PO lines with its e-invoice, vendor changed on the bill (HTC, Việt Thành pattern).
2. The quantity still on hand changes owner to the garment company, valued at the bill price, against 3399.
3. The quantity already consumed in the trading company's orders is garment material used: next invoice to it.

Scripted like `material-ownership/p00097_vietthanh.py` if it recurs.

---

## 6. Before the run

| Item | Detail | Who |
|---|---|---|
| Negative stock, all in **WH/Pre-Production** (18 Nov) | MAT01390 −16,050 m; MAT01787 −5,380 m; WIP00928 −558; MAT01687 −226.56 m; MAT01609 −215; MAT01812 −180.56 m; WIP01928 −1. MOs consumed more than *Pick Components* brought; the warehouse totals are likely right. Fix: internal transfer WH/Stock → WH/Pre-Production, or a stock adjustment if the material really was missing | Peter's staff |
| CSM00323 | Valuation layers hold 16 units at value 0, stock 0. Not a material; tidy later | — |
| Zero-cost materials | None on hand; 7 in active BoMs, to list | Claude lists, Peter prices |
| P00100 (Hoài Nguyễn) | Receive what arrived (backorder for the missing roll); bill the full `invoice2.xml` (1C26TAA-503) to Hoài Nguyễn; drop the spare part SPPT00018; rounding line without tax on 6320; XML attached | Peter, before the run |
| Other POs in the trading company's name with real vendors | Left as they are, counted as the trading company's; optional known-vendor list; otherwise late attribution (§5.7) | Peter |
| POs from real vendors not yet received or billed | Nothing to do: garment-owned when they arrive | — |
| Nhà Bàng (P00091, P00103) | Material at the subcontracting location (≈ 227 M) and the hammocks are the trading company's. Bills without VAT (fiscal position *Hộ cá nhân – không hóa đơn*); the fee is a garment cost, recovered through the processing fee | Peter |
| Uniform location | `WH/Consumptions` moved under *Virtual Locations* on production (Peter, 2026-11-18); the run's checks confirm it | — |
| The trading company's POs P00098–P00106 | Receipts of its goods; their bills were deleted (Peter, 2026-11-18); no bills | — |

---

## 7. The processing contract

The fee is per product (Peter, 2026-11-23); Claude extracts the product list (finished products made or sold
since 24 Oct, with quantities) for Peter to price. The contract should also cover:

- **Title:** the trading company owns its materials and the goods made from them; the garment company holds them
  for processing.
- **Garment material in its orders:** used only where its stock runs out; priced at garment cost plus an agreed
  margin; invoiced to it.
- **Norms and allowed wastage** (*định mức, hao hụt*); who bears losses beyond them.
- **Delivery and acceptance records** (*biên bản giao nhận*) for material in and goods out.
- **Monthly statement and settlement;** a written **offset clause** (*bù trừ công nợ*).
- **The material reconciliation report** at the end of each contract (*quyết toán nguyên vật liệu gia công*).
- **Quality and rework.**
- **A transitional clause** covering work since 24 Oct.
- **Related-party pricing:** fees and margins at arm's length *(acct)*.

Invoicing: an e-invoice cannot be backdated; it carries the day it is signed. November work invoiced in November
is fine; October work invoiced in November is late *(acct)*. The trading company invoices its own customers for
S00263–S00280 (Peter, 2026-11-23: it can).

---

## 8. Decisions

| # | Decision | By |
|---|---|---|
| D-V2-1 | One owner per MO: own production (garment stock only) or processing for the trading company (its stock first, then garment stock, invoiced) | Peter, 2026-11-22 |
| D-V2-2 | The conversion splits stock by replaying actual consumption since 24 Oct, the trading company's pool first | Peter, 2026-11-23 |
| D-V2-3 | Unknown attributions count as the trading company's; late attribution after the run (§5.7) | Peter, 2026-11-23 |
| D-V2-4 | All MOs since 24 Oct, open ones included, are the trading company's | Peter, 2026-11-23 |
| D-V2-5 | No physical count; conversion date = the day of the run, month-end accounting date | Peter, 2026-11-23 |
| D-V2-6 | Remaining garment stock revalued to actual invoice prices in the run | Peter, 2026-11-23 |
| D-V2-7 | The journal-entry purchase of trading-company material is rejected (§2.3) | Peter, 2026-11-22 |
| D-V2-8 | Most of 33889 is the trading company's, not the garment company's | Peter, 2026-11-22 |
| D-V2-9 | Conversion accounts: garment material in the trading company's goods, conversion absorbed into them and the revaluation of garment stock go to 6320; whatever happened to its goods since 24 Oct (deliveries without invoice, the 6 Nov revaluation's 1541 part, inventory gains and losses, scrap) goes to 33889; 1541 is filled by the November closing (`material-ownership/conversion_spec.md` §10) | Peter, 2026-11-24 |
| D-V2-10 | The sales orders since 24 Oct (S00263–S00329) are the trading company's sales: cancelled after the run, never invoiced by the garment company. Its goods leave by a delivery type with *Goods Owner* = the trading company, without a sales order; the garment company's own sales keep *Delivery Orders*, restricted to its own stock | Peter, 2026-11-24 |
| D-V2-11 | The trading company's goods come in by a receipt type owned by it, without a purchase order; purchase orders are only for the garment company's own purchases, in the real seller's name | Peter, 2026-11-24 |
| D-V2-12 | Monthly invoice to the trading company: processing fees for the goods made plus the garment material used; the fees must cover the processing cost | Peter, 2026-11-24 |
| D-V2-13 | Uniforms: the garment company makes its own or buys them from the trading company (its e-invoice): a *Xuất hàng Công ty TM* transfer out of the trading company's stock and a purchase order to it received as the garment's, then *Consumption* | Peter, 2026-11-24 |
| D-V2-14 | Subcontractors (Nhà Bàng) process the trading company's material through the subcontracting flow, its goods owned by it; their fees are a garment cost (6277 through their fiscal position, 3399 → 6277) recovered in the processing fee | Peter, 2026-11-24 |

## 9. Open items

1. Fee list per product (needs Claude's product list).
2. Accountant *(acct)* items: the conversion part's accounts (§5.5), the revaluation counterpart, the 33889
   residue, related-party pricing, late invoices.
3. Losses and differences in the replay: trading company first, or proportional (§5.4).
4. Where processed goods go: back to the trading company's warehouse (Bình Tân) or to its customers directly.
5. The 7 zero-cost materials in BoMs.
6. The negative stock investigation.

---

## 10. Handoff (for the next session)

**State on 23 Nov 2026.** Nothing of v2 is built. Production runs `sale_material_ownership` 18.0.1.4.0 (v1;
demo batch MTB/2026/0001 cancelled; later batches only for viewing). `stock_picking_type_partner_owner` is
installed. `prod_copy` holds production as of 18 Nov 02:00 (restored by Claude with Peter's standing permission
to restore R2 backups into `prod_copy` for inspection; strip the backdoor after each restore, memory
*db-backdoor-incident-2026*). Corrections already done on production: P00097 → Việt Thành
(`material-ownership/p00097_vietthanh.py`), HTC bill on P00099 + P00101 (1C26THC-170), five trading-company bills
and 14 customer invoices deleted, uniform location moved.

**Files.** This note; v1 `docs/Accounting/Material Ownership Transfer — Design.md` (history); spec
`docs/modules/sale_material_ownership.md`; scripts and XMLs in `Odoo-Build/material-ownership/` (outside the
repo); the revaluation scripts in `Odoo-Build/revaluation-conversion/`.

**LIVE on production since 25 Nov 2026, about 22:50.** Conversion committed (MISC/2026/11/0006, dated 30 Nov;
0 failed checks): 1520 201,185,673 (38 materials ours), 1550 −6, 1599 0, 3399 +46,705,186 (bills awaiting goods),
33889 −7,067,360, 1541 −505,224,992 (to be filled by the November closing), 6320 +717,583,533; register 368 lines,
227,796,013 (`material-ownership/out_prod/`). Modules `stock_picking_type_partner_owner` 18.0.1.3.0,
`stock_owner_restriction`, `mrp_production_partner_owner` 18.0.1.1.0; setup committed (499 open MOs owned by the
trading company, S00263–S00329 cancelled, types and route per `Processing for an Owner — Design.md` §5);
`sale_material_ownership` uninstalled. Verified on the post-go-live backup (25 Nov 22:55). Staff guide:
`docs/Procedures/Processing — Step-by-step Guide.md`.

**State on 24 Nov 2026.** Conversion script `material-ownership/ownership_conversion.py` with its spec
`conversion_spec.md`; check run on `prod_copy` (production backup 24 Nov 17:11) clean, accounting decisions D-V2-9.
Module specs written: `docs/modules/mrp_production_partner_owner.md` (step 1) and
`docs/modules/stock_picking_type_partner_owner.md` step 2 (*Goods Owner* on operation types).

**Next, one deliverable at a time, with Peter's review in between:**

1. Peter reviews this note with his accountant; open items §9.
2. ~~Claude: the product list for the fees and the 7 zero-cost materials~~: done 2026-11-23 from `prod_copy` (18 Nov),
   `material-ownership/processing_fee_products.csv` (29 styles, blank fee column), `processing_fee_variants.csv`
   (753 variants) and `zero_cost_materials_in_boms.csv` (7 materials, blank price column). Peter fills them in.
3. Claude: module spec `docs/modules/mrp_production_partner_owner.md` (§4), on `stock_owner_restriction`.
4. Claude: conversion script spec, then the script, check mode on a freshly restored `prod_copy`; Peter reviews
   the reports with the accountant.
5. Peter: the fixes in §6; then the run on production, the module installed and the operation types set the same day.
6. After the run: uninstall `sale_material_ownership`; monthly invoice to the trading company from the register.
