# mrp_production_partner_owner

A manufacturing order can work for an owner: the operation type names the owner of the goods (*Goods Owner*), and
its orders reserve that owner's components first and the company's after, produce goods owned by that owner and
left out of valuation, and charge the company's own components they consume to the product's expense account. An
order without an owner reserves only the company's stock. The first use is processing (*gia công*) for the trading
company: `docs/Accounting/Material Ownership v2 — Processing Model.md` §2.2 and §4. Generic, in OCA's
`<base_module>_<feature>` form, with unprefixed field names. Built on OCA `stock_owner_restriction` and on the
*Goods Owner* of `stock_picking_type_partner_owner` (its step 2).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The owner on the order; reservation by owner for components and *Pick Components*; finished goods owned; own components to the expense account; the two report menus | done | 2026-11-24: `-i` then `-u`, 9 post-tests passed (Peter's run). The first run failed 3: chained component moves reserved the owner's quants twice (fixed, D3a), and a test helper asked for a 0-unit backorder. UI check pending |
| 2 | The processing invoice: a fee per product and a draft invoice to the owner per period (finished goods × fee, plus the company's components consumed) | planned, specified after step 1 | |

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

## Folder structure

```
mrp_production_partner_owner/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── mrp_production.py
│   └── stock_move.py
├── views/
│   ├── mrp_production_views.xml
│   └── report_views.xml
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
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Manufacturing/Manufacturing` |
| `depends` | `mrp_account`, `stock_owner_restriction`, `stock_picking_type_partner_owner` |
| `data` | `views/mrp_production_views.xml`, `views/report_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import mrp_production`, `from . import stock_move` |
| `tests/__init__.py` | `from . import test_production_owner` |

## Access

No access rules: the module adds one field to an existing model.

## Models

### `mrp.production` — `models/mrp_production.py`

`_inherit = "mrp.production"`

| Field | Type | Attributes |
|---|---|---|
| `owner_id` | Many2one `res.partner` | `string="Goods Owner"`, `index=True`, `copy=True`, `tracking=True`, `help="The partner who owns the components taken first and the goods produced. Empty: the company's own production, from the company's stock only."` |

| Method | Decorator | Behaviour |
|---|---|---|
| `create` | `@api.model_create_multi` | `super()`; then each order created without `owner_id` in its vals takes its operation type's *Goods Owner*, read after `super()` so that a defaulted type counts too (D1), and `write` puts it on the finished moves. An order created with `owner_id`, as the form does (it sends the owner and the finished moves together, the moves without `restrict_partner_id`), gets it on its open finished moves here (D5; found in the UI check, WH/MO/01777) |
| `_onchange_owner_from_type` | `@api.onchange("picking_type_id")` | Draft or confirmed orders: `owner_id` = `picking_type_id.owner_partner_id` (core lets the type change until confirmed, `mrp/views/mrp_production_views.xml:539`) |
| `_get_move_finished_values` | — | `super()`, plus `restrict_partner_id` = `owner_id.id` when set (D5) |
| `write` | — | When `owner_id` changes: the finished moves not done or cancelled get `restrict_partner_id` = the new owner (D5). Then `super()` |
| `_get_backorder_mo_vals` | — | `super()`, plus `owner_id` |

### `stock.move` — `models/stock_move.py`

`_inherit = "stock.move"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_get_owner_production` | — | `ensure_one`. The order the move works for: `raw_material_production_id` or `production_id`; else the first `move_dest_ids.raw_material_production_id`; else an empty order (D3) |
| `_action_assign` | — | Moves with an order and without chained origin moves (D3a) go by the order's `owner_id` (D2, D4). With an owner: `super()` with `force_restricted_owner_id` = the owner, then `super()` with `force_restricted_owner_id=False` for those still `confirmed` or `partially_available`. Without an owner: `super()` with `force_restricted_owner_id=False`. Other moves: `super()` unchanged |
| `_prepare_move_line_vals` | — | `super()`. When no `reserved_quant` is given and `_get_owner_production().owner_id` is set: `owner_id` = that owner (D5, D8) |
| `_get_dest_account` | — | For a component move consumed into production (`_is_production_consumed()`) of an order with an owner: the product's `expense` account from `accounts_data`. Otherwise `super()` (D6) |

## Views

### `views/mrp_production_views.xml`

| Record | Inherits | Content |
|---|---|---|
| `mrp_production_form_view` | `mrp.mrp_production_form_view` | `owner_id` after the *Miscellaneous* tab's `picking_type_id`, `readonly="state not in ('draft', 'confirmed')"` |
| `mrp_production_tree_view` | `mrp.mrp_production_tree_view` | `owner_id`, `optional="show"` |
| `view_mrp_production_filter` | `mrp.view_mrp_production_filter` | field `owner_id` after `picking_type_id`; filters *Processing* `[('owner_id', '!=', False)]` and *Own Production* `[('owner_id', '=', False)]` after *Cancelled*; group by `owner_id` after *Procurement Group* |

### `views/report_views.xml`

| Record | Content |
|---|---|
| `action_processing_material` | *Company Material in Processing*: `ir.actions.act_window` on `stock.valuation.layer`, `view_mode` `list,pivot`, domain `[('stock_move_id.raw_material_production_id.owner_id', '!=', False)]`, context grouping by product |
| `action_processed_goods` | *Processed Goods*: on `stock.move`, `view_mode` `pivot,list`, domain `[('production_id.owner_id', '!=', False), ('state', '=', 'done')]`, pivot rows by product, columns by date (month), measure `quantity` |
| `view_processed_goods_pivot` | `stock.move` pivot, priority 99: rows product, columns date by month, measure `quantity` |
| menus | under *Manufacturing → Reporting*: *Company Material in Processing* for `stock.group_stock_manager`, since valuation layers are readable by stock managers only (`stock_account/security/ir.model.access.csv:8`); *Processed Goods* for `mrp.group_mrp_manager` |

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

## Readme

- `DESCRIPTION.md`: an operation type's *Goods Owner* makes its manufacturing orders work for that owner; the
  owner's components are reserved first, the goods produced are the owner's and left out of valuation, and the
  company's components consumed are charged to cost of sales for invoicing to the owner.
- `USAGE.md`: set *Goods Owner* on a manufacturing operation type (and on the subcontracting type); leave the
  manufacturing and *Pick Components* types' *Owner restriction* on *Standard behavior*; use a second
  manufacturing type without an owner for the company's own production; the two reports under
  *Manufacturing → Reporting*.
