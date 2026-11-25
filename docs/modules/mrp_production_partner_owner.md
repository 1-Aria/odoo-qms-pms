# mrp_production_partner_owner

A manufacturing order can work for an owner (*gia công*): it reserves the owner's components first and the
company's after, and the company's components it uses are charged to the owner. The owner comes from the operation
type (a fixed *Goods Owner*), from the customer of the sales order behind the order, or from the parent order. Per
operation type, the goods produced belong to the owner and stay out of valuation (contract processing), or remain
the company's, valued at its input, and are sold on the sales order (order processing). An order without an owner is
the company's own production and reserves only the company's stock. Design: `docs/Accounting/Processing for an
Owner — Design.md`. Generic, in OCA's `<base_module>_<feature>` form, with unprefixed field names. Built on OCA
`stock_owner_restriction` and on `stock_picking_type_partner_owner` (*Goods Owner*, step 2; *Partner Owns the
Goods*, step 1).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The owner on the order; reservation by owner for components and *Pick Components*; finished goods owned; own components to the expense account; the two report menus | done | 2026-11-24: `-i` then `-u`, 9 post-tests passed (Peter's run). The first run failed 3: chained component moves reserved the owner's quants twice (fixed, D3a), and a test helper asked for a 0-unit backorder. UI check pending |
| 1.1 | Order processing and the owner's sources: *Products Belong to the Owner* on manufacturing types and orders; the owner from the sales order's customer; child orders take the parent's owner; scraps from an order take the owner of the goods; reports limited to owned production | done | 2026-11-25: `-u`, 15 post-tests passed (Peter's run). The owner from the sales order moved from `_post_run_manufacture` to the rule's `_prepare_mo_vals` before the code was delivered (D12). UI check (Tester, test database with the sandbox setup) passed: S00332 → WH/MOGC/00001 owned by Che Thơm, products ours; WH/SBC/00057 12 owned, no layer; WH/PC/01607 customer's 10 owned + Gòn 10 unowned; Áo gia công test +33,655 (Dr 1550 / Cr 1541); WH/OUT/00082 Dr 1599; INV/2026/00052 revenue 200,000, cost of sales Dr 6320 / Cr 1599 33,655; WH/RTGC/00001 the 2 owned leftover. The owner on transfer lines shows only in *Detailed Operations* (`stock/views/stock_move_views.xml:211, 254`) |
| 2 | The periodic invoice of contract processing: a fee per product and a draft invoice to the owner per period (goods processed × fee, plus the company's components consumed) | planned, specified after step 1.1 | |

## Divergences from the design

- The design note's §4 put the owner on "manufacturing operation types" through this module. The owner field on the
  operation type is `stock_picking_type_partner_owner`'s *Goods Owner* (its step 2), because delivery types need
  the same fixed owner. This module reads it.
- §3 books "Processing MO also using garment material: Dr 632 / Cr 1520". The account is the product's expense
  account, which is 6320 on this chart (D6).

## Decisions

| # | Decision |
|---|---|
| D1 | **The order carries the owner** (`mrp.production.owner_id`), filled at creation from its operation type's *Goods Owner*, editable while draft or confirmed. One owner per order (design D-V2-1). Orders that exist at install are not touched: the conversion's setup sets the owner on the open ones |
| D2 | **Reservation is driven by the order, not by the operation type.** `stock_owner_restriction` reads the restriction from the operation type (`stock_owner_restriction/models/stock_move.py:55-79`), but one *Pick Components* type serves every order. This module groups the moves that belong to an order and sets OCA's context key `force_restricted_owner_id` itself. OCA then limits the quants gathered to that owner (`models/stock_quant.py:19-42`, `models/stock_move.py:81-100`). The manufacturing and *Pick Components* types stay on *Standard behavior*, so OCA does not regroup them |
| D3 | **Which moves belong to an order:** its component moves (`raw_material_production_id`), and the moves whose destination moves are an order's component moves: *Pick Components*, and *Resupply Subcontractor* for a subcontracting order |
| D3a | **A chained move is left to core.** A component move fed by *Pick Components* reserves what its origin moves brought, line by line with their owners (`stock/models/stock_move.py:1965-1984`); the owner was chosen when *Pick Components* reserved. With the owner forced, OCA turns the unowned origin lines into the owner's (`stock_owner_restriction/models/stock_move.py:91-92`), and core, which creates the lines only after its loop, reserves the owner's quants twice (first install run, 2026-11-24: 10 owned lines on 6 owned units) |
| D4 | **With an owner:** first pass restricted to the owner, second pass, for what is still missing, restricted to the company's stock (`force_restricted_owner_id=False`). **Without an owner:** one pass, the company's stock only. An order of the company never takes another owner's goods (design §2.2) |
| D5 | **The finished goods belong to the owner.** The finished and by-product moves get `restrict_partner_id` = owner, which keeps them out of valuation at move level (`stock_account/models/stock_move.py:700-715`). Every move line created on an order's move without a reserved quant gets `owner_id` = owner: finished lines, by-product lines, and component lines typed beyond the stock (`stock/models/stock_move.py:2357-2368`). A line on a reserved quant keeps that quant's owner. The receipt into stock (*Store Finished Product*) then reserves the owned goods by its chained origin lines |
| D6 | **The company's own components consumed by an order with an owner go to the product's expense account** (6320 here) instead of the production cost account (1541). Core picks the production account in `_get_dest_account` (`mrp_account/models/stock_move.py:31-34`). These are the materials invoiced to the owner. The owner's components create no valuation (`stock_account/models/stock_move_line.py:121-130`) |
| D7 | **No conversion is absorbed into an owner's goods.** The finished move is not valued, so `mrp_bom_conversion_cost`'s extra unit cost moves no value. The labour and overhead of processing stay in 622/627 and are closed to cost of sales at month end, matched by the processing fee. The order still records its conversion minutes and rate |
| D8 | **Quantities typed beyond the reservation follow core:** core extends the line's quant, then takes any owner's quants in removal order (`stock/models/stock_move.py:2329-2355`), and only then creates a line from the move, which D5 gives the owner. *Check Availability* is the step that applies the owner's stock first |
| D9 | **Two reports, no new model.** *Company Material in Processing*: valuation layers of component moves of orders with an owner. *Processed Goods*: done finished moves of orders with an owner. They are the register and the quantity basis of the invoice to the owner |
| D10 | **Unbuild needs nothing.** Core copies the consumed lines' owner to the unbuild's moves (`mrp/models/mrp_unbuild.py:219-222`) |
| D11 | **Whether the products belong to the owner is a property of the flow** (step 1.1, design P-2): `production_owned` on the manufacturing type, default True, copied to the order at creation (a stored field, so a later change of the type does not change open orders). True is contract processing, as in step 1. False is order processing: the finished and by-product moves get no `restrict_partner_id` and their lines no owner, the company's components go to the production cost account as core does, and conversion is absorbed as core does, so the goods are valued at the company's input and the sales invoice costs them from their layers (`stock_account/models/product.py:902-912` falls back to the standard price without layers). Reservation is the same in both (D2, D4) |
| D12 | **The owner from the sales order's customer** (step 1.1): an order of a type with *Partner Owns the Goods* (`owner_from_partner`, from `stock_picking_type_partner_owner`) and still without owner takes the commercial partner of the customer of its linked sales order. It goes into the order's values in the manufacture rule's `_prepare_mo_vals`, from the procurement's `group_id`, which is the sales order's group. Not later: the rule confirms the orders it creates, which creates and reserves *Pick Components*, before `_post_run_manufacture`, where `sale_mrp` links the sales order to the order (`mrp/models/stock_rule.py:79-82`, `sale_mrp/models/mrp_production.py:56-60`). Read as superuser through `sale_id`, only when `sale_stock` adds it to groups, as `stock_picking_type_partner_owner` D5 does; no dependency on `sale_mrp`. Not for a child order (a destination move that is another order's component). An order made by hand on such a type gets its owner from the onchange, or by hand |
| D13 | **A child order takes its parent's owner and `production_owned`** (step 1.1): an order made for another order's component, found through `move_dest_ids.raw_material_production_id` as core reads it (`mrp/models/mrp_production.py:3059`). One owner for the whole tree (design R2, R3) |
| D14 | **Order of the sources at creation:** `owner_id` given in the values; else the parent order (D13); else the type's *Goods Owner*. The sales order's customer comes in the values from the manufacture rule (D12), so it counts as given |
| D15 | **A scrap made from an order takes the owner of the goods scrapped** (step 1.1, design R4): a scrap with `production_id` and without owner gets the order's owner when that owner holds stock of the product at the scrap's source location, else no owner. The owner's goods first, as in reservation; the company's stock when the owner has none there (a finished good of order processing, a component the company supplied). Set at creation and by an onchange on product, order and location. The downgrade of `stock_scrap_downgrade` keeps the scrap's owner (its D10) |
| D16 | **The reports count owned production only** (step 1.1): in order processing the company's material is priced into the sales order and its goods are sold there, so neither belongs to the periodic invoice |
| D17 | ***Partner Owns the Goods* shows on manufacturing types** (step 1.1), with its help extended to them; *Products Belong to the Owner* shows on manufacturing types only |

## Folder structure

```
mrp_production_partner_owner/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── mrp_production.py
│   ├── stock_move.py
│   ├── stock_picking_type.py      (step 1.1)
│   ├── stock_rule.py              (step 1.1)
│   └── stock_scrap.py             (step 1.1)
├── views/
│   ├── mrp_production_views.xml
│   ├── report_views.xml
│   └── stock_picking_type_views.xml   (step 1.1)
├── tests/
│   ├── __init__.py
│   └── test_production_owner.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `MRP Production Partner Owner` |
| `summary` | `Manufacturing orders that process another owner's goods` |
| `version` | `18.0.1.1.0` (step 1.1) |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Manufacturing/Manufacturing` |
| `depends` | `mrp_account`, `stock_owner_restriction`, `stock_picking_type_partner_owner` |
| `data` | `views/mrp_production_views.xml`, `views/report_views.xml`, `views/stock_picking_type_views.xml` (step 1.1) |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import mrp_production`, `from . import stock_move`, `from . import stock_picking_type`, `from . import stock_rule`, `from . import stock_scrap` |
| `tests/__init__.py` | `from . import test_production_owner` |

## Access

No access rules: the module adds fields to existing models.

## Models

### `mrp.production` — `models/mrp_production.py`

`_inherit = "mrp.production"`

| Field | Type | Attributes |
|---|---|---|
| `owner_id` | Many2one `res.partner` | `string="Goods Owner"`, `index=True`, `copy=True`, `tracking=True`, `help="The partner who owns the components taken first and the goods produced. Empty: the company's own production, from the company's stock only."` |
| `production_owned` | Boolean | step 1.1. `string="Products Belong to the Owner"`, `default=True`, `copy=True`, `help="The goods produced belong to the order's owner and stay out of valuation. Off: they remain the company's, valued at its input, for sale on the sales order (order processing)."` (D11) |

| Method | Decorator | Behaviour |
|---|---|---|
| `create` | `@api.model_create_multi` | `super()`; then, for each order (D14): without `production_owned` in its vals, the type's `production_owned`; without `owner_id` in its vals, the parent's owner and `production_owned` when it has a parent (D13), else its operation type's *Goods Owner*, read after `super()` so that a defaulted type counts too (D1); `write` puts the owner on the finished moves. An order created with `owner_id`, as the form does (it sends the owner and the finished moves together, the moves without `restrict_partner_id`), gets it on its open finished moves here (D5; found in the UI check, WH/MO/01777). Finished moves get the owner only when `production_owned` (D11) |
| `_get_parent_production` | — | step 1.1. `ensure_one`. `move_dest_ids.raw_material_production_id[:1]` (D13) |
| `_get_sale_owner` | — | step 1.1. `ensure_one`. When procurement groups have `sale_id`: the commercial partner of `procurement_group_id.sudo().sale_id.partner_id`, browsed back in the user's environment; else an empty partner (D12) |

| `_onchange_owner_from_type` | `@api.onchange("picking_type_id")` | Draft or confirmed orders: `owner_id` = `picking_type_id.owner_partner_id` (core lets the type change until confirmed, `mrp/views/mrp_production_views.xml:539`); step 1.1: also `production_owned` = the type's, and, on a type with `owner_from_partner`, the owner `_get_sale_owner()` when found |
| `_get_move_finished_values` | — | `super()`, plus `restrict_partner_id` = `owner_id.id` when set and `production_owned` (D5, D11) |
| `write` | — | `super()`; then, when `owner_id` or `production_owned` changes: the finished moves not done or cancelled get `restrict_partner_id` = the owner when `production_owned`, else none (D5, D11) |
| `_get_backorder_mo_vals` | — | `super()`, plus `owner_id` and `production_owned` |

### `stock.move` — `models/stock_move.py`

`_inherit = "stock.move"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_get_owner_production` | — | `ensure_one`. The order the move works for: `raw_material_production_id` or `production_id`; else the first `move_dest_ids.raw_material_production_id`; else an empty order (D3) |
| `_action_assign` | — | Moves with an order and without chained origin moves (D3a) go by the order's `owner_id` (D2, D4). With an owner: `super()` with `force_restricted_owner_id` = the owner, then `super()` with `force_restricted_owner_id=False` for those still `confirmed` or `partially_available`. Without an owner: `super()` with `force_restricted_owner_id=False`. Other moves: `super()` unchanged |
| `_prepare_move_line_vals` | — | `super()`. When no `reserved_quant` is given and `_get_owner_production().owner_id` is set: `owner_id` = that owner (D5, D8); step 1.1: for a finished or by-product move (`production_id`), only when the order's `production_owned` (D11) |
| `_get_dest_account` | — | For a component move consumed into production (`_is_production_consumed()`) of an order with an owner and `production_owned`: the product's `expense` account from `accounts_data`. Otherwise `super()` (D6, D11) |

### `stock.picking.type` — `models/stock_picking_type.py` (step 1.1)

`_inherit = "stock.picking.type"`

| Field | Type | Attributes |
|---|---|---|
| `production_owned` | Boolean | `string="Products Belong to the Owner"`, `default=True`, `help="Manufacturing orders of this type produce goods owned by their owner, left out of valuation (contract processing). Off: the goods remain the company's, valued at its input, for sale on the sales order (order processing)."` |
| `owner_from_partner` | Boolean | redefined for its help only: `help="Transfers of this type assign the goods to their partner as owner, or, without a partner, to the customer of their sales order. Manufacturing orders of this type take the customer of their sales order as owner. An owner set by hand is kept."` |

### `stock.rule` — `models/stock_rule.py` (step 1.1)

`_inherit = "stock.rule"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_prepare_mo_vals` | — | `super()`; then, when the values have no `owner_id`, the rule's operation type has `owner_from_partner` and no *Goods Owner*, the procurement has a `group_id` with `sale_id` (groups have the field) and no destination move is another order's component: `owner_id` = the commercial partner of the group's sales order's customer, read as superuser (D12) |

### `stock.scrap` — `models/stock_scrap.py` (step 1.1)

`_inherit = "stock.scrap"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_get_production_owner` | — | `ensure_one`. With `production_id` whose `owner_id` is set: that owner when the sum of the owner's quants of `product_id` at `location_id` (`child_of`) is above zero; else an empty partner (D15) |
| `create` | `@api.model_create_multi` | `super()`; then each scrap created without `owner_id` in its vals: `owner_id` = `_get_production_owner()` when found |
| `_onchange_owner_from_production` | `@api.onchange("product_id", "production_id", "location_id")` | `owner_id` = `_get_production_owner()` when found |

## Views

### `views/mrp_production_views.xml`

| Record | Inherits | Content |
|---|---|---|
| `mrp_production_form_view` | `mrp.mrp_production_form_view` | `owner_id` after the *Miscellaneous* tab's `picking_type_id`, `readonly="state not in ('draft', 'confirmed')"`; step 1.1: `production_owned` after it, same `readonly`, `invisible="not owner_id"` |
| `mrp_production_tree_view` | `mrp.mrp_production_tree_view` | `owner_id`, `optional="show"` |
| `view_mrp_production_filter` | `mrp.view_mrp_production_filter` | field `owner_id` after `picking_type_id`; filters *Processing* `[('owner_id', '!=', False)]` and *Own Production* `[('owner_id', '=', False)]` after *Cancelled*; group by `owner_id` after *Procurement Group* |

### `views/report_views.xml`

| Record | Content |
|---|---|
| `action_processing_material` | *Company Material in Processing*: `ir.actions.act_window` on `stock.valuation.layer`, `view_mode` `list,pivot`, domain `[('stock_move_id.raw_material_production_id.owner_id', '!=', False)]`, step 1.1 plus `('stock_move_id.raw_material_production_id.production_owned', '=', True)` (D16), context grouping by product |
| `action_processed_goods` | *Processed Goods*: on `stock.move`, `view_mode` `pivot,list`, domain `[('production_id.owner_id', '!=', False), ('state', '=', 'done')]`, step 1.1 plus `('production_id.production_owned', '=', True)` (D16), pivot rows by product, columns by date (month), measure `quantity` |
| `view_processed_goods_pivot` | `stock.move` pivot, priority 99: rows product, columns date by month, measure `quantity` |
| menus | under *Manufacturing → Reporting*: *Company Material in Processing* for `stock.group_stock_manager`, since valuation layers are readable by stock managers only (`stock_account/security/ir.model.access.csv:8`); *Processed Goods* for `mrp.group_mrp_manager` |

### `views/stock_picking_type_views.xml` (step 1.1)

| Record | Inherits | Content |
|---|---|---|
| `view_picking_type_form` | `stock_picking_type_partner_owner.view_picking_type_form` | `owner_from_partner`: `invisible="code not in ('incoming', 'internal', 'outgoing', 'mrp_operation')"`; `production_owned` after it, `invisible="code != 'mrp_operation'"` (D17) |

## Tests

`tests/test_production_owner.py`, `TestProductionOwner(TransactionCase)`, `@tagged("post_install", "-at_install")`:
the fixtures create a company, products and partners.

**Fixtures (`setUpClass`):**
- a company of its own in the env's `allowed_company_ids`; its warehouse switched to manufacture in two steps
  (`manufacture_steps = "pbm"`), so orders get a *Pick Components* transfer;
- a partner *Owner*;
- two storable AVCO real-time products, component A at cost 10 and finished F, with a category whose valuation,
  input, output, production cost and expense accounts are distinct accounts of the company;
- a BoM F ← 1 A;
- a manufacturing operation type *Processing* with `owner_partner_id` = *Owner*. The warehouse's own
  manufacturing type is left without an owner.

**Helpers:** `_stock(product, qty, owner=None, location=stock)` sets quants through `_update_available_quantity`
with a valuation layer for unowned stock; `_order(qty, picking_type)` creates and confirms an order;
`_produce(order)` sets `qty_producing`, picks the components and marks the order done.

| Test | Asserts |
|---|---|
| `test_owner_from_type` | an order of *Processing* gets `owner_id` *Owner*; of the warehouse type, none; an owner given at create is kept; its finished move has `restrict_partner_id` *Owner* |
| `test_owner_from_form` | an order made through `Form` on *Processing*: `owner_id` *Owner* and its finished move's `restrict_partner_id` *Owner* |
| `test_reserve_owner_first` | 6 A owned by *Owner*, 10 A unowned, an order of 10 on *Processing*: the *Pick Components* move reserves 6 owned + 4 unowned |
| `test_own_production_company_only` | the same stock, an order of 10 on the warehouse type: reserves 10 unowned, none owned |
| `test_own_production_partial` | 6 owned and 3 unowned: 3 unowned reserved, none owned, state `partially_available` |
| `test_finished_owned_not_valued` | *Processing* order of 10 done from 6 owned + 4 unowned A: F quant owned by *Owner*, 10; no valuation layer value and no account entry on the finished move; the owned component lines create no layer; the unowned 4 create a layer of −40 whose entry debits the expense account, not the production cost account |
| `test_own_production_valued` | warehouse-type order of 10 from unowned A: F unowned with a layer of +100; the components' entry debits the production cost account (core unchanged) |
| `test_excess_line_owned` | *Processing* order with 0 A in stock: the component quantity typed by hand creates a line owned by *Owner* |
| `test_backorder_keeps_owner` | a *Processing* order of 10 produced 4 with a backorder: the backorder's `owner_id` is *Owner* |
| `test_reports` | after `test_finished_owned_not_valued`'s flow, `action_processing_material`'s domain finds the −40 layer and `action_processed_goods`'s the finished move |

Step 1.1 adds two fixtures: a customer company and its contact; a manufacturing type *Order Processing*, a copy of
the warehouse type with `owner_from_partner` True and `production_owned` False.

| Test | Asserts |
|---|---|
| `test_order_processing_goods_ours` | an order of 10 on *Order Processing* with owner the customer, from 6 A owned by the customer + 4 unowned: *Pick Components* reserves 6 owned + 4 unowned; done: F unowned with a layer of +40; the finished move has no `restrict_partner_id`; the components' entry debits the production cost account, not the expense account |
| `test_owner_from_sale_order` | skipped when procurement groups have no `sale_id`. A sales order for the contact and a procurement group with its `sale_id`; a route with a copy of the warehouse's manufacture rule on *Order Processing*, set on F; a procurement of 5 F into stock with that group run: one order on *Order Processing*, `owner_id` the customer company, `production_owned` False, no `restrict_partner_id` on its finished move. The BoM is made `active` first when `mrp_bom_version` adds `state` (it finds active BoMs only) |
| `test_child_takes_parent_owner` | a confirmed *Processing* order; an order on the warehouse type created with `move_dest_ids` = the parent's component move: `owner_id` *Owner*, `production_owned` True |
| `test_scrap_owner` | after *Pick Components* of a *Processing* order is validated (6 owned + 4 unowned A at Pre-Production): a scrap of A from the order at Pre-Production gets owner *Owner*; with the owner's A gone from Pre-Production (moved back by an inventory move), a new scrap gets none; a scrap from an order of the warehouse type gets none |
| `test_reports_owned_only` | after `test_order_processing_goods_ours`'s flow, neither report's domain finds its layer or its finished move |

## Readme

- `DESCRIPTION.md`: an operation type's *Goods Owner* makes its manufacturing orders work for that owner; the
  owner's components are reserved first, the goods produced are the owner's and left out of valuation, and the
  company's components consumed are charged to cost of sales for invoicing to the owner.
- `USAGE.md`: contract processing: a manufacturing type (and the subcontracting type) with *Goods Owner*;
  order processing: a manufacturing type with *Partner Owns the Goods* and without *Products Belong to the Owner*,
  on a route with MTO and a manufacture rule on that type, the components resupplied from the customer; leave the
  manufacturing and *Pick Components* types' *Owner restriction* on *Standard behavior*; the warehouse's own type
  without owner for own production; the two reports under *Manufacturing → Reporting*.
