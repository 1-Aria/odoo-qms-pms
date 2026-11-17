# stock_picking_type_partner_owner

An operation type can say that the goods its transfers move belong to the partner. Its transfers then get
the partner as *Owner* (`owner_id`) when none is set: in the form as soon as the partner is chosen, and in any
case at validation, where a transfer without a partner — a receipt created by a manufacturing order — takes the
customer of its sales order. The first use is *Resupply From Customer*: material customers send for processing,
which then stays out of the company's stock valuation. Generic, in OCA's `<base_module>_<feature>` form, with
unprefixed field names. Context: `docs/Accounting/VN Vouchers — Design.md` §5.1 (customer material).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The operation-type flag; the owner set in the form and at validation, with the sales-order fallback | spec | |

## Divergences from the design

None.

## Decisions

| # | Decision |
|---|---|
| D1 | **The owner is the commercial partner** (`commercial_partner_id`): quants of one customer are not split between the company and its contacts |
| D2 | **An owner already on the transfer is never replaced;** the module only fills an empty one, so a different owner can be set by hand |
| D3 | **Validation is the hook that matters:** `stock.picking._action_done` is overridden to fill the owner before `super()`, which copies it to the moves' `restrict_partner_id` and the move lines' `owner_id` (`stock/models/stock_picking.py:1256-1260`). Every transfer passes there, including those created by procurement |
| D4 | **The form shows the owner earlier** through an onchange on the partner and the operation type, from the transfer's partner only |
| D5 | **Without a partner, the customer of the sales order behind the moves' procurement group** (`group_id.sale_id.partner_id`, read as superuser, only when `sale_stock` adds `sale_id` to groups, `sale_stock/models/stock.py:84`). A *Resupply From Customer* receipt is created by a manufacturing order and has no partner (WH/SBC/00027: group WH/MO/01716, sales order S00071). No dependency on `sale_stock` |
| D6 | **Nothing else changes.** Reservation already takes quants of any owner when a move names none (`stock/models/stock_move.py:1957`, `strict=False`), so manufacturing consumes the customer's material; moves and lines with an owner other than the company are left out of valuation by `stock_account` (`stock_account/models/stock_move_line.py:121-128`, `stock_move.py:700`). Material of one customer can be reserved for another's order, as for any owned stock; OCA `stock_owner_restriction` would restrict it and is not used |

## Folder structure

```
stock_picking_type_partner_owner/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── stock_picking_type.py
│   └── stock_picking.py
├── views/
│   └── stock_picking_type_views.xml
├── tests/
│   ├── __init__.py
│   └── test_partner_owner.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Stock Picking Type Partner Owner` |
| `summary` | `Operation types whose transfers assign the goods to the partner as owner` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Inventory/Inventory` |
| `depends` | `stock` |
| `data` | `views/stock_picking_type_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import stock_picking_type`, `from . import stock_picking` |
| `tests/__init__.py` | `from . import test_partner_owner` |

## Access

No access rules: the module adds one field to an existing model.

## Models

### `stock.picking.type` — `models/stock_picking_type.py`

`_inherit = "stock.picking.type"`

| Field | Type | Attributes |
|---|---|---|
| `owner_from_partner` | Boolean | `string="Partner Owns the Goods"`, `help="Transfers of this type assign the goods to their partner as owner, or, without a partner, to the customer of their sales order. An owner set by hand is kept."` |

### `stock.picking` — `models/stock_picking.py`

`_inherit = "stock.picking"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_get_partner_owner` | — | `ensure_one`. `partner_id.commercial_partner_id`; else, when procurement groups have `sale_id`, the commercial partner of `group_id.sudo().sale_id.partner_id`, browsed back in the user's environment; else an empty partner (D1, D5) |
| `_onchange_owner_from_partner` | `@api.onchange("partner_id", "picking_type_id")` | When the type has `owner_from_partner` and `owner_id` is empty: `owner_id` = `partner_id.commercial_partner_id` (D2, D4) |
| `_action_done` | — | For each transfer whose type has `owner_from_partner` and whose `owner_id` is empty: `owner_id` = `_get_partner_owner()` when found. Then `super()` (D2, D3) |

## Views — `views/stock_picking_type_views.xml`

One record, `view_picking_type_form`, inheriting `stock.view_picking_type_form`.

| Position | Content |
|---|---|
| `//field[@name='create_backorder']` after | `owner_from_partner`, `invisible="code not in ('incoming', 'internal')"` |

## Tests

`tests/test_partner_owner.py`, `TestPartnerOwner(TransactionCase)`, `@tagged("post_install", "-at_install")`:
the fixtures create a company, products and partners.

**Fixtures (`setUpClass`):** a company of its own, put in the env's `allowed_company_ids`, and its warehouse,
which `stock` creates; a storable product with `standard_price` 100; a customer company and its contact; an
incoming operation type *Resupply From Customer test* (`code` `incoming`, from the customer location to the
warehouse's stock, `owner_from_partner` True); the warehouse's own receipt type, without the flag.

**Helpers:** `_receipt(picking_type, partner=None, **values)` creates a receipt of 5 units;
`_validate(picking)` confirms it, sets the move's quantity and `picked`, and calls `button_validate`.

| Test | Asserts |
|---|---|
| `test_owner_on_validation` | a receipt of the flagged type from the contact, validated: `owner_id` the customer company; the move's `restrict_partner_id`, the move line's `owner_id` and the quant's `owner_id` the same |
| `test_owner_kept` | the same with `owner_id` another partner before validation: kept |
| `test_type_without_flag` | a receipt of the warehouse's receipt type from the contact, validated: no owner |
| `test_onchange` | a `Form` of a new transfer: choosing the flagged type and the contact shows the customer company as owner; with the receipt type, no owner |
| `test_sale_fallback` | skipped when procurement groups have no `sale_id`. A sales order for the contact; a receipt of the flagged type without partner whose moves get a procurement group with that `sale_id`, validated: `owner_id` the customer company |
| `test_no_valuation` | skipped without `stock_account`. The flagged receipt validated creates no valuation layer for its move; a receipt of the unflagged type creates one |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | An operation-type option, *Partner Owns the Goods*: its transfers assign the goods to their partner as owner, or, without a partner, to the customer of their sales order; an owner set by hand is kept. Owned stock is reserved and consumed as usual and stays out of the company's valuation |
| `readme/USAGE.md` | Enable *Consignment* (*Inventory → Settings*); tick *Partner Owns the Goods* on the operation type (for example customer material received for processing); the owner shows on the transfer when the partner is chosen and is set at validation in any case |
