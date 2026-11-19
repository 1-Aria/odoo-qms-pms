# stock_scrap_downgrade

A scrap into a location marked as a downgrade location also receives a chosen lower-grade product: same quantity,
at the scrapped goods' cost, in the same transaction. The first use is garment seconds (*hàng loại 2*). Generic, in
OCA's `<base_module>_<feature>` form, with unprefixed field names. Context:
`docs/Accounting/Defective Goods and Seconds — Design.md` §6.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The location's category, the lower-grade product on the scrap with its proposal, the receipt at cost | done | 2026-11-18: `-i`, 12 post-tests passed (Peter's run). Database check: SP/00005 and SP/00006, 3 × PANT00589 from WH/MO/00611-001 to PR/00209; value out equals value in (3,218 and 1,609); every entry on 1550 only; WH/SFP/01428 reserved 93 of 96; downgrade location totals 0. Both UI scraps were made by an administrator; a plain stock user is covered by `test_as_stock_user` |

## Divergences from the design

None.

## Decisions

| # | Decision |
|---|---|
| D1 | **The location decides.** A scrap is a downgrade when its `scrap_location_id` has `downgrade_categ_id`. No separate action or wizard: the *Scrap* form is core's, from the MO (`stock_scrap_form_view2`) and from Inventory (`stock_scrap_form_view`) |
| D2 | **The receipt is a plain move with `scrap_id` set, without a picking.** It then shows in the scrap's *Product Moves* (`stock/models/stock_scrap.py:181-184`) and in valuation views that read `scrap.move_ids`, with no new field. It follows core's own scrap move (`stock_scrap.py:120-157`) |
| D3 | **`scrapped` needs no value.** It is related to the destination's `scrap_location` (`stock/models/stock_move.py:141-142`), so it is False on the receipt, which tells the receipt from the scrap's own move |
| D4 | **The cost is the value actually taken out:** the negated sum of the valuation layers of the scrap's moves, divided by the scrapped quantity in the product's unit. Summing the layers also covers a kit, whose scrap has several moves. Layers are read as superuser: only stock managers may read them (`stock_account/security/ir.model.access.csv:8`) |
| D5 | **A zero value stays zero.** An incoming move with `price_unit` 0 otherwise takes the product's average cost (`stock_account/models/stock_move.py:69-79`), so `_should_force_price_unit` is extended for the receipt |
| D6 | **No proposal table.** The proposal reads the last done downgrade into the same location: of the same variant, else of the same product template |
| D7 | **The accounts are configuration.** The entries come from the location's *Incoming* and *Outgoing* valuation accounts (`stock_account/models/stock_move.py:536-543`). The module reads and checks no account |
| D8 | **Core's other scrap behaviour is unchanged,** including the insufficient-quantity warning, which ends in `do_scrap` (`stock/wizard/stock_warn_insufficient_qty.py:45-46`) |
| D9 | **No undo.** A downgrade is corrected by hand with transfers |

## Folder structure

```
stock_scrap_downgrade/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── stock_location.py
│   ├── stock_move.py
│   └── stock_scrap.py
├── views/
│   ├── stock_location_views.xml
│   └── stock_scrap_views.xml
├── tests/
│   ├── __init__.py
│   └── test_scrap_downgrade.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Stock Scrap Downgrade` |
| `summary` | `Scrap goods into a lower-grade product at their cost` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Inventory/Inventory` |
| `depends` | `stock_account` |
| `data` | `views/stock_location_views.xml`, `views/stock_scrap_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import stock_location`, `from . import stock_move`, `from . import stock_scrap` |
| `tests/__init__.py` | `from . import test_scrap_downgrade` |

## Access

No access rules: the module adds fields to existing models. Whoever may scrap may downgrade.

## Models

### `stock.location` — `models/stock_location.py`

`_inherit = "stock.location"`

| Field | Type | Attributes |
|---|---|---|
| `downgrade_categ_id` | Many2one `product.category` | `string="Downgrade Category"`, `help="Scrapping into this location downgrades the goods: a product of this category is received in their place, at their cost."` |

### `stock.scrap` — `models/stock_scrap.py`

`_inherit = "stock.scrap"`

| Field | Type | Attributes |
|---|---|---|
| `downgrade_categ_id` | Many2one `product.category` | `related="scrap_location_id.downgrade_categ_id"` |
| `downgrade_product_id` | Many2one `product.product` | `string="Downgrade To"`, `compute="_compute_downgrade_product_id"`, `store=True`, `readonly=False`, `check_company=True`, `domain="[('categ_id', 'child_of', downgrade_categ_id), ('uom_id.category_id', '=', product_uom_category_id), ('is_storable', '=', True), ('tracking', '=', 'none')]"` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_downgrade_product_id` | `@api.depends("product_id", "scrap_location_id")` | For each scrap: `_last_downgrade_product()` when it has `downgrade_categ_id` and `product_id`, else empty. Always assigns |
| `_last_downgrade_product` | — | `ensure_one`. Base domain: `state = done`, same `scrap_location_id`; `downgrade_product_id` stays out of it, because searching on it inside its own compute would flush that compute. Searches with `limit=1`, in the model's order (newest first), for the same `product_id`, then for the same `product_id.product_tmpl_id`. Returns the found scrap's `downgrade_product_id`, or an empty product (D6) |
| `do_scrap` | — | `downgrades` = the scraps with `downgrade_categ_id`. When one has no `downgrade_product_id`: `UserError` naming its product, before anything moves. `super()`, keeping its result. Then `_receive_downgrade_product()` on each of `downgrades`. Returns the result |
| `_receive_downgrade_product` | — | `ensure_one`. Quantity: `scrap_qty` from `product_uom_id` to `product_id.uom_id`. Value: minus the sum of `value` over `move_ids.sudo().stock_valuation_layer_ids` (D4). Destination: `lot_stock_id` of `location_id.warehouse_id`, or of the company's first warehouse. Creates the move below, then calls `_action_done()` on it |

Values of the receipt move:

| Field | Value |
|---|---|
| `name` | the scrap's `name` |
| `origin` | the scrap's `origin` or `name` |
| `company_id` | the scrap's company |
| `product_id` | `downgrade_product_id` |
| `product_uom` | `downgrade_product_id.uom_id` |
| `product_uom_qty` | the quantity |
| `location_id` | `scrap_location_id` |
| `location_dest_id` | the destination |
| `price_unit` | value ÷ quantity |
| `scrap_id` | the scrap |
| `state` | `draft` |
| `picked` | `True` |
| `move_line_ids` | one line: `product_id`, `product_uom_id`, `quantity`, `location_id` and `location_dest_id`, as above |

### `stock.move` — `models/stock_move.py`

`_inherit = "stock.move"`

| Method | Behaviour |
|---|---|
| `_should_force_price_unit` | True when the move has `scrap_id` and is not `scrapped`; otherwise `super()` (D3, D5) |

## Views

### `views/stock_location_views.xml`

`view_location_form`, inheriting `stock.view_location_form`.

| Position | Content |
|---|---|
| `//field[@name='scrap_location']` after | `downgrade_categ_id`, `invisible="not scrap_location or usage != 'inventory'"`, `options="{'no_create': True}"` |

### `views/stock_scrap_views.xml`

| Record | Inherits | Position | Content |
|---|---|---|---|
| `stock_scrap_form_view` | `stock.stock_scrap_form_view` | `//field[@name='scrap_location_id']` after | `downgrade_product_id`, `invisible="not downgrade_categ_id"`, `required="downgrade_categ_id"`, `readonly="state == 'done'"`, `options="{'no_create': True}"` |
| `stock_scrap_form_view2` | `stock.stock_scrap_form_view2` | `//field[@name='scrap_location_id']` after | the same |
| `stock_scrap_tree_view` | `stock.stock_scrap_tree_view` | `//field[@name='scrap_location_id']` after | `downgrade_product_id`, `readonly="1"`, `optional="show"` |

## Tests

`tests/test_scrap_downgrade.py`, `TestScrapDowngrade(TransactionCase)`, `@tagged("post_install", "-at_install")`:
the fixtures create a company and products.

**Fixtures (`setUpClass`):** a Vietnamese company of its own in VND with the `vn` chart, put in the env's
`allowed_company_ids`, and its warehouse, which `stock` creates. Accounts created in that company: stock valuation,
stock input, stock output and scrap expense. The chart's `STJ` journal. A category *Goods* and a category *Seconds*, both AVCO and real-time, with those accounts and journal. A
template *Style* in *Goods* with a two-value attribute, so two variants; a product *Other* in *Goods*; a product
*Second* and a product *Second B* in *Seconds*. A scrap location *Downgrade*, `usage` `inventory`, with
`downgrade_categ_id` *Seconds* and both valuation accounts set to stock valuation. A scrap location *Waste*,
`usage` `inventory`, with its incoming valuation account set to scrap expense.

**Helpers:** `_stock_in(product, quantity, price)` validates a move from the supplier location to the warehouse's
stock at that `price_unit`. `_scrap(product, quantity, location, **values)` creates a scrap from the warehouse's
stock and calls `do_scrap`. `_on_hand(product)` is the quantity in the warehouse's stock. `_value(product)` is
the sum of the product's valuation layers in the company.

| Test | Asserts |
|---|---|
| `test_downgrade_moves_stock` | 10 of a variant in at 100; 3 downgraded to *Second*: the variant 7 on hand, *Second* 3; the *Downgrade* location holds +3 of the variant and −3 of *Second*; the scrap has 2 moves, both done |
| `test_cost_follows_the_goods` | the same: the variant's value 700, *Second*'s value 300 and `standard_price` 100 |
| `test_entries_stay_on_valuation` | the same: the two moves' journal entries have lines on the stock valuation account only, debits equal to credits, 300 each way |
| `test_average_of_two_sources` | 3 of one variant at 100 and 1 of *Other* at 200 downgraded to *Second*: on hand 4, value 500, `standard_price` 125 |
| `test_zero_cost_stays_zero` | 2 at 100 downgraded to *Second*; then 2 of *Other*, in at price 0 and `standard_price` 0, downgraded to it: on hand 4, value 200, `standard_price` 50 |
| `test_unit_conversion` | 24 of a variant in at 10; 1 dozen downgraded, `product_uom_id` the dozen: the variant 12 on hand, *Second* 12, value 120 |
| `test_refused_without_product` | a downgrade scrap of a product never downgraded, no `downgrade_product_id`: `do_scrap` raises `UserError`; on hand and the scrap's state unchanged |
| `test_ordinary_scrap` | a scrap into *Waste*: empty `downgrade_product_id`, one move, nothing of *Second* received, the value debited to scrap expense |
| `test_proposal` | after a done downgrade of variant 1 to *Second* and a later one of *Other* to *Second B*: a new scrap of variant 1 into *Downgrade* proposes *Second*; of variant 2 proposes *Second* (same template); of *Other* proposes *Second B*; of a product with no history proposes nothing; changing variant 1's scrap location to *Waste* empties it |
| `test_variant_first` | variant 1 downgraded to *Second*, then variant 2 to *Second B*: a new scrap of variant 1 proposes *Second*; a new scrap of variant 2 proposes *Second B* |
| `test_proposal_kept_when_changed` | a draft scrap whose proposal is replaced by writing *Second B*: `do_scrap` receives *Second B* |
| `test_as_stock_user` | a user of the company with only *Inventory / User*, in an environment limited to that company: reading a valuation layer raises `AccessError` (positive control for the sudo); the same user's downgrade succeeds and *Second*'s value is correct |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Scrapping into a location with a *Downgrade Category* removes the goods and receives a chosen product of that category in their place: same quantity, at the cost of the goods removed, in one step |
| `readme/USAGE.md` | Create a virtual scrap location (*Inventory Loss*, *Is a Scrap Location*); set its *Downgrade Category* and its *Incoming* and *Outgoing* valuation accounts, normally the stock valuation account of both products. In the *Scrap* form choose that location and the *Downgrade To* product, which is proposed from the last downgrade of the same product |
