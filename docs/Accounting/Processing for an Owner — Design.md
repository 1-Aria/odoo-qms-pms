# Processing for an Owner — Design

Nov 25, 2026 · @Peter · Status: draft for review

How a manufacturer works goods that belong to someone else (*gia công*), next to its own production, in Odoo 18
with OCA. The note defines the business flows generically: any company processing for an owner can use them by
configuration. Our own setup is one configuration of them (§8). The modules are
`stock_picking_type_partner_owner`, `mrp_production_partner_owner` and OCA `stock_owner_restriction`.

---

## 1. The concept

**A manufacturing order works for an owner.** The owner's material is used first. Where it runs short, the
manufacturer's own material goes in on top and is charged to the owner. The goods go back to the owner, or wherever
the owner instructs. An order without an owner is the manufacturer's own production.

Three facts of Odoo carry it:

| Fact | Reference |
|---|---|
| Stock can carry an owner (*Consignment*). Stock owned by another partner is left out of valuation, on the move and on the move line | `stock_account/models/stock_move.py:700-715`, `stock_move_line.py:121-130` |
| Without help, reservation takes any owner's stock, oldest first | `stock/models/stock_move.py:1957` (`strict=False`, no owner) |
| OCA `stock_owner_restriction` limits reservation to one owner, or to the company's own stock, by a context key it reads when gathering quants | `stock_owner_restriction/models/stock_quant.py:19-42`, `models/stock_move.py:81-100` |

## 2. The flows

| | **Own production** | **Order processing** (*gia công theo đơn*) | **Contract processing** (*gia công dài hạn*) |
|---|---|---|---|
| Business | The manufacturer makes and sells its goods | A customer orders goods made from its material; the sales order carries the processing fee | A standing agreement: the owner sends material over time, the manufacturer processes it as the owner plans, and invoices periodically |
| Owner of the order | none | the sales order's customer | a fixed partner (the contract's owner) |
| Material in | purchases | resupplied for the order: a receipt from the customer, created by the order, owned by the customer | receipts under the contract, without an order, owned by the owner |
| Order created by | planning, MTO, reordering | the sales order (MTO on the processing route) | planning, against the owner's orders |
| Goods produced belong to | the manufacturer | **the manufacturer**, valued at its input (§4.4) | **the owner**, not valued |
| Goods out | sales delivery | the sales order's delivery | a delivery type with the owner: only the owner's goods, to the owner or to whom the owner instructs |
| Invoice | the sale | the sales order: the fee per product; the manufacturer's material in it is priced in | periodic: goods processed × fee per product, plus the manufacturer's material used |
| Owner's material left over | — | returned to the customer | stays with the owner's stock, accounted for at the contract's settlement (*quyết toán*) |

**The rule behind deliveries:** a delivery ships the goods of the owner its flow names. A sales delivery ships the
manufacturer's goods, including those it processed for that customer (order processing). A contract delivery ships
the contract owner's goods. Nothing in either flow names a third party's goods, so neither can ship them.

## 3. Rules common to the flows

| # | Rule |
|---|---|
| R1 | **The order's owner decides reservation:** the owner's stock first, then the manufacturer's; an order without an owner takes the manufacturer's stock only. This covers the order's components and the transfers that supply them (*Pick Components*, *Resupply Subcontractor*). A component move fed by such a transfer keeps the owners its origin lines brought (`stock/models/stock_move.py:1965-1984`) |
| R2 | **The owner comes from the flow:** fixed on the operation type (contract processing), or the commercial partner of the sales order's customer (order processing). A child order, made for another order's component, takes its parent's owner. It can be changed by hand while the order is draft or confirmed |
| R3 | **One owner per order.** No finished good is split between owners |
| R4 | **Scrap and downgrade follow the goods:** a scrap made from an order takes the owner of the goods scrapped (the order's owner for its components; for finished goods, the owner they have). A downgrade keeps the scrap's owner (`stock_scrap_downgrade`, D10) |
| R5 | **Unbuild and returns keep the owner** of the lines they reverse (`mrp/models/mrp_unbuild.py:219-222`) |
| R6 | **Inventory counts are per owner.** A count line carries the owner of the stock counted; an owned line creates no valuation |
| R7 | **Outsourced processing** (subcontracting) of an owner's goods keeps the owner: the subcontracting type carries the same owner as the flow. The subcontractor's fee is the manufacturer's cost, recovered in its own fee to the owner |

## 4. Books

### 4.1 Owned stock is not in the manufacturer's books

Receiving, holding, moving, scrapping and delivering the owner's goods create no entry. The stock report grouped by
*Owner* shows them; the valuation report does not.

### 4.2 Contract processing

| Event | Entry |
|---|---|
| The manufacturer's material consumed by an order with an owner | Dr cost of sales (the product's expense account) / Cr stock: it is sold to the owner (`mrp_account/models/stock_move.py:31-34` is where the account is chosen) |
| Labour and overhead | stay in the production cost accounts (622, 627) and are closed to cost of sales at month end; nothing is absorbed into the owner's goods |
| Subcontractor's bill | Dr outside services (6277) / Cr payable, through the subcontractor's fiscal position (3399 → 6277): an owned subcontracted receipt credits nothing to the goods-received account |
| Periodic invoice to the owner | Dr receivable / Cr revenue (fees + material), Cr output VAT |

### 4.3 Order processing

| Event | Entry |
|---|---|
| Customer's material received and consumed | none |
| The manufacturer's material consumed | Dr production cost (1541) / Cr stock, as in own production |
| Goods produced | Dr finished goods / Cr production cost, at the manufacturer's input: its material plus conversion |
| Delivery | Dr goods issued not invoiced / Cr finished goods |
| Invoice of the sales order | revenue at the fee; cost of sales at the delivered value |

### 4.4 Why the goods of order processing stay the manufacturer's

A sales invoice values its cost of sales from the valuation layers of the delivered moves, and falls back to the
product's standard price when there are none (`stock_account/models/product.py:902-912`). Goods owned by the
customer are delivered without layers, so their invoice would book a cost against a delivery that booked nothing.
Kept as the manufacturer's goods, valued at its input, they are invoiced the native way: revenue is the fee, cost is
what the manufacturer put in. The customer's material is still the customer's: it is consumed without value. In
contract processing nothing is sold through a sales order, so the goods can belong to the owner.

## 5. Configuration

| Item | Own production | Order processing | Contract processing |
|---|---|---|---|
| Manufacturing operation type | *Manufacturing* (warehouse default), no owner | *Order Processing* type, owner from the sales order's customer, goods stay the manufacturer's | *Contract Processing* type, *Goods Owner* fixed, goods owned |
| Route | *Manufacture*, MTO for sales | *Order Processing* route (MTO + manufacture on its type), on the processed products or the sales-order line; components with *Resupply From Customer on Order* | none: orders are planned |
| Receipt | *Receipts* | *Resupply From Customer* (*Partner Owns the Goods*) | a receipt type with *Goods Owner* |
| Delivery | *Delivery Orders*, the manufacturer's stock only | *Delivery Orders*, the manufacturer's stock only; leftovers returned with an outgoing type owned by the partner | a delivery type with *Goods Owner*, restriction *Picking partner* |
| Subcontracting | — | — | the subcontracting type with the owner |
| *Pick Components*, the manufacturing types | restriction *Standard behavior*: the order decides (R1) | | |

## 6. Modules

| Module | Provides | State |
|---|---|---|
| `stock_picking_type_partner_owner` | step 1: *Partner Owns the Goods* on receipt and internal types; step 2: a fixed *Goods Owner* on any type | done |
| OCA `stock_owner_restriction` | reservation restricted by owner | installed on the test database |
| `mrp_production_partner_owner` | step 1: the order's owner from its type, R1, owned finished goods, the manufacturer's material to cost of sales, two reports | done |
| | step 1.1: R2 (owner from the sales order's customer on a type so marked; child orders), R4 (scrap owner), a type option for whether the goods produced belong to the owner (§4.4); *Partner Owns the Goods* also on outgoing types, for leftovers | planned |
| | step 2: the periodic invoice to an owner (contract processing): goods processed × fee, plus the manufacturer's material | planned |

## 7. Decisions

| # | Decision |
|---|---|
| P-1 | One mechanism, an owner on the manufacturing order; the flows are configurations of it, not code per partner |
| P-2 | In order processing the goods produced stay the manufacturer's, valued at its input; in contract processing they belong to the owner (§4.4) |
| P-3 | The manufacturer's material consumed for an owner is charged to the owner: through the sales order's price in order processing, on the periodic invoice in contract processing |
| P-4 | A delivery ships only the goods of the owner its flow names (§2) |

## 8. Our configuration

- **Contract processing for the trading company** (Công ty TNHH DV TM Quang Phương): the conversion of today's stock
  and the decisions specific to it are in `Material Ownership v2 — Processing Model.md`; subcontracted hammocks
  (Nhà Bàng) go through its subcontracting type.
- **Order processing for customers**: the existing *Resupply From Customer on Order* route (one component carries it
  today), the order-processing type and route to be added.
- **Own production**: *Manufacturing*.

## 9. Open points

1. The fee per product for contract processing, and how the periodic invoice is approved.
2. Order processing: the processing route on products or on sales-order lines (both work; the second needs
   *Routes on Sales Order Lines*).
3. Leftover customer material: returned at once, or held for the customer's next order.
