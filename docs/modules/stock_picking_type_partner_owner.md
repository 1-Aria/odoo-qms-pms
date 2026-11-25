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
| 1 | The operation-type flag; the owner set in the form and at validation, with the sales-order fallback | done | 2026-11-17: `-i`, `exit=0`, 6 post-tests, 0 failures. UI checked: *Partner Owns the Goods* on *Resupply From Customer*; WH/SBC/00027, without partner, validated with owner *chị út nhí* from S00071, no valuation entry; a new receipt's owner set on choosing the customer |
| 2 | A fixed *Goods Owner* on the operation type, for any type: its transfers get that owner at creation and at validation; read by `mrp_production_partner_owner` for manufacturing types | done | 2026-11-24: `-u`, 8 post-tests passed (Peter's run). UI check pending |
| 3 | *Partner Owns the Goods* also on outgoing types (a customer's leftover material returned); the partner's owner set when the transfer is created | done | 2026-11-25: `-u`, 9 post-tests passed (Peter's run, with the 15 of `mrp_production_partner_owner`, which the upgrade also ran) |
| 4 | The *Owner* column on a transfer's line details, read-only when the lines are picked from stock | done | 2026-11-25: `-u`, 10 post-tests passed (Peter's run); the column shows on the test database |

## Divergences from the design

None.

## Decisions

| # | Decision |
|---|---|
| D1 | **The owner is the commercial partner** (`commercial_partner_id`): quants of one customer are not split between the company and its contacts |
| D2 | **At validation an owner already on the transfer is never replaced;** only an empty one is filled, so a different owner can be set by hand |
| D3 | **Validation is the hook that matters:** `stock.picking._action_done` is overridden to fill the owner before `super()`, which copies it to the moves' `restrict_partner_id` and the move lines' `owner_id` (`stock/models/stock_picking.py:1256-1260`). Every transfer passes there, including those created by procurement |
| D4 | **The form shows the owner earlier** through an onchange on the partner and the operation type: for a flagged type with a partner, the owner becomes the partner's commercial partner, also when it already held one, so correcting a wrongly chosen partner corrects the owner. An owner set by hand after the partner stays until the partner changes again |
| D5 | **Without a partner, the customer of the sales order behind the moves' procurement group** (`group_id.sale_id.partner_id`, read as superuser, only when `sale_stock` adds `sale_id` to groups, `sale_stock/models/stock.py:84`). A *Resupply From Customer* receipt is created by a manufacturing order and has no partner (WH/SBC/00027: group WH/MO/01716, sales order S00071). No dependency on `sale_stock` |
| D6 | **Nothing else changes** (step 1). Reservation already takes quants of any owner when a move names none (`stock/models/stock_move.py:1957`, `strict=False`), so manufacturing consumes the customer's material; moves and lines with an owner other than the company are left out of valuation by `stock_account` (`stock_account/models/stock_move_line.py:121-128`, `stock_move.py:700`). Material of one customer can be reserved for another's order, as for any owned stock; OCA `stock_owner_restriction` would restrict it and is not used |
| D7 | **A fixed owner for any operation type** (step 2): `owner_partner_id`, *Goods Owner*. A transfer of that type gets it as `owner_id` when it is created without one, and at validation when it still has none. The first uses are a delivery type for goods another partner owns, whose partner is the buyer and not the owner, and manufacturing types (`mrp_production_partner_owner`) |
| D8 | **The fixed owner comes before the partner.** On a type with both, *Goods Owner* is applied first; *Partner Owns the Goods* fills only a transfer still without owner |
| D9 | **At creation, so that reservation sees it.** OCA `stock_owner_restriction`'s *Picking partner* restriction reserves the transfer's `owner_id`, else its partner (`stock_owner_restriction/models/stock_move.py:38-46`). The owner must be on the transfer before *Check Availability*, so `create` sets it, not only `_action_done`. Without that module the owner applies at validation only, as in step 1 |
| D10 | **An owner set by hand is kept,** at creation and at validation (as D2) |
| D11 | **Outgoing types too** (step 3): returning a customer's leftover material is a delivery of the customer's goods. With *Picking partner* (OCA `stock_owner_restriction`) the transfer reserves its `owner_id`, else its partner (`stock_owner_restriction/models/stock_move.py:38-46`). The partner is often a contact while the goods belong to the commercial partner (D1), so the owner must be on the transfer before *Check Availability* |
| D13 | **The owner shows on every line** (step 4). Core hides *Owner* in the line details whenever the lines are picked from stock (`stock/views/stock_move_views.xml:211`), and *Pick From* is a field that is neither stored nor computed (`stock/models/stock_move_line.py:88`), filled only while a line is edited (`:304-337`): on saved lines the owner is not visible. The column shows for *Consignment* users, read-only where core hid it (reservation chooses the owner), editable as before on receipts. Found in Peter's UI check, 2026-11-25 |
| D12 | **At creation, for a flagged type with a partner** (step 3): `owner_id` = the partner's commercial partner, after the fixed *Goods Owner* (D8). Receipts get it earlier than in step 1, with the same result |

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
| `version` | `18.0.1.3.0` (step 4) |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Inventory/Inventory` |
| `depends` | `stock` |
| `data` | `views/stock_picking_type_views.xml`, `views/stock_move_line_views.xml` (step 4) |
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
| `owner_partner_id` | Many2one `res.partner` | step 2. `string="Goods Owner"`, `help="Transfers of this type assign the goods to this partner as owner. An owner set by hand is kept."` |

### `stock.picking` — `models/stock_picking.py`

`_inherit = "stock.picking"`

| Method | Decorator | Behaviour |
|---|---|---|
| `_get_partner_owner` | — | `ensure_one`. `partner_id.commercial_partner_id`; else, when procurement groups have `sale_id`, the commercial partner of `group_id.sudo().sale_id.partner_id`, browsed back in the user's environment; else an empty partner (D1, D5) |
| `create` | `@api.model_create_multi` | Step 2. For each vals without `owner_id` whose operation type (`picking_type_id` in vals) has `owner_partner_id`: `owner_id` = it (D7, D9, D10). Step 3: else, when the type has `owner_from_partner` and the vals a `partner_id`: `owner_id` = that partner's commercial partner (D12). Then `super()` |
| `_onchange_owner_from_partner` | `@api.onchange("partner_id", "picking_type_id")` | When the type has `owner_partner_id` (step 2): `owner_id` = it (D8). Else, when the type has `owner_from_partner` and the transfer a partner: `owner_id` = `partner_id.commercial_partner_id` (D4) |
| `_action_done` | — | For each transfer whose `owner_id` is empty: the type's `owner_partner_id` when set (step 2, D8); else, when the type has `owner_from_partner`, `_get_partner_owner()` when found. Then `super()` (D2, D3) |

## Views — `views/stock_picking_type_views.xml`

One record, `view_picking_type_form`, inheriting `stock.view_picking_type_form`.

| Position | Content |
|---|---|
| `//field[@name='create_backorder']` after | `owner_from_partner`, `invisible="code not in ('incoming', 'internal')"`; step 3: `invisible="code not in ('incoming', 'internal', 'outgoing')"` |
| `//field[@name='create_backorder']` after (step 2) | `owner_partner_id` |

### `views/stock_move_line_views.xml` (step 4)

| Record | Inherits | Content |
|---|---|---|
| `view_stock_move_line_operation_tree` | `stock.view_stock_move_line_operation_tree` | `owner_id`: `column_invisible="False"`, `readonly="parent.show_quant or (package_level_id and parent.picking_type_entire_packs)"` (D13) |

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
| `test_onchange` | a new transfer (`stock.picking.new`) of the flagged type and the contact, `_onchange_owner_from_partner` called: owner the customer company; the partner changed to another and the onchange called again: owner that partner; of the receipt type: no owner. Called directly, not through `Form`, because the form shows `owner_id` only to *Consignment* users |
| `test_sale_fallback` | skipped when procurement groups have no `sale_id`. A sales order for the contact; a receipt of the flagged type without partner whose moves get a procurement group with that `sale_id`, validated: `owner_id` the customer company |
| `test_fixed_owner_on_create` | step 2. An outgoing type with `owner_partner_id` *Owner*: a delivery to the contact created without owner has `owner_id` *Owner*; created with another owner, that one is kept; validated, the move line's owner is *Owner* |
| `test_fixed_owner_before_partner` | step 2. A type with both `owner_from_partner` and `owner_partner_id` *Owner*: a receipt from the contact, validated: owner *Owner* |
| `test_outgoing_owner_from_partner` | step 3. An outgoing type with `owner_from_partner`: a delivery to the contact, created: `owner_id` the customer company; with 5 units owned by the customer company in stock, validated: the move line's owner the customer company |
| `test_owner_column_on_line_details` | step 4. The user in *Consignment*; `get_view` of `stock.view_stock_move_line_operation_tree`: one `owner_id` node, `column_invisible` "False", `readonly` naming `parent.show_quant` |
| `test_no_valuation` | skipped without `stock_account`. The flagged receipt validated creates no valuation layer for its move; a receipt of the unflagged type creates one |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | An operation-type option, *Partner Owns the Goods*: its transfers assign the goods to their partner as owner, or, without a partner, to the customer of their sales order; an owner set by hand is kept. Owned stock is reserved and consumed as usual and stays out of the company's valuation |
| `readme/USAGE.md` | Enable *Consignment* (*Inventory → Settings*); tick *Partner Owns the Goods* on the operation type (for example customer material received for processing); the owner shows on the transfer when the partner is chosen and is set at validation in any case |
