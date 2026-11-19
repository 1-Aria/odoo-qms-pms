# Defective Goods and Seconds — Design

Nov 18, 2026 · @Peter · Revised Nov 18, 2026 · Status: method accepted by Peter; module `stock_scrap_downgrade` step 1 done

How the garment company (company 1) treats pieces that are not first quality: the policy, the daily
practice, and how both run in Odoo. Seconds are currently sold only to staff, in small quantities.

The design stays on core Odoo. Scrap, sales orders, deliveries, invoices, variants and saved filters do the
work. One very small module, `stock_scrap_downgrade`, adds what core cannot do: receive the seconds product, at
the piece's cost, in the same step that scraps the piece (§6).

## 1. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| S1 | **Every defective piece is accounted for** | Each piece leaves finished goods through a recorded downgrade or scrap, tied to its manufacturing order where it has one |
| S2 | **Seconds are sold through the system** | Each sale is a sales order, a delivery and an e-invoice |
| S3 | **Seconds stock means something** | Management can see the quantity, cost and expected price of each type and price band |
| S4 | **The downgrade is one step** | One confirmation removes the piece and receives the second; neither half can happen alone |
| S5 | **Seconds sales stay apart** | They are out of the normal sales views and reports by default, one click away, with their own revenue account |
| S6 | **Books follow the goods** | A sellable piece keeps its cost until sold; an unsellable piece is expensed when scrapped |
| S7 | **Small footprint** | No new model, menu or security group |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| Downgrade of finished pieces to seconds | In | S1, S4 |
| Scrap of unsellable pieces, panels and fabric | In, core | S1, S6 |
| Seconds by type and price band | In, core variants | S3 |
| Staff sale days | In, core sales flow | S2 |
| Separate views and reports | In, saved filters | S5 |
| Sale of seconds to outside buyers | Core sales flow | Same products and accounts |
| Sale of cutting waste by the kg | Optional | Only if the company decides to sell it (§4.6) |
| Defect codes, causes and rates | Out | QMS and `ie_quality` own them |
| Repair | Out | Repaired pieces never leave first quality; `ie_quality` records the work |

## 2. Facts that shape the design

Checked on 2026-11-18 against the running code, the test database and `prod_copy`.

| Fact | Evidence | Consequence |
|---|---|---|
| Defective garments are not in Odoo | Test database: 1,565 finished MOs (310,600 pieces); before this test, 2 scraps ever, 1 cut panel and 10 of fabric; none on a finished product and none linked to an MO | Quantities and sales of seconds are invisible |
| They are probably still counted as finished goods | No finished-goods inventory adjustment since June. The 4,357 panels in Pre-Production are all needed by open MOs, so no unconsumed material is left over from short MOs | An inference, to be confirmed by a physical count (§12) |
| Mirroring variants is not practical | Test database: 63 garment templates with a BoM hold 2,166 variants | Seconds are organised by type and band (§5) |
| **Scrap never reaches an expense account today** | Neither scrap location has a valuation account on `prod_copy`, so the debit goes to the category's stock output account (`stock_account/models/stock_move.py:539-543`): SP/00001 Dr 1550 / Cr 1541, SP/00002 Dr 1541 / Cr 1520. A finished good would debit 1599 | The Scrap location needs an expense account (D5) |
| An MO scales material to the good quantity | `_set_qty_producing` sets each component to producing quantity × unit factor (`mrp/models/mrp_production.py:1349`) | Recording only good pieces leaves the defective pieces' material unconsumed (§9) |
| A scrap can be raised from a finished MO | The MO's *Scrap* action offers its finished product, starts from the MO's destination and counts on the MO's *Scraps* button (`mrp/models/stock_scrap.py:24-32`, `mrp_production.py:2301-2314`). The scrap's move stays out of the produced quantity (`mrp_production.py:180-183`) | The downgrade starts from core's Scrap form |
| Core offers several scrap locations | `scrap_location_id` is a choice among locations marked as scrap (`stock/models/stock_scrap.py:43-46`), and it defaults to the lowest id | *Hạ loại 2* is a second choice on the same form |
| A location can carry its own accounts | `stock_account/models/stock_move.py:536-543` | With both accounts on 1550, the downgrade needs no new accounting code |
| A move can be priced and linked | An incoming move uses its `price_unit` (`stock_account/models/stock_move.py:69-74`). `stock.scrap.move_ids` shows every move carrying `scrap_id` (`stock_scrap.py:37, 181-184`) | The receipt carries the cost and appears on the scrap with no new field |
| A variant can hold its own price | OCA `product_variant_sale_price` is installed; 1,336 of 1,603 finished-goods variants on the test database use it | The band's expected price sits on the variant |
| A sales receipt cannot become an e-invoice | Only customer invoices are marked ready to send (`l10n_vn_edi_viettel/models/account_move.py:449-453`). A receipt also moves no stock and records no payment | Sales receipts are not used (§9) |
| Staff can be invoiced as they are | All 433 active employees on `prod_copy` have a contact. Core's check needs no buyer address or tax code, and the company default invoice symbol applies | Viettel's acceptance remains to be confirmed (O5) |
| Staff sales could outnumber normal sales | `prod_copy`: 274 confirmed sales orders and 77 posted customer invoices | Separate views are needed (S5) |
| A saved filter can be every user's default | A shared default favorite applies per action (`base/models/ir_filters.py:95-152`) and replaces the action's default filters (`web/static/src/search/search_model.js:1227-1230`) | Separation needs no code (§7) |
| Room between cost and price varies | `prod_copy`, finished goods on hand, cost as % of first-quality price: Hammock 80, Shorts 78, Pants 68, Underwear Women 53, T-Shirt 49, Shirt 40, Underwear Men 34 | Seconds prices are checked against cost (§5) |

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
3. **Seconds are not sold below cost.** A piece that cannot recover its cost is not a second.
4. **Buyer brands are not sold as seconds** without the buyer's agreement. Labels come off, or the goods are
   destroyed, as the contract requires.
5. **The seconds area is counted monthly** against Odoo.

### 3.3 Staff sale days

1. **One sale day a month,** a few days after payday on the 10th; every two months if few people buy.
2. **The list is posted beforehand:** type, band and price.
3. **Each person has a quantity limit** per sale day.
4. **Payment is taken on the spot,** by cash or transfer, with no salary deduction.
5. **Goods are checked at the gate** against the delivery note or invoice.
6. **Staff pay the same price as outside buyers.**
7. **Old stock is cleared.** What stays unsold for about three months is repriced, never below cost without a
   decision, or goes in a bulk sale.

## 4. Process in Odoo

### 4.1 The flow

```
Sewing line ─► MO closed for ALL pieces made ─► Post-Production
                                                   │
                                     QC sorts      ├─ A ─► Store Finished Product ─► WH/Stock
                                                   ├─ B ─► Scrap form, location "Hạ loại 2" ─► seconds variant in WH/Stock ─► Staff sale day
                                                   └─ C ─► Scrap form, location "Scrap" ─► destroyed
```

### 4.2 Manufacturing order

Nothing changes. The MO records every piece sewn, good or defective, so material and conversion cost are
complete.

### 4.3 Downgrade (B)

From the MO's *Scrap* action, or Inventory → Operations → Scrap for goods found later or returned by customers:

1. Enter the product and quantity, as for any scrap.
2. Choose Scrap Location **Hạ loại 2**. The seconds product appears, proposed from the last downgrade of that
   product.
3. Confirm. The piece leaves and the seconds variant arrives in the warehouse's stock location, at the piece's cost.

### 4.4 Scrap (C)

The same form with the standard **Scrap** location. A *biên bản hủy* supports the entry.

### 4.5 Staff sale day

1. Before the day, sales posts the list from Product Variants, filtered to the Seconds category.
2. On the day, sales are written on a signed sheet: buyer, item, quantity, price, paid.
3. The same day, one sales order per buyer, with the employee's contact as customer.
4. Deliveries are validated, and invoices created, confirmed and sent, in batches from their lists.
5. Cash is recorded in the cash journal as usual.

A buyer has one invoice per sale day. The law requires an e-invoice per buyer (D12).

### 4.6 Cutting waste

If sold: one product without inventory tracking, in kg, weighed at sale and never held in stock.

## 5. Seconds products: type × price band

| Dimension | Odoo | Example |
|---|---|---|
| **Type** | One product per garment type | *Hàng loại 2 – Quần tây*, *Hàng loại 2 – Áo lá* |
| **Price band** | Attribute `Khung giá`: *Thấp*, *Trung*, *Cao* | *Hàng loại 2 – Áo lá (Trung)* |
| **Expected price** | The variant's sales price | 50,000 |
| **Cost** | The variant's average cost, built from the pieces downgraded into it | |
| **Actual price** | The sales order line | |

- Band names carry no amounts. A price change edits one number.
- Only the bands a type needs are created.
- Size, colour and style are not tracked in seconds. The scrap keeps the original variant and MO.
- Pieces of very different cost go in different bands, because a variant's cost is their average.
- Product Variants, filtered to the Seconds category, shows type, band, cost, expected price and quantity on hand.

Peter's list (internal reference, variant, seconds price, quantity) sets the first types, bands and prices. Each
seconds price is compared with that variant's cost before the products are created.

## 6. Module `stock_scrap_downgrade`

Depends on `stock_account` only. It adds no model, menu, group or access rule.

| Element | Design |
|---|---|
| `stock.location.downgrade_categ_id` | Many2one to `product.category`, shown on scrap locations. When set, scrapping into this location is a downgrade, and the seconds product must belong to this category |
| `stock.scrap.downgrade_product_id` | Many2one to `product.product`. Shown only for a downgrade location. Filtered to the location's category and the scrapped product's unit-of-measure category, untracked products only. An editable stored compute proposes the seconds product of the last downgrade of the same variant, then of the same style. Cleared for any other location |
| `stock.scrap.do_scrap` | Extended. A downgrade without a seconds product is refused. After core's scrap, it reads the scrap move's value and creates and validates a move of the seconds product, same quantity, from the downgrade location to the source warehouse's stock location, with `price_unit` = value ÷ quantity and `scrap_id` set |
| `stock.move._should_force_price_unit` | Extended for that receipt, so a piece of zero cost enters at zero, not at the seconds product's average |
| Views | The field on the two scrap forms and the scrap list; the category on the location form |

Everything else is core: the Scrap form and its MO action, the *Scraps* count on the MO, the scrap's *Product
Moves*, the insufficient-quantity warning, the valuation entries and the moving average.

Both moves run in one transaction. If either fails, neither happens.

Corrections are done by hand with transfers back through *Hạ loại 2*. There is no automatic undo.

## 7. Master data and saved filters

| Record | Values |
|---|---|
| Account **6328** *Giá vốn - hàng hủy* | Type *Cost of Revenue* |
| Account **51102** *Doanh thu hàng loại 2* | Type *Income* |
| Location **Virtual Locations/Hạ loại 2** | *Inventory Loss*, company 1, *Is a Scrap Location*, Seconds category; Incoming and Outgoing valuation accounts **1550** |
| Location **Virtual Locations/Scrap** (company 1) | Incoming valuation account 6328 |
| Category **Finished Goods / Seconds** | AVCO, automated valuation; valuation 1550, input 1541, output 1599, income 51102, expense 6320, stock journal as the other finished goods |
| Attribute **Khung giá** | Values *Thấp*, *Trung*, *Cao*; variants created instantly |
| Products **Hàng loại 2 – <type>** | Goods, tracked by quantity, Units, invoiced on delivered quantity, default variant management; a sales price per variant |

The product category is the key that separates seconds. It is automatic, so nobody has to remember a team or a
tag.

| List or report | Shared default filter: hides seconds | Shared favorite: shows only seconds |
|---|---|---|
| Sales → Orders | Orders with no line in the category | Orders with a line in it |
| Sales → Quotations | The same, for the user's own quotations | The same |
| Sales → Sales Analysis | Category is not Seconds | Category is Seconds |
| Accounting → Invoice Analysis | Category is not Seconds | Category is Seconds |
| Accounting → Customer Invoices | No default, because accounting must see every legal invoice | Invoices with a line in the category |

Any user can remove a default filter to see everything.

## 8. Accounting

| Event | Stock | Entry |
|---|---|---|
| MO closed | A variant + all pieces | As today |
| Downgrade | A variant − n; seconds + n, at the same value | Dr 1550 / Cr 1550 twice, net zero, with the product on each line |
| Delivery of seconds | Seconds − n | Dr 1599 / Cr 1550 at average cost |
| Invoice | | Dr 1311 / Cr 51102, Cr 33311; Dr 6320 / Cr 1599 at average cost |
| Scrap of a garment, anywhere | A variant − n | Dr 6328 / Cr 1550 |
| Scrap of panels or fabric | − n | Dr 6328 / Cr 1541 or 1520 |

No norm is applied. Scrap within a normal level is expensed at once and is not spread over the good pieces, which
changes timing only.

Stock must not be carried above what it will sell for. If a seconds variant's cost exceeds its realistic price, the
difference is written down.

## 9. Decisions

| ID | Decision | Reason |
|---|---|---|
| D1 | Grades A, repair, B, C as in §3 | Separates what is sold from what is destroyed |
| D2 | Seconds are type × price band, with the expected price on the variant (Peter, 2026-11-18) | Keeps management value without tracking size, colour or style (S3) |
| D3 | **The MO records all pieces; defects leave afterwards. By-products are not used** | See below |
| D4 | **A downgrade keeps the piece's cost, and cost of sales is booked at sale** (Peter, 2026-11-18) | Seconds are sold above cost, so there is no loss to book, and each sale shows its real margin. This replaces the earlier zero-cost design |
| D5 | **Scrap is expensed to 6328 wherever it happens, with no norm** (Peter, 2026-11-18) | A piece is either sellable or scrapped. Simple and conservative |
| D6 | Seconds revenue posts to 51102 | Part of sales of own products, yet separate (S5) |
| D7 | No separate stock location for seconds | The products already separate them. The locked area is physical |
| D8 | The downgrade extends core's scrap, in one small module | Only code can pass the cost and tie the two moves together. Everything else stays core (S7) |
| D9 | No mapping table. The last downgrade proposes the seconds product | No data to import or maintain; the first downgrade of a style is chosen by hand |
| D10 | No new access rights (Peter, 2026-11-18) | MO handlers downgrade and sales staff sell. Each scrap records its user |
| D11 | Staff buy on periodic sale days | Opens the seconds area under supervision and batches the work |
| D12 | One e-invoice per buyer (Peter, 2026-11-18) | Required by law |
| D13 | Separation by product category with saved filters; no sales team, journal or menu | Automatic, and needs no code (S5, S7) |

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
| A separate product for each price | Prices change; band and variant price do the same job |
| Scrap, then a manual transfer | Two steps that can drift apart, and the transfer cannot carry the piece's cost |
| Inventory adjustment for the receipt | Needs manager rights, overwrites a counted quantity, leaves no document |
| Downgrade MO | Heavy for a one-to-one change of product |
| Zero cost for seconds | Writes off value that will be recovered and overstates the margin at sale |
| A norm with account 154 | Unneeded once seconds carry their cost and scrap is simply expensed |
| A staff sales team, journal and menu | Needs team membership, and a forgotten team leaks orders into normal views. The Sales Teams menu is also limited to sales managers |
| Sales receipts | No stock movement, no payment and no e-invoice (§2) |
| Point of Sale | Not installed, and too much for a monthly sale |

## 10. Open points

| ID | Point | Recommendation |
|---|---|---|
| O1 | Tax treatment of scrapped goods | Keep the *biên bản hủy* and signed counts; confirm what the accountant requires |
| O2 | Which brands belong to buyers | Sales lists them before the first sale day |
| O3 | `sale_material_ownership`: seconds have no BoM, so a batch holding them warns *Not exploded (no BoM)* and requests no material for them (`sale_material_batch.py:150-155, 337-339`) | Keep staff orders out of batches. The module is temporary and the warning does not block |
| O4 | Several MOs of one variant waiting in Post-Production: a scrap reduces the reservation of the latest-scheduled transfer, which may not be that MO's (`stock/models/stock_move_line.py:803-822`) | Accept. The pieces are interchangeable and the totals stay right |
| O5 | Viettel's acceptance of a buyer with no address or tax code | Send one real invoice before the first batch |
| O6 | Scrap entries already on production's 1541 or 1550 | Check production before go-live |

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

The type × band structure, the saved filters and SInvoice sending were not tested. The test instance has no
SInvoice login.

## 12. Rollout

| # | Step | Who |
|---|---|---|
| 1 | The list: internal reference, variant, seconds price, quantity | Peter |
| 2 | Check prices against cost and quantities against Odoo; propose types and bands | Claude, approved by Peter |
| 3 | `stock_scrap_downgrade`: spec, code, test | Claude writes, Peter runs |
| 4 | A setup script outside `addons/`, with check and commit modes, creating §7 | Claude writes |
| 5 | Rehearsal on `prod_copy`, then production | Peter runs |
| 6 | Count the seconds now held. Pieces still in finished goods go through the downgrade. Pieces no longer in Odoo have already left the books, so they enter by inventory adjustment at zero value, before any downgrade into that variant | Warehouse |
| 7 | Count finished goods, since defective pieces may be inside them | Warehouse |
| 8 | Brief MO handlers, the warehouse and sales on §3 and §4 | Peter |
| 9 | One real invoice to an employee, then the first sale day | Sales, accounting |
