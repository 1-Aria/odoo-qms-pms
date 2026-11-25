# Defective Goods and Seconds — Design

Nov 18, 2026 · @Peter · Revised Nov 24, 2026 · Status: live on production since 2026-11-24 (module
`stock_scrap_downgrade` 18.0.1.1.0 and the setup); seconds sales halted until ownership v2 is live

How the garment company (company 1) treats pieces that are not first quality: the policy, the daily
practice, and how both run in Odoo. Seconds are sold only to staff, in small quantities. Some seconds belong to the
garment company and some to the trading company, and each company sells its own (§3.4).

The design stays on core Odoo. Scrap, sales orders, deliveries, invoices, variants, owners on stock and saved filters
do the work. One very small module, `stock_scrap_downgrade`, adds what core cannot do: receive the seconds product, at
the piece's cost and with its owner, in the same step that scraps the piece (§6).

## 1. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| S1 | **Every defective piece is accounted for** | Each piece leaves finished goods through a recorded downgrade or scrap, tied to its manufacturing order where it has one |
| S2 | **Seconds are sold through the system** | Each sale of the garment company's seconds is a sales order, a delivery and an e-invoice; each sale of the trading company's seconds is a delivery that company invoices |
| S3 | **Seconds stock means something** | Management can see the quantity, owner, cost and expected price of each type and price band |
| S4 | **The downgrade is one step** | One confirmation removes the piece and receives the second; neither half can happen alone |
| S5 | **Seconds sales stay apart** | One click in the normal sales views and reports shows or hides them, and they have their own revenue account |
| S6 | **Books follow the goods** | A sellable piece keeps its cost until sold, at a seconds price set above cost; an unsellable piece is expensed when scrapped |
| S7 | **Each owner sells its own** | A delivery takes only the stock of the company that invoices it |
| S8 | **Small footprint** | No new model, menu or security group |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| Downgrade of finished pieces to seconds | In | S1, S4 |
| Scrap of unsellable pieces, panels and fabric | In, core | S1, S6 |
| Seconds by type and price band | In, core variants | S3 |
| Opening stock of seconds held outside Odoo | In, core inventory adjustment with an owner | S1, S3 |
| Staff sale days | In, core sales flow and deliveries | S2 |
| Reservation by owner | In, OCA `stock_owner_restriction`, installed by ownership v2 | S7 |
| Separate views and reports | In, saved filters | S5 |
| Sale of seconds to outside buyers | Core sales flow | Same products and accounts |
| Sale of cutting waste by the kg | Optional | Only if the company decides to sell it (§4.6) |
| Defect codes, causes and rates | Out | QMS and `ie_quality` own them |
| Repair | Out | Repaired pieces never leave first quality; `ie_quality` records the work |

## 2. Facts that shape the design

Checked on 2026-11-18 and 2026-11-23 against the running code, the test database and `prod_copy`.

| Fact | Evidence | Consequence |
|---|---|---|
| Seconds have been kept outside Odoo | Peter, 2026-11-23: they were scrapped or set aside and managed off the system. Test database: 2 scraps ever, 1 cut panel and 10 of fabric | The opening stock enters by inventory adjustment (§4.7) |
| The opening stock is known | Peter's list, `Odoo-Build/defective-handling/defective-count.xlsx`: 24 rows by style and fabric, 2,910 pieces, 1,969 of them 505G. Its prices are the normal prices; Odoo agrees in most rows | Types and bands follow from it (§5) |
| Half the normal price is below cost for most polos and all trousers | Peter's staff priced seconds at half the normal price. At that price 14 of the 24 rows sell below cost (e.g. 077: cost 106,811, half price 67,500) | Seconds prices are set at least 10% above cost (D14) |
| The opening stock belongs to the trading company | Ownership v2: stock from before the separation belongs to the trading company (`Material Ownership v2 — Processing Model.md` §5.3). The trading company will not sell it to the garment company (Peter, 2026-11-23) | It enters with the trading company as owner and is sold by that company (§3.4) |
| Owned stock is left out of valuation | A move line whose owner is not the company's partner creates no valuation layer (`stock_account/models/stock_move_line.py:121-130`). An inventory adjustment passes the quant's owner to its move (`stock/models/stock_quant.py:1286`) | Stock owned by the trading company costs nothing in the garment company's books, with no choice to make |
| Core reserves any owner's stock | A move reserves without an owner filter (`stock/models/stock_move.py:1957`). A transfer's *Owner* shows only on receipts and is applied only at validation (`stock/views/stock_picking_views.xml:243-245`, `stock/models/stock_picking.py:1257-1260`) | Core cannot keep a delivery to one owner's stock |
| OCA restricts reservation per operation type | `stock_owner_restriction`: *Unassigned owner* reserves company stock only; *Picking partner* reserves the transfer's owner's stock and shows *Owner* on the delivery (`oca/stock-logistics-workflow/stock_owner_restriction/models/stock_move.py:38-79`, `views/stock_picking_views.xml`). Ownership v2's owner module depends on it | Seconds sales wait for v2 (D16) |
| Mirroring variants is not practical | Test database: 63 garment templates with a BoM hold 2,166 variants | Seconds are organised by type and band (§5) |
| **Scrap never reaches an expense account today** | Neither scrap location has a valuation account on `prod_copy`, so the debit goes to the category's stock output account (`stock_account/models/stock_move.py:539-543`): SP/00001 Dr 1550 / Cr 1541, SP/00002 Dr 1541 / Cr 1520. A finished good would debit 1599 | Scrap locations need an expense account (D5) |
| An MO scales material to the good quantity | `_set_qty_producing` sets each component to producing quantity × unit factor (`mrp/models/mrp_production.py:1349`) | Recording only good pieces leaves the defective pieces' material unconsumed (§9) |
| A scrap can be raised from a finished MO | The MO's *Scrap* action offers its finished product, starts from the MO's destination and counts on the MO's *Scraps* button (`mrp/models/stock_scrap.py:24-32`, `mrp_production.py:2301-2314`). The scrap's move stays out of the produced quantity (`mrp_production.py:180-183`) | The downgrade starts from core's Scrap form |
| Core offers several scrap locations | `scrap_location_id` is a choice among locations marked as scrap (`stock/models/stock_scrap.py:43-46`), and it defaults to the lowest id | *Hạ loại 2* is a second choice on the same form |
| A location can carry its own accounts | `stock_account/models/stock_move.py:536-543` | With both accounts on 1550, the downgrade's two entries net to zero |
| A move can be priced and linked | An incoming move uses its `price_unit` (`stock_account/models/stock_move.py:69-74`). `stock.scrap.move_ids` shows every move carrying `scrap_id` (`stock_scrap.py:37, 181-184`) | The receipt carries the value and appears on the scrap with no new field |
| A scrap carries an owner | `stock.scrap.owner_id`, shown to *Consignment* users, is set on the scrap's move line (`stock/models/stock_scrap.py:36, 120-145`) | The seconds can keep the owner of the pieces (D17) |
| A variant can hold its own price | OCA `product_variant_sale_price` is installed; 1,336 of 1,603 finished-goods variants on the test database use it | The band's expected price sits on the variant |
| A sales receipt cannot become an e-invoice | Only customer invoices are marked ready to send (`l10n_vn_edi_viettel/models/account_move.py:449-453`). A receipt also moves no stock and records no payment | Sales receipts are not used (§9) |
| Staff can be invoiced as they are | All 433 active employees on `prod_copy` have a contact. Core's check needs no buyer address or tax code, and the company default invoice symbol applies | Viettel's acceptance remains to be confirmed (O5) |
| Staff sales could outnumber normal sales | `prod_copy`: 274 confirmed sales orders and 77 posted customer invoices | Separate views are needed (S5) |
| A saved filter can be shared | A favorite without a user is offered to every user of its action (`base/models/ir_filters.py:72-92`) | Separation needs no code (§7) |

## 3. Policy

### 3.1 Grades

| Grade | What it is | What happens |
|---|---|---|
| **A** | First quality | Normal sale |
| **Repair** | Fixable on the line | Repaired, re-inspected, stays A |
| **B, seconds** (*hàng loại 2*) | Sellable, with an aesthetic defect: shade, small stain, slub, cosmetic stitching | Downgraded at cost, kept in a separate locked area, sold on staff sale days |
| **C, reject** | Not sellable, wherever it is found | Scrapped and destroyed with a *biên bản hủy* |
| **Cutting waste** | Offcuts, end of rolls, thread | Discarded, or sold by the kg if the company chooses |

### 3.2 Handling rules

1. **The people handling MOs downgrade pieces.** The count is signed when the pieces are separated.
2. **Repair comes first.** A piece is downgraded only when repair is impossible or not worthwhile.
3. **Seconds are priced above cost** (Peter, 2026-11-23): half the normal price, or the style's average cost plus
   10% when that is higher, rounded up to 5,000 (D14).
4. **Buyer brands are not sold as seconds** without the buyer's agreement. Labels come off, or the goods are
   destroyed, as the contract requires.
5. **The seconds area is counted monthly** against Odoo, by owner.

### 3.3 Staff sale days

1. **One sale day a month,** a few days after payday on the 10th; every two months if few people buy.
2. **The list is posted beforehand:** type, band and price.
3. **Each person has a quantity limit** per sale day.
4. **Payment is taken on the spot,** by cash or transfer, with no salary deduction.
5. **Goods are checked at the gate** against the delivery note or invoice.
6. **Staff pay the same price as outside buyers.**
7. **Old stock is cleared.** What stays unsold for about three months goes in a bulk sale or is repriced by decision.

### 3.4 Ownership

| Seconds | Owner | Sold and invoiced by |
|---|---|---|
| The opening stock (§4.7) | Trading company | The trading company, with its own e-invoice to each buyer |
| Downgraded from the trading company's goods | Trading company | The same |
| Downgraded from the garment company's goods | Garment company | The garment company: sales order, delivery and SInvoice |

A buyer who takes seconds of both owners gets an invoice from each. **Seconds sales are halted until ownership v2 is
live** (Peter, 2026-11-23), because only its owner restriction keeps each delivery to one owner's stock.

## 4. Process in Odoo

### 4.1 The flow

```
Sewing line ─► MO closed for ALL pieces made ─► Post-Production
                                                   │
                                     QC sorts      ├─ A ─► Store Finished Product ─► WH/Stock
                                                   ├─ B ─► Scrap form, location "Hạ loại 2" ─► seconds variant in WH/Stock, same owner ─► Staff sale day
                                                   └─ C ─► Scrap form, location "Scrap" ─► destroyed
```

### 4.2 Manufacturing order

Nothing changes. The MO records every piece sewn, good or defective, so material and conversion cost are
complete.

### 4.3 Downgrade (B)

From the MO's *Scrap* action, or Inventory → Operations → Scrap for goods found later or returned by customers:

1. Enter the product and quantity, as for any scrap. For the trading company's goods, set *Owner* to it.
2. Choose Scrap Location **Hạ loại 2**. The seconds product appears, proposed from the last downgrade of that
   product.
3. Confirm. The piece leaves and the seconds variant arrives in the warehouse's stock location, with the same owner,
   at the piece's cost.

### 4.4 Scrap (C)

The same form with the standard **Scrap** location. A *biên bản hủy* supports the entry.

### 4.5 Staff sale day

1. Before the day, sales posts the list from Product Variants, filtered to the Seconds category, and the stock
   report grouped by *Owner*.
2. On the day, sales are written on a signed sheet: buyer, item, owner, quantity, price, paid.
3. The same day, for the **garment company's** pieces: one sales order per buyer, with the employee's contact as
   customer; deliveries validated, and invoices created, confirmed and sent, in batches from their lists. The
   *Delivery Orders* type reserves only the garment company's stock.
4. For the **trading company's** pieces: one transfer per buyer of the type **Xuất hộ Công ty TM**, partner the
   employee, *Owner* the trading company. It reserves only that company's stock and creates no entry. The
   trading company invoices each buyer from its own system, using the delivery notes.
5. Cash is recorded as each company records its own.

A buyer has one invoice per seller per sale day. The law requires an e-invoice per buyer (D12).

### 4.6 Cutting waste

If sold: one product without inventory tracking, in kg, weighed at sale and never held in stock.

### 4.7 Opening stock

The seconds counted on Peter's list enter by **inventory adjustment of the seconds variants with *Owner* = the
trading company**, before any downgrade into them. Odoo leaves them out of valuation: no entry, now or at the
ownership conversion.

## 5. Seconds products: type × price band

| Dimension | Odoo | Example |
|---|---|---|
| **Type** | One product per garment type | *Hàng loại 2 – Quần tây* |
| **Price band** | Attribute `Khung giá`, one value per seconds price, named by that price | *Hàng loại 2 – Quần tây (105.000)* |
| **Expected price** | The variant's sales price, by the rule of §3.2 | 105,000 |
| **Cost** | The variant's average cost, built from the garment company's pieces downgraded into it | |
| **Actual price** | The sales order line, or the trading company's invoice | |

Prices by the rule of §3.2, from `prod_copy`'s average cost of each style's stock on hand on 17 November; a style
without cost in Odoo takes half its normal price. Neighbouring prices are merged upwards, which keeps every price
above its floor. 6 types, 12 variants (Claude, at Peter's request, 2026-11-23). The normal prices are the list's;
where Odoo disagrees (043, T01, Thun polo 3906), the list wins.

| Type | Seconds price → styles (normal price; average cost) |
|---|---|
| Áo polo | **55.000**: 509P (90,000; none), 511P (90,000; 48,645), 512P (90,000; 47,842), Thun polo 3906 (80,000; 45,629) · **60.000**: 516T (70,000; 50,435), A015/A017 in A015 fabrics (80,000; 52,273), 515T in A015 fabrics (80,000; 53,847) · **70.000**: 514T (80,000; 60,801), 514V (80,000; 56,336) · **80.000**: 515T in THUNCASAU-US (160,000; 43,640), A017 in A017 (160,000; 57,943) |
| Áo thun | **30.000**: A10 (60,000; none) · **55.000**: 505, 505G (100,000; 46,357) |
| Áo sơ mi | **85.000**: 011D (170,000; 67,732), 012N (160,000; 60,569) |
| Quần tây | **75.000**: 007 (95,000; 67,500) · **105.000**: 076 (130,000; 88,677), 043 (200,000; none), 066 (205,000; none) · **120.000**: 077 in 007 fabrics (135,000; 106,811) · **140.000**: 024 (205,000; 125,083), Kaki K09 (245,000; added 2026-11-25) |
| Quần sọt | **75.000**: 006A (90,000; 64,362) |
| Quần thể dục | **50.000**: T01 (65,000; 44,530) |
| Võng | **30.000**: Võng Vải Rêu · **100.000**: Võng Mùng (seconds prices from Peter's count of 2026-11-25; added then, SCND00014 and SCND00015) |

The setup script recomputes the rule from the costs on the day it runs and lists any price that falls short.

- A type with a single price has no band: Áo sơ mi, Quần sọt and Quần thể dục are one product each.
- A new style takes the band at or above its price by the rule; a new price adds a value.
- Size, colour and style are not tracked in seconds. The scrap keeps the original variant and MO.
- Product Variants, filtered to the Seconds category, shows type, band, cost, expected price and quantity on hand;
  the stock report adds the owner.

## 6. Module `stock_scrap_downgrade`

Depends on `stock_account` only. It adds no model, menu, group or access rule. Spec:
`docs/modules/stock_scrap_downgrade.md`.

| Element | Design |
|---|---|
| `stock.location.downgrade_categ_id` | Many2one to `product.category`, shown on scrap locations. When set, scrapping into this location is a downgrade, and the seconds product must belong to this category |
| `stock.scrap.downgrade_product_id` | Many2one to `product.product`. Shown only for a downgrade location. Filtered to the location's category and the scrapped product's unit-of-measure category, untracked products only. An editable stored compute proposes the seconds product of the last downgrade of the same variant, then of the same style. Cleared for any other location |
| `stock.scrap.do_scrap` | Extended. A downgrade without a seconds product is refused. After core's scrap, it creates and validates a move of the seconds product, same quantity, from the downgrade location to the source warehouse's stock location, with `scrap_id` set, at the scrap's value per unit. Its owner is the scrap's owner (step 1.1) |
| `stock.move._should_force_price_unit` | Extended for that receipt, so a value of zero stays zero, not the seconds product's average |
| Views | The field on the two scrap forms and the scrap list; the category on the location form |

Everything else is core: the Scrap form and its MO action, its *Owner* field, the *Scraps* count on the MO, the
scrap's *Product Moves*, the insufficient-quantity warning, the valuation entries and the moving average.

Both moves run in one transaction. If either fails, neither happens.

Corrections are done by hand with transfers back through *Hạ loại 2*. There is no automatic undo.

## 7. Master data, operation types and saved filters

| Record | Values |
|---|---|
| Account **6328** *Giá vốn - hàng hủy* | Type *Cost of Revenue* |
| Account **51102** *Doanh thu hàng loại 2* | Type *Income* |
| Location **Virtual Locations/Hạ loại 2** | *Inventory Loss*, company 1, *Is a Scrap Location*, Seconds category; Incoming and Outgoing valuation accounts **1550** |
| Location **Virtual Locations/Scrap** (company 1) | Incoming valuation account 6328 |
| Category **Finished Goods / Seconds** | Internal reference prefix `SCND` (OCA `product_sequence`, like `TSRT`, `PANT`); AVCO, automated valuation; valuation 1550, input 1541, output 1599, income 51102, expense 6320, stock journal as the other finished goods |
| Attribute **Khung giá** | One value per seconds price (§5); variants created instantly |
| Products **Hàng loại 2 – <type>** | Goods, tracked by quantity, Units, invoiced on delivered quantity, default variant management; a sales price per variant |
| Opening stock | Inventory adjustment per seconds variant, *Owner* the trading company (§4.7) |
| Operation type **Delivery Orders** | Owner restriction *Unassigned owner* (ownership v2) |
| Operation type **Xuất hộ Công ty TM** | Outgoing, WH/Stock to Customers, owner restriction *Picking partner* (ownership v2); *Phiếu xuất kho* configured on it |

The product category is the key that separates seconds. It is automatic, so nobody has to remember a team or a
tag.

| List or report | Shared favorite *Ẩn hàng loại 2*: hides seconds | Shared favorite *Hàng loại 2*: shows only seconds |
|---|---|---|
| Sales → Orders | Orders with no line in the category | Orders with a line in it |
| Sales → Quotations | The same | The same |
| Sales → Sales Analysis | Category is not Seconds | Category is Seconds |
| Accounting → Invoice Analysis | Category is not Seconds | Category is Seconds |
| Accounting → Customer Invoices | None | Invoices with a line in the category |

Nothing is filtered by default (Peter, 2026-11-24): staff pick a favorite from the search bar when they need it.

## 8. Accounting

The garment company's seconds:

| Event | Stock | Entry |
|---|---|---|
| MO closed | A variant + all pieces | As today |
| Downgrade | A variant − n; seconds + n, at the same value | Dr 1550 / Cr 1550 twice, net zero, with the product on each line |
| Delivery of seconds | Seconds − n | Dr 1599 / Cr 1550 at average cost |
| Invoice | | Dr 1311 / Cr 51102, Cr 33311; Dr 6320 / Cr 1599 at average cost |
| Scrap of a garment, anywhere | A variant − n | Dr 6328 / Cr 1550 |
| Scrap of panels or fabric | − n | Dr 6328 / Cr 1541 or 1520 |

The trading company's seconds create no entry in the garment company's books: not the opening adjustment, the
downgrade or the delivery.

No norm is applied. Scrap within a normal level is expensed at once and is not spread over the good pieces, which
changes timing only. Product Variants shows each seconds variant's cost beside its price; a variant whose cost
climbs above its price is repriced or written down by hand.

## 9. Decisions

| ID | Decision | Reason |
|---|---|---|
| D1 | Grades A, repair, B, C as in §3 | Separates what is sold from what is destroyed |
| D2 | Seconds are type × price band, with the expected price on the variant (Peter, 2026-11-18). **Bands are named by their price** (Peter, 2026-11-23) | Keeps management value without tracking size, colour or style (S3). The price follows a fixed rule, so each price is its own band |
| D3 | **The MO records all pieces; defects leave afterwards. By-products are not used** | See below |
| D4 | **A downgrade keeps the piece's cost, and cost of sales is booked at sale** (Peter, 2026-11-18, confirmed 2026-11-23) | Seconds are priced above cost (D14), so there is no loss to book, and each sale shows its real margin |
| D5 | **Scrap is expensed to 6328 wherever it happens, with no norm** (Peter, 2026-11-18) | A piece is either sellable or scrapped. Simple and conservative |
| D6 | Seconds revenue posts to 51102 | Part of sales of own products, yet separate (S5) |
| D7 | No separate stock location for seconds | The products already separate them. The locked area is physical |
| D8 | The downgrade extends core's scrap, in one small module | Only code can pass the value and tie the two moves together. Everything else stays core (S8) |
| D9 | No mapping table. The last downgrade proposes the seconds product | No data to import or maintain; the first downgrade of a style is chosen by hand |
| D10 | No new access rights (Peter, 2026-11-18) | MO handlers downgrade and sales staff sell. Each scrap records its user |
| D11 | Staff buy on periodic sale days | Opens the seconds area under supervision and batches the work |
| D12 | One e-invoice per buyer (Peter, 2026-11-18) | Required by law |
| D13 | Separation by product category with shared favorites, none applied by default (Peter, 2026-11-24); no sales team, journal or menu | Needs no code, and staff choose the view they need (S5, S8) |
| D14 | **Seconds are priced above cost: half the normal price, or the style's average cost plus 10% when higher, rounded up to 5,000** (Peter, 2026-11-23; prices by Claude at his request) | Half price alone sells most polos and trousers below cost. The 10% absorbs moves in cost, so stock is never carried above what it sells for and no write-down code is needed |
| D15 | **The opening stock enters with the trading company as owner** (Peter, 2026-11-23) | It is that company's stock (ownership v2). Owned stock is unvalued, so the garment company books nothing, and the conversion needs no rule for it |
| D16 | **Each owner sells its own seconds; sales wait for ownership v2** (Peter, 2026-11-23) | The trading company will not sell its stock to the garment company. Only OCA `stock_owner_restriction`, installed with v2, keeps each delivery to one owner's stock |
| D17 | **A downgrade keeps the owner of the pieces** (step 1.1) | The trading company's defects stay the trading company's |

**Why not by-products (D3).** A by-product with cost share 0 would enter at value 0
(`mrp_account/models/stock_move.py:17-21`). It fails in practice:

- Closing the MO for 980 of 1,000 consumes material for 980 only (`mrp_production.py:1349`). Recording the real
  consumption means editing every component by hand, on BoMs averaging 9 lines and reaching 40.
- The by-product stops in Post-Production, with no onward transfer (`mrp_production.py:1221`).
- The grade must be known before the MO closes, while warehouse finds and customer returns need another method.

**Other alternatives rejected.**

| Alternative | Why not |
|---|---|
| A *Grade* attribute on garments | Multiplies every template's variants and enters sales and BoMs |
| Seconds variants mirroring the catalogue | About 2,000 more products |
| Scrap, then a manual transfer | Two steps that can drift apart, and the transfer cannot carry the piece's value |
| Inventory adjustment for each downgrade | Needs manager rights, overwrites a counted quantity, leaves no document |
| Downgrade MO | Heavy for a one-to-one change of product |
| Zero cost for seconds | Writes off value that will be recovered and overstates the margin at sale |
| Half price for every style | Below cost for 14 of the 24 styles |
| The lower of cost and seconds price in the module | Unneeded once prices are set above cost (Peter, 2026-11-23) |
| A norm with account 154 | Unneeded once seconds carry their value and scrap is simply expensed |
| The opening stock as garment stock at zero value | It is not the garment company's |
| The trading company selling the opening lot to the garment company once | It will not sell its stock (Peter, 2026-11-23), the reason ownership v2 exists |
| A staff sales team, journal and menu | Needs team membership, and a forgotten team leaks orders into normal views. The Sales Teams menu is also limited to sales managers |
| Sales receipts | No stock movement, no payment and no e-invoice (§2) |
| Point of Sale | Not installed, and too much for a monthly sale |

## 10. Open points

| ID | Point | Recommendation |
|---|---|---|
| O1 | Tax treatment of scrapped goods | Keep the *biên bản hủy* and signed counts; confirm what the accountant requires |
| O2 | Which brands belong to buyers | Sales lists them before the first sale day |
| O3 | `sale_material_ownership` warns *Not exploded (no BoM)* on a batch holding seconds (`sale_material_batch.py:150-155, 337-339`) | None: ownership v2 supersedes the module and it is uninstalled after the conversion |
| O4 | Several MOs of one variant waiting in Post-Production: a scrap reduces the reservation of the latest-scheduled transfer, which may not be that MO's (`stock/models/stock_move_line.py:803-822`) | Accept. The pieces are interchangeable and the totals stay right |
| O5 | Viettel's acceptance of a buyer with no address or tax code | Send one real invoice before the first batch |
| O6 | Scrap entries already on production's 1541 or 1550 | Check production before go-live |
| O7 | The two delivery types of §7 | Set up with ownership v2's owner module; its spec should list them |
| O8 | Normal prices in Odoo that disagree with Peter's list: Thun polo 3906 at 0, T01 at 1 VND, Quần tây 043 at 500,000 (list 200,000), Quần tây 076 as two templates with variants at 1 VND, zero-cost variants in several styles | Correct the first-quality data; it does not block seconds |

## 11. Test results

Run by Peter on the test instance, 2026-11-18, checked in the database. It used the manual method and zero-cost
seconds, so its stock flow still holds while its downgrade and cost-of-sales entries are superseded by §8.

| Step | Result |
|---|---|
| Downgrade SP/00003, 5 × UNWM00002 from WH/MO/01717 | Stock correct; Dr 6328 / Cr 1550, 501,698 |
| Scrap SP/00004, 1 piece | Dr 6328 / Cr 1550, 100,340 |
| WH/SFP/01441 | Done at 194 of 200, no backorder |
| Receipt HL200001, 5 seconds | Value 0, no entry |
| `Hạ loại 2` | +5 UNWM00002, −5 seconds |
| Sale S00326, delivery WH/OUT/00080 | 3 pieces |
| Invoice INV/2026/00050 | Dr 1311 162,000 / Cr 5110 150,000 / Cr 33311 12,000; ready to send |
| Sales receipt INV/2026/00049 | No stock movement, no e-invoice state; cancelled |

`stock_scrap_downgrade` step 1, the same day: SP/00005 and SP/00006 downgraded 3 × PANT00589 from WH/MO/00611-001 to
PR/00209. The value out equals the value in (3,218 and 1,609), every entry stays on 1550, and the location totals 0.
The receipt's unit cost comes from the rounded VND value, so the seconds cost is 1,609.00 against the piece's 1,608.87.

A sale of a costed second, S00327, 1 × PR/00209 at 100,000: delivery WH/OUT/00081 posted Dr 1599 / Cr 1550, 1,609;
invoice INV/2026/00051 posted Dr 1311 108,000 / Cr 5110 100,000 / Cr 33311 8,000 and Dr 6320 / Cr 1599, 1,609. The two 1599
lines are reconciled. Revenue went to 5110 because the test category has no 51102.

Step 1.1, 2026-11-23: an inventory adjustment of 5 × PR/00209 with the trading company as owner, the opening
pattern of §4.7, created no valuation layer or entry. SP/00007 downgraded 2 owned PANT00589: the seconds arrived
owned by the trading company, with no entry, and the garment company's PR/00209 stock and value were unchanged.

Not yet tested: the type × band products, the owner restriction,
the saved filters and SInvoice sending. The test instance has no SInvoice login.

## 12. Rollout

| # | Step | Who |
|---|---|---|
| 1 | The list of seconds held, with normal prices and quantities | Peter, done 2026-11-23 |
| 2 | Types, bands and prices from the list | Claude, 2026-11-23, at Peter's request |
| 3 | `stock_scrap_downgrade` step 1.1 (the seconds keep the owner): spec, code, test | Done 2026-11-23 |
| 4 | A setup script outside `addons/`, with check and commit modes, creating §7's accounts, locations, category, attribute, products and saved filters, and the opening adjustment with the trading company as owner | Done: `Odoo-Build/defective-handling/seconds_setup.py` |
| 5 | Rehearsal on `prod_copy`, then production | Done 2026-11-24: rehearsal on `prod_copy` committed and re-run unchanged; UI check on the test instance, including a downgrade by an MO user; production check, commit and re-run unchanged (SCND00001–SCND00013, 2,910 pieces owned by the trading company, no valuation) |
| 5a | Count of 2026-11-25 (`Odoo-Build/material-ownership/Seconds_count_25Nov.xlsx`): rows of 23 Nov unchanged; new K09 (1, band 140.000), hammock seconds 707 (100.000) and 2 (30.000), a new type *Võng*. The setup script carries the new rows; its step 7 sets each seconds product to the counted total. Since ownership v2 all finished goods belong to the trading company, so the rule's cost floor finds no garment-owned stock and falls back to half the normal price | Claude, 2026-11-25; check on `prod_copy` (copy of production after go-live): 3,620 pieces, no valuation |
| 6 | Ownership v2: its owner module brings `stock_owner_restriction`; the two delivery types of §7 are set up with it | Done 2026-11-25: the trading company's goods, the seconds included, leave with *Xuất hàng Công ty TM* |
| 7 | Brief MO handlers, the warehouse and sales on §3 and §4 | Peter |
| 8 | One real invoice to an employee, then the first sale day | Sales, accounting, the trading company |
