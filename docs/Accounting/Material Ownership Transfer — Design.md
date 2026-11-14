# Material Ownership Transfer — Design

Nov 14, 2026 · @Peter · Revised Nov 14, 2026 · Status: draft for review; module spec
`docs/modules/sale_material_ownership.md`

Who owns the materials in the garment company's stock, and how the rest passes from the trading
company to the garment company, one group of sales orders at a time. Module working name:
`sale_material_ownership`.

---

## 1. Purpose

The garment company (Odoo company 1, Công ty TNHH SX TM Quang Phương) separated from the trading company
(company 2, Công ty TNHH DV TM Quang Phương, the former parent) on 24 Oct 2026. The management rule
(Peter, 2026-11-14):

> Stock covered by a validated vendor bill is the garment company's. The rest still belongs to the
> trading company.

What makes a material legally owned is a vendor bill backed by a correct e-invoice, for goods received
(D11). The separation bill PRP/2026/10/0001 transferred materials only. The finished goods and cut panels
in the warehouse, and the materials no bill covers, are still the trading company's. The garment company
may only deliver and invoice goods it owns. The module therefore:

1. keeps a running **ownership balance per material**, in quantities;
2. groups confirmed sales orders into **transfer batches**, explodes them by BoM norms (*định mức*), nets
   each material against the balance and asks the trading company to invoice only the shortfall;
3. links the trading company's invoice (our vendor bill) to the batch and, once that bill is posted with
   its e-invoice, marks the batch's orders **covered**, which clears them for delivery and our
   e-invoices.

### Nature of the module (D10)

The module exists for one temporary purpose and is uninstalled when the transfer is done (§10). It is:

- **Self-contained.** It depends only on modules already installed and changes no core or OCA behaviour.
- **Suggestive.** It shows balances, requests and coverage, and warns. It blocks nothing outside its own
  records: deliveries, invoices and bills follow their usual flows.
- **Without lasting effect.** It never posts anything. The bills it prepares are ordinary drafts that the
  accountant checks and posts. Uninstalling it removes its batches and links and leaves every journal
  entry, bill and fiscal position as it is.

### Scope

- Company 1 only. Sales orders, BoMs, vendor bills and stock are all company 1's.
- Materials only: fabric, trims and packaging. The conversion done before 24 Oct is not transferred by
  this module (O6).
- Not in scope: offsetting payables against receivables (a written agreement, §6.4), the trading
  company's own books (O4), printing the delivery note.

---

## 2. Facts that shape the design

Checked on `prod_copy` (production as of 12 Nov 2026 20:48) and in `../odoo`, `../oca` and this repo.

### 2.1 The instance

| Fact | Source |
|---|---|
| PRP/2026/10/0001, 23 Oct, partner = the trading company (partner 7), 17,447,989,638 + VAT 1,744,798,967. 1,007 product lines, all from a purchase order (`purchase_line_id` set), posted to 3399 (GRNP, the stock input account), 6320 (packaging, then periodic) and 6273 | `account_move_line` |
| Material bills of company 1: PRP/2026/10/0001 and PRP/2026/10/0003 (23 Oct), BILL/2026/10/0001, BILL/2026/11/0001 and BILL/2026/11/0002 (since 24 Oct, all from the trading company). **None before 23 Oct.** Every line comes from a purchase order with a receipt, and no line is billed beyond what was received | `account_move`, `purchase_order_line` |
| **No bill has an e-invoice attached.** Production holds no `l10n_vn.einvoice` record at all, although `l10n_vn_einvoice` is installed | `l10n_vn_einvoice` |
| Material, WIP and finished-goods categories are AVCO (`average`) with real-time valuation in company 1; stock input = 3399, stock output = 1599, valuation 1520 (materials, packaging) and 1541 (WIP) | `product_category` |
| Anglo-saxon accounting is on in both companies | `res_company.anglo_saxon_accounting` |
| Active BoMs: 45 finished goods (44 `normal`, 1 `subcontract`, a hammock) and 40 cut panels (WIP, `normal`) | `mrp_bom` |
| Sales since 24 Oct: 14 confirmed orders (S00263–S00276), 12 invoiced, 2 confirmed on 12 Nov and not yet invoiced. Lines: finished goods, 2 raw-material lines and 1 cut-panel line | `sale_order` |
| **Company 2 keeps no records in Odoo:** no journal entries at all, no stock on hand, no sales or purchase orders, last stock move 19 May 2026 | `account_move`, `stock_quant`, `stock_move` |
| OCA `account_invoice_inter_company`, `purchase_sale_inter_company` and `purchase_sale_stock_inter_company` are installed, **switched off** in both companies (`intercompany_invoicing = False`, `so_from_po = False`) | `res_company` |
| No fiscal position exists yet | `account_fiscal_position` |
| Every UoM rounds to 0.01 | `uom_uom` |
| Stock value (12 Nov): materials 3.50 bn, packaging 58 M, cut panels 1.07 bn, finished goods 6.55 bn (hammocks 5.00 bn). 33889 balance −11,810,151,551 (credit) | `stock_valuation_layer`, `account_move_line` |

### 2.2 The code

| Behaviour relied on | Reference |
|---|---|
| `_bom_find` returns the first active BoM by `sequence, product_id, id` for the company (or no company), any type unless `bom_type` is given, and skips services | `odoo/addons/mrp/models/mrp_bom.py:351-394` |
| `explode` recurses only through **kit** sub-BoMs (`bom_type='phantom'`). A component with a `normal` BoM, such as a cut panel, is returned as a leaf, so the module recurses itself (as `ownership_balance.py` does) | `mrp_bom.py:405-408` |
| `explode` skips lines whose attribute values do not match the variant (`_skip_bom_line`), which the garment BoMs rely on | `mrp_bom.py:427`, `715-727` |
| `explode` rounds each leaf quantity **up** to the UoM rounding (0.01 here) | `mrp_bom.py:446-448` |
| On a vendor bill, a storable real-time product's line takes the product's **stock input** account, mapped through the bill's fiscal position | `odoo/addons/stock_account/models/account_move.py:266-277`; `odoo/addons/account/models/product.py:90-94` |
| A fiscal position maps account to account by its `account_ids` (`account_src_id` → `account_dest_id`) | `odoo/addons/account/models/partner.py:106-108`, `158-159`, `322-336` |
| A bill line without a purchase-order line makes no valuation layer and reconciles nothing: price differences are read from the PO line's done moves, and the anglo-saxon reconciliation stops when the bill has no stock moves | `odoo/addons/purchase_stock/models/account_move_line.py:12-16`, `32-47`; `stock_account/models/account_move.py:185-203`; `purchase_stock/models/account_invoice.py:160-168` |
| Confirming a purchase order creates a receipt | `odoo/addons/purchase_stock/models/purchase_order.py:117-119` |
| A PO line's `qty_received` and `qty_invoiced` are stored; so are a move's `amount_untaxed`, `amount_tax`, `amount_total` | `odoo/addons/purchase/models/purchase_order_line.py:55`, `61`; `odoo/addons/account/models/account_move.py:506-515` |
| A picking knows its sales order (`sale_id`) | `odoo/addons/sale_stock/models/stock.py:99-108` |
| A customer return marked *to refund* lowers the order line's `qty_delivered` | `odoo/addons/sale_stock/models/sale_order_line.py:326-360` |
| With *Lock Confirmed Sales* (`sale.group_auto_done_setting`) on, every order is locked at confirmation. The setting is off on the instance and no order is locked, but a rule may not rely on `locked` | `odoo/addons/sale/models/sale_order.py:1176`, `1183-1186` |
| `standard_price` is company-dependent and is the running average under AVCO | `odoo/addons/product/models/product_product.py:54-58` |
| With `intercompany_invoicing` on in both companies, posting a bill to a partner that is another company's partner creates the counterpart invoice in that company | `oca/multi-company/account_invoice_inter_company/models/account_move.py:28-41`, `49-74` |
| An e-invoice belongs to at most one document (`unique(move_id)`), has a `direction` (received / issued) and stores its amounts. `correction_state` (stored) is *replaced* once a replacing invoice is recorded. `amounts_differ` compares the three amounts with the document's (sign −1 on a refund) but is **not stored** | `addons/l10n_vn_einvoice/models/l10n_vn_einvoice.py:80-94`, `123-130`, `164-169`, `178-186`, `207-249` |
| Attaching an e-invoice XML to an existing bill (E3) compares partner, date and totals and leaves the bill unchanged | `docs/Accounting/VN E-Invoice — Design.md` §6.1 |

---

## 3. Decisions

| # | Decision | By |
|---|---|---|
| D1 | Ownership is tracked **per material, in quantities**, through the BoM norms: finished goods → cut panels → fabric, trims, packaging. A material sold as such counts itself. | Peter, 2026-11-14 |
| D2 | Materials are fungible. No bill line is paired with a sales line; a material is owned up to its balance. | Peter, 2026-11-14 |
| D3 | The transfer is made per **batch of confirmed sales orders**, at the sales-order stage. An order belongs to one batch (lines added later: O1). A helper adds all uncovered orders. | Peter, 2026-11-14 |
| D4 | The explosion of an order is **frozen** when the order joins a batch. | Peter, 2026-11-14 |
| D5 | Each material of a batch is first netted against the owned balance (the bills that count under D11, minus the materials already used by earlier batches). Only the rest is requested. | Peter, 2026-11-14 |
| D6 | Per batch, a document for the trading company lists the requested materials per sales order and in total, at Odoo's current unit cost. The trading company issues its e-invoice; our bill is linked to the batch; once it counts (D11), the batch's orders are covered. Quantity differences are shown. | Peter, 2026-11-14 |
| D7 | Delivery and our e-invoices come after the batch is covered. The module shows this; it does not enforce it (D10). | Peter, 2026-11-14 |
| D8 | The trading company's bills do not receive goods again: their lines post to 33889 through a dedicated fiscal position (stock input → 33889), at current unit cost, so 33889 is relieved by exactly the value the stock already carries. | Peter, 2026-11-14 |
| D9 | **No opening allocation.** The orders confirmed between 24 Oct and go-live are ordinary uncovered orders: *Add uncovered orders* puts them in the first batch, whose request covers what they used beyond the bills. Their trading-company invoice comes after the delivery; its date and wording are the accountant's call. Orders confirmed **before** 24 Oct are out of scope: a company setting, *Ownership Start*, marks the date (added 2026-11-14 after the first UI check, where the helper took every confirmed order ever). On production every order confirmed before 24 Oct was fully delivered before it (`prod_copy`, 12 Nov). | Peter, 2026-11-14 |
| D10 | The module is **temporary, self-contained, suggestive and without lasting effect** (§1). | Peter, 2026-11-14 |
| D11 | **What counts as owned** is a posted vendor bill line of a material whose bill carries a correct e-invoice, for goods received (§4). Bills are counted automatically, never picked by hand. | Peter, 2026-11-14 |

---

## 4. The ownership balance

Per material *m* (a product whose category is marked as material, §8.1):

```
balance(m) = Σ counted bill lines of m        (in: D11, below)
           − Σ materials used by batched orders  (out: frozen need per unit × effective quantity, §5.4)
```

### 4.1 Which bill lines count (D11)

A posted vendor bill line of a material counts when:

1. **Its bill carries a correct e-invoice:** an `l10n_vn.einvoice` of direction *received* is attached to
   it, it has not been replaced (`correction_state` is not *replaced*), and its untaxed amount, VAT and
   total equal the bill's: the e-invoice module's own comparison (`amounts_differ`) is false.
2. **The goods were received:**
   - a line from a purchase order counts up to the quantity received: per PO line, the lesser of the
     quantity on counted bills and `qty_received`;
   - a line of a **batch bill** counts in full: those goods are already in our warehouse, which is the
     point of the batch;
   - any other line (a direct bill outside a batch) does not count and is shown as *not linked to a
     receipt*. There is none today.

**Refunds count at once, without waiting for an e-invoice.** A vendor refund lowers what we own, so it is
taken into account as soon as it is posted (negative), and a return to a vendor lowers `qty_received`
anyway. Increases need proof; decreases do not.

Bills of any vendor count, not only the trading company's. A subcontractor's bill for a finished good
(the hammock) does not: its product is not a material, and the materials inside were ours to supply.

### 4.2 What does not move the balance

Drafts, bills without a correct e-invoice, manufacturing, scrap and inventory adjustments. The balance
measures legal ownership by norms, not the physical stock.

### 4.3 How it is computed

**P1 — computed from its sources, never stored.** One Python method reads the material bill lines and the
batches' need lines and returns the quantities per material. *Request* nets with it, and the balance
report (§7.2) is a transient model filled from it each time it is opened. Nothing is written when a bill
is posted or an e-invoice attached, so the module overrides nothing on `account.move` and the balance
cannot drift from its sources.

A SQL view was the first idea and was dropped: the e-invoice check (`amounts_differ`) is computed in
Python and not stored, and the effective quantity (§5.4) and the UoM conversions would have been written
twice. The volumes are small (about 1,100 material bill lines, a few hundred order lines).

Beside the balance, the method gives two quantities that do not count yet:

- **awaiting e-invoice:** posted material bill lines without a correct e-invoice;
- **billed, not received:** quantities on bills beyond `qty_received`.

### 4.4 Before go-live

As of 12 Nov no bill carries an e-invoice (§2.1), so the counted balance would start at zero and the
first batch would ask the trading company to invoice everything again. **The XMLs of the five material
bills are attached first**, PRP/2026/10/0001 above all, with *Attach e-invoice*.

---

## 5. Transfer batches

### 5.1 Life cycle

| State | Meaning | What can change |
|---|---|---|
| **Draft** | Orders are being collected. The figures are a preview. | Orders added or removed; *Add uncovered orders*; *Refresh* |
| **Requested** | The explosion, the netting and the prices are fixed; the document is printed for the trading company; a draft bill exists | The bill (quantities to match the e-invoice); *Cancel* while the bill does not count |
| **Covered** | The batch's bill counts (D11), or nothing needed to be requested | Nothing |
| **Cancelled** | The orders are free again | Nothing |

- An order can join a batch when it is confirmed (`state = 'sale'`) on or after the company's
  *Ownership Start* (D9), belongs to company 1, is not in another batch (cancelled batches excepted) and
  has something to explode. Without a start date no order can join. An order of services only
  needs no batch and shows *not needed*.
- *Add uncovered orders* adds every such order, oldest first. At go-live this includes the orders since
  24 Oct (D9).
- A batch whose request is zero for every material (all owned) goes from *requested* straight to
  *covered*, without a bill.
- Requests are made one at a time per company (the netting reads the balance; two batches requested at
  once must not both claim the same quantity).
- The batch **warns** before *Request*, without refusing it, when its materials have bills awaiting their
  e-invoice or billed beyond receipt (the request would then be too large), or when a product could not
  be exploded (§5.2).

### 5.2 Explosion

For each product line of each order, in the product's UoM:

1. If the product is a material, it counts itself.
2. Otherwise `_bom_find` gives its first BoM for company 1, any type; `explode` gives the BoM's leaf
   lines, and each component that is not a material and has a BoM of its own (a cut panel) is exploded
   again, to a depth limit. This is the recursion of `ownership_balance.py`.
3. A non-material product without a BoM is not exploded. It gets a need line marked **not exploded**,
   which counts for nothing and is listed in the batch's warning until it is fixed (a BoM added and the
   batch refreshed, or the category marked as material for goods bought for resale).

The result is stored per order line and material (`need` lines) when the order **joins** the batch (D4).
A BoM changed afterwards does not change the batch. *Refresh* re-explodes the orders of a draft batch.

Notes:

- `explode` rounds each leaf up to 0.01 of its UoM (§2.2). Over a batch this adds at most 0.01 per
  material per order line.
- A product with both a `normal` and a `subcontract` BoM is exploded through the first by sequence.
  The norms should agree; the BoM used is shown on the need line.

### 5.3 Netting

At *Request*, for each material *m* of the batch:

```
need(m)      = Σ frozen explosion of the batch's need lines
available(m) = balance(m) before this batch + pending(m)
               pending(m) = quantities requested by earlier batches whose bill does not count yet
request(m)   = max(0, need(m) − available(m))
unit cost    = company 1's standard_price of m at that moment (AVCO)
```

- **Pending** requests count as incoming, so a second batch does not ask again for what the first one
  already asked for.
- When `available(m)` is negative — the trading company invoiced less than asked, or an order grew after
  its batch (O1) — the next batch requests the gap too. The document shows it on its own line, *earlier
  shortfall*, so the per-order lines still add up.
- The request lines keep `need`, `available`, `request`, unit cost and amount as they were at *Request*.

### 5.4 Effective quantity

A need line counts its frozen materials **per unit** of the order line, times an effective quantity:

| Order line | Effective quantity |
|---|---|
| Order cancelled | 0 |
| Closed: delivered ≥ ordered (`qty_delivered ≥ product_uom_qty`) | `qty_delivered` (returns *to refund* already deducted) |
| Open | the larger of the frozen quantity and `qty_delivered` |

So materials of goods never delivered, or returned, come back into the balance once the line is closed,
and goods delivered beyond the frozen quantity become a shortfall that the next batch requests. This one
rule handles O1–O3.

A line closes by its quantities, never by the order's *locked* flag: with *Lock Confirmed Sales* on,
Odoo locks every order at confirmation (§2.2), and every line would then count only what was delivered,
nothing before delivery. When the rest of a line will not ship, or goods came back, the user lowers the
line's ordered quantity to what was delivered.

### 5.5 The document for the trading company

A QWeb report on the batch, A4, Vietnamese labels (working title *Bảng kê nguyên phụ liệu đề nghị xuất
hóa đơn*):

1. Header: batch number and date, both companies with tax codes, the orders covered.
2. **Per sales order**: order number, customer, finished goods and quantities, and the materials
   requested for that order. The owned part is allocated to orders in batch order (oldest first) and
   only the requested remainder is printed per order.
3. **Total per material**: code, name, UoM, quantity, unit cost, amount; the *earlier shortfall* line if
   any; total before VAT.

The trading company issues its e-invoice from the total table.

---

## 6. The trading company's bill

### 6.1 How it is made

*Request* is for accounting users (*Accounting / Invoicing*), since it creates a vendor bill. It creates a
**draft vendor bill** linked to the batch: partner = the trading company (company
setting), fiscal position = the ownership fiscal position (company setting), one line per requested
material, quantity = `request(m)`, unit price = the frozen unit cost, the product's vendor taxes. The
module never posts it.

The bill is made directly, **not from a purchase order**: a confirmed purchase order creates a receipt
(§2.2), which would receive goods already on our shelves. This replaces the earlier idea of a draft
purchase order.

When the e-invoice arrives, the accountant attaches its XML to the bill with *Attach e-invoice* (E3 of
`l10n_vn_einvoice`), corrects the bill's quantities to the e-invoice if they differ, and posts it. The
bill then counts (D11).

### 6.2 What it posts

| Line | Account | Why |
|---|---|---|
| Each material | **33889** (stock input 3399 mapped by the fiscal position) | Debits the clearing account the stock was booked against. Nothing posts to stock, no valuation layer is created (§2.2) |
| VAT | 1331 | From the product's vendor tax, as on PRP/0001 |
| Payable | 3311 | The trading company's partner |

The fiscal position maps the stock input account of the material categories (3399) to 33889. It must not
be set to apply automatically, so ordinary bills from the trading company, which go through purchase
orders and receipts, are not affected.

At current unit cost, each bill relieves 33889 by exactly the value the stock already carries for that
quantity, so the transfer itself makes no gain or loss. 33889 as a whole does not reach zero through
batches alone (O6).

### 6.3 Coverage

- The batch is **covered** when its bill counts: posted, with a correct e-invoice. Its orders show
  *covered*, with the batch and bill.
- The batch shows, per material, requested and billed quantities and the difference. A shortfall stays
  in the balance and is requested by the next batch (§5.3); an excess stays as owned balance.
- When the bill stops counting (reset to draft, e-invoice replaced), the batch goes back to *requested*.

### 6.4 Payment and offset

The bills are ordinary payables to the trading company. The garment company also sells to it (S00263,
S00265, S00268, S00270, S00272). Offsetting the two needs a **written offset agreement** (*biên bản bù trừ
công nợ*) between the companies; the offset entry is an ordinary journal entry. Not in this module.

---

## 7. Coverage shown, and reports

### 7.1 Coverage where people work

No check, wizard or block (D10). Coverage is shown:

- on the sales order form and list: batch, batch state, bill, *covered / requested / not batched /
  not needed*;
- on the delivery transfer, through its sales order (`sale_id`): a banner when the order is not covered.

### 7.2 Reports

| Report | Shows |
|---|---|
| **Orders not in a batch** | Confirmed orders of company 1 that need a batch and have none, and batched orders with lines added after their batch (sales order list, filters) |
| **Open batches** | Batches in *draft* or *requested*, with the bill, its state and its e-invoice |
| **Balance per material** | List and pivot of the quantities (§4.3): counted bills, used by batches, pending requests, balance, awaiting e-invoice, billed not received, on hand, value at current cost; and, as in `ownership_balance.py`, the on-hand quantity not covered by the balance (the trading company's raw stock) |

The last column counts raw stock only. Materials inside finished goods and cut panels on hand are not
split out; the balance covers them as the goods are sold (D2).

---

## 8. Data model (working names)

### 8.1 Configuration

| Model | Field | Meaning |
|---|---|---|
| `product.category` | `material_ownership` (Boolean) | Products of this category count as materials. Set per category, not inherited. On this instance: Raw Materials, Raw Materials / Fabric, Consumables / Packaging (Peter sets it; not seeded) |
| `res.company` | `material_ownership_start` | Orders confirmed from this date on are in scope (24 Oct 2026; set by hand) |
| | `material_owner_partner_id` | The trading company's partner (partner 7) |
| | `material_fiscal_position_id` | The fiscal position of §6.2 |

### 8.2 Records

| Model | Fields |
|---|---|
| `sale.material.batch` | `name` (sequence), `company_id`, `state`, `order_ids`, `date_request`, `need_line_ids`, `request_line_ids`, `bill_ids`, `warning`, `note` |
| `sale.material.batch.need` | `batch_id`, `order_id`, `order_line_id`, `bom_id`, `line_qty` (order line quantity in the product's UoM, frozen), `product_id` (material, or the product not exploded), `material_qty` (frozen), `exploded` |
| `sale.material.batch.request` | `batch_id`, `product_id`, `need_qty`, `available_qty`, `shortfall_qty` (earlier shortfall included), `request_qty`, `unit_cost`, `amount`, `billed_qty` (computed from the counted bills), `difference_qty` |
| `sale.order` | `material_batch_id` (`copy=False`), `material_coverage` (computed) |
| `account.move` | `material_batch_id` (`copy=False`) |
| `sale.material.ownership.balance` | Transient rows of the balance report (§4.3): per material, owned by bills, used, balance, pending, awaiting e-invoice, billed not received, not linked to a receipt, on hand, not owned on hand, values |

Depends on `sale_stock`, `mrp`, `purchase_stock`, `l10n_vn_einvoice`, all installed.

---

## 9. Opening figures

From `revaluation-conversion/ownership_balance.py` on `prod_copy` (production 12 Nov 2026 20:48;
`ownership_prodcopy.txt`, `ownership_balance_prodcopy.csv`). The script nets the 12 sales invoiced since
24 Oct against **all posted** material bills (the rule before D11), then compares the balance with raw
stock on hand. Once the five bills carry their e-invoices (§4.4), D11 gives the same result, since every
line was received.

| Category | Items | Raw stock value | Owned | Still the trading company's | Already short |
|---|---:|---:|---:|---:|---:|
| Consumables / Packaging | 46 | 58,141,641 | 50,168,266 | 7,973,375 | 509,025 |
| Raw Materials | 429 | 1,879,812,203 | 1,618,438,914 | 261,374,425 | 8,430,311 |
| Raw Materials / Fabric | 126 | 1,616,092,225 | 1,112,339,252 | 503,752,993 | 6,121,195 |
| **Total** | **601** | **3,554,046,069** | **2,780,946,432** | **773,100,793** | **15,060,531** |

Largest shortfalls: FAB00594 (3.52 M), FAB00658 (2.60 M), elastic MAT01699 / MAT01702 / MAT01700.

These figures leave out S00275, S00276 and every order since. Before go-live the script is re-run on a
fresh production backup (download from R2, restore into `prod_copy`, strip the backdoor), with D11's
rule, to check the first batch's request.

---

## 10. End of use

The module is stopped once the trading company's remaining materials are settled — by batches, or by the
final settlement of O6 — and the last batch is covered. It is then uninstalled. Its batches, need and
request lines and the `material_batch_id` links go with it. The bills, their e-invoices, the fiscal
position and every journal entry stay. Nothing needs undoing.

---

## 11. Open points for Peter

### O1 — Orders changed after batching

The explosion is frozen when the order joins (D4). Nothing is refused (D10):

- **Cancelled order, smaller quantity, removed line, larger quantity:** the effective quantity (§5.4)
  handles them. A larger quantity becomes a shortfall once delivered, which the next batch requests as
  *earlier shortfall*.
- **New line on a batched order:** it has no need line. The next batch explodes it and lists it under its
  order, marked *added after batch X*. The order shows *partly covered* until then.

Recommendation: as above. The order then appears on two documents, which is the honest record.

### O2 — Partial deliveries

A partial delivery needs nothing while the rest will still ship. A remainder that will never ship is
released when the line's ordered quantity is lowered to what was delivered, through the effective
quantity (§5.4). Recommendation: lower the quantity whenever a remainder is dropped (cancelling the
backorder alone releases nothing).

### O3 — Credit notes and returns

- A credit note for price only (discount, claim) moves no goods: nothing changes.
- A return marked *to refund* lowers `qty_delivered` (§2.2). The line is then open again (delivered <
  ordered), so its materials come back into the balance once its ordered quantity is lowered to what was
  delivered (§5.4), unless replacement goods will ship.
- A credit note without a return (goods kept or destroyed by the customer) changes nothing.

Recommendation: no mechanism beyond §5.4.

### O4 — The trading company's records in company 2

Company 2 keeps no records in Odoo (§2.1). Options:

- **(a) Nothing in company 2.** The batch document is the hand-off; the trading company invoices from its
  own system.
- **(b) Its customer invoice in company 2,** generated from our bill by OCA `account_invoice_inter_company`
  (installed, switched off). It would need company 2's chart, journals and taxes in use, and its stock
  is not in company 2 either (the goods sit in WH Chi Lăng).

Recommendation: **(a)**, which D10 also favours. Inter-company invoicing stays off: switched on, it would
also create counterpart invoices for every ordinary sale to the trading company.

### O5 — Is the portal list part of "correct"?

D11 requires an attached, unreplaced e-invoice whose amounts match the bill. `l10n_vn_einvoice_reconcile`
can also match it against the tax portal's list. Recommendation: show the portal match on the batch and
the balance as information, not as a condition, so a batch never waits on a portal list being imported.

### O6 — What batches do not transfer

Finished goods (6.55 bn) and cut panels (1.07 bn) on hand on 12 Nov hold the trading company's materials
and the conversion done before 24 Oct. The batches transfer the materials as the goods are sold; the
conversion part, and any difference between norms and actual use, stay in 33889. Open: whether a final
settlement (a closing invoice for what remains, at a date to choose) or another entry closes 33889, and
when. That date is also when the module ends (§10).

### O7 — Naming

`sale_material_ownership` is a working name, and so are the model and field names. The module is
temporary and not meant for OCA. Peter decides the final name.

---

## 12. Next

1. Peter reviews O1–O7.
2. Module spec `docs/modules/sale_material_ownership.md`, in three steps: (1) configuration, explosion,
   draft batches, the quantities and the balance report; (2) *Request*, netting, the bill and coverage;
   (3) the document.
3. Before go-live: attach the five bills' XMLs (§4.4); re-run `ownership_balance.py` on a fresh
   production backup with D11's rule (§9).
