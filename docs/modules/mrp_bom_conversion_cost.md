# mrp_bom_conversion_cost

An interim standard conversion cost for manufactured goods. Each BoM holds its standard conversion
minutes per unit, and each company holds a conversion cost per minute. When a manufacturing order is
created, the module sets its *Extra Unit Cost* (`extra_cost`, from `mrp_account`) to minutes × rate. Core
then adds that amount to the finished goods' value when the MO is done.

It comes before `ie_valuation`, which takes over for products with an IE standard and leaves this figure
on the rest. Design: `docs/IE-MES/IE_Technical_Design_v0.4.md` TD-52, building on `IE_Fit_Gap_v0.3.md`
§9 (FG-06, FG-07).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Fields, the MO compute, views, Settings, tests | done | 2026-11-04: `-i` with tests: `exit=0`, 10 tests, 0 failures. Existing MOs not recomputed (129 IE-PROTO MOs at 15,017.21 and 38 subcontract MOs at 16,000 unchanged). UI checked by Peter: Settings rate, BoM minutes, MO figure. Work centres' `costs_hour` set to 0 by Peter |

## Divergences from the design

None.

## Decisions

| # | Decision |
|---|---|
| D1 | **Standard minutes, never logged time.** The BoM's minutes are the style's standard minutes, such as its garment SAM, entered by hand. Work-order time never feeds the figure. Line work centres keep `costs_hour = 0` (FG-06, rule R2). |
| D2 | **The figure is copied when the MO is created.** Changing a BoM's minutes or the company rate later does not change existing MOs. Changing an MO's BoM recomputes its figure. The figure can be edited on the MO until the MO is done or cancelled. |
| D3 | **Core's `extra_cost` becomes a stored compute** (`readonly=False`, `precompute=True`, depending on `bom_id`).<br>• MOs created in code (procurement, sales, imports) get the figure at `create()`.<br>• A value given in `create()` wins over the compute. This keeps the figure that splits and backorders copy (`odoo/addons/mrp_account/models/mrp_production.py:67-70`, `odoo/addons/mrp/models/mrp_production.py:1923`).<br>• Installing the module recomputes no existing MO. A stored compute is computed for existing rows only when its column is new (`odoo/odoo/models.py:3473-3476`, `odoo/odoo/fields.py:1114`), and `extra_cost`'s column already exists. |
| D4 | **Normal BoMs only.** A BoM of any other type, or one without minutes, gives 0.<br>• Kits make no MO.<br>• For a subcontract MO, `mrp_subcontracting_account` overwrites `extra_cost` with the subcontractor's price when the MO is done (`odoo/addons/mrp_subcontracting_account/models/mrp_production.py:10-16`). It also books that amount to the stock input account (`models/stock_move.py:31-45`).<br>• The type is compared as text, so the module does not depend on `mrp_subcontracting`. |
| D5 | **The rate is a `Float` with the *Product Price* precision, not a `Monetary`.** A `Monetary` rounds to its currency (`odoo/odoo/fields.py:1768`, `1784`), and VND's rounding is 1. A rate of 1,494.25 VND per minute would be stored as 1,494. The figure on the MO is not rounded either: valuation rounds the total. |
| D6 | **No rate history in this module.** Each MO keeps the figure it was given. The versioned, dated rate of fit-gap §9.5 belongs to `ie_valuation` (chunk 4). |
| D7 | **Visibility:**<br>• **MO form:** the figure shows for *Manufacturing / Administrator* (`mrp.group_mrp_manager`).<br>• **BoM form:** the minutes show to everyone who can open a BoM, and only BoM managers can write them (core's access file).<br>• **Rate:** in Settings, Manufacturing section, per company. |
| D8 | **Generic naming.** The module is named in OCA's `<base_module>_<feature>` form and its fields are unprefixed: nothing in it is specific to garments or IE. |
| D9 | **Accounting, not module behaviour:**<br>• At MO done, the finished goods' value includes the absorbed amount (`odoo/addons/mrp_account/models/mrp_production.py:40-65`).<br>• The production account (1541 on all finished-goods and raw-material categories) keeps it as a credit.<br>• Finance clears that monthly against actual labour and overhead (6220, 627x) and posts the remaining variance to 6320.<br>• The accountant confirms this treatment. |
| D10 | **Hand-over to `ie_valuation`** (TD-52, settled in chunk 4):<br>• From a start date on the first day of a month, at MO done, `ie_valuation` overwrites `extra_cost` for products that have an IE standard.<br>• This module stays installed as the fallback for the rest. |

## Folder structure

```
mrp_bom_conversion_cost/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── mrp_bom.py
│   ├── mrp_production.py
│   ├── res_company.py
│   └── res_config_settings.py
├── views/
│   ├── mrp_bom_views.xml
│   ├── mrp_production_views.xml
│   └── res_config_settings_views.xml
├── tests/
│   ├── __init__.py
│   └── test_conversion_cost.py
└── readme/
    ├── DESCRIPTION.md
    └── USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `BoM Conversion Cost` |
| `summary` | `Value manufactured goods with a standard conversion cost: BoM minutes × a company rate per minute` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Manufacturing/Manufacturing` |
| `depends` | `mrp_account` |
| `data` | `views/mrp_bom_views.xml`, `views/mrp_production_views.xml`, `views/res_config_settings_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import mrp_bom, mrp_production, res_company, res_config_settings` |
| `tests/__init__.py` | `from . import test_conversion_cost` |

## Access

No new model, no access file. Who can write each field comes from core's access rules and the view groups (D7).

## Models

### `res.company` — `models/res_company.py`

`_inherit = "res.company"`

| Field | Type | Attributes |
|---|---|---|
| `conversion_cost_rate` | Float | string *Conversion Cost per Minute*; `digits="Product Price"`; default `0.0`; help *Cost of one standard minute of conversion work (labour and overhead), in the company's currency. Copied into new manufacturing orders as their BoM's minutes × this rate.* |

SQL constraint `conversion_cost_rate_not_negative`: `CHECK (conversion_cost_rate >= 0)`, message *The conversion cost per minute cannot be negative.*

### `res.config.settings` — `models/res_config_settings.py`

`_inherit = "res.config.settings"`

| Field | Type | Attributes |
|---|---|---|
| `conversion_cost_rate` | Float | `related="company_id.conversion_cost_rate"`, `readonly=False` |

### `mrp.bom` — `models/mrp_bom.py`

`_inherit = "mrp.bom"`

| Field | Type | Attributes |
|---|---|---|
| `conversion_minutes` | Float | string *Conversion Minutes*; `digits=(16, 4)`; default `0.0`; `tracking=True`; help *Standard minutes of conversion work per unit of the product, in the product's unit of measure (for a garment, its SAM). New manufacturing orders get these minutes × the company's conversion cost per minute as their Extra Unit Cost.* |

SQL constraint `conversion_minutes_not_negative`: `CHECK (conversion_minutes >= 0)`, message *Conversion minutes cannot be negative.*

The field keeps the default `copy=True`, so a BoM copy, including a new `mrp_bom_version` version (`oca/manufacture/mrp_bom_version/models/mrp_bom.py:103`), keeps its minutes.

### `mrp.production` — `models/mrp_production.py`

`_inherit = "mrp.production"`

| Field | Type | Attributes |
|---|---|---|
| `extra_cost` | Float (core, redefined) | `compute="_compute_extra_cost"`, `store=True`, `readonly=False`, `precompute=True`. Core's `string` and `copy=False` stay. |

**`_compute_extra_cost()`** — `@api.depends("bom_id")`. For each production, with `bom = production.bom_id`:
- `bom.type == "normal"` and `bom.conversion_minutes` → `production.extra_cost = bom.conversion_minutes * production.company_id.conversion_cost_rate`;
- otherwise → `production.extra_cost = 0.0`.

Both branches assign, for every record.

## Views

### `views/mrp_bom_views.xml`

| Record id | Inherits | Change |
|---|---|---|
| `mrp_bom_form_view_conversion_cost` | `mrp.mrp_bom_form_view` | after `//field[@name='code']`: `<field name="conversion_minutes" invisible="type != 'normal'"/>` |
| `mrp_bom_tree_view_conversion_cost` | `mrp.mrp_bom_tree_view` | after `//field[@name='code']`: `<field name="conversion_minutes" optional="hide"/>` |

### `views/mrp_production_views.xml`

| Record id | Inherits | Change |
|---|---|---|
| `mrp_production_form_view_conversion_cost` | `mrp.mrp_production_form_view` | after `//field[@name='user_id']`: `<field name="extra_cost" groups="mrp.group_mrp_manager" readonly="state in ('done', 'cancel')"/>`. Core shows `extra_cost` in no form; `mrp_account` puts it only in the graph view, hidden (`odoo/addons/mrp_account/views/mrp_production_views.xml:31`). |

### `views/res_config_settings_views.xml`

| Record id | Inherits | Change |
|---|---|---|
| `res_config_settings_view_form_conversion_cost` | `mrp.res_config_settings_view_form` | inside `//app[@name='mrp']`: `<block title="Costing" name="conversion_cost_setting_container">` holding `<setting id="conversion_cost_rate" string="Conversion Cost per Minute" company_dependent="1" help="Copied into new manufacturing orders as their BoM's conversion minutes × this rate">` with `<field name="conversion_cost_rate"/>` |

## Tests

`TestConversionCost(TransactionCase)` in `tests/test_conversion_cost.py`, tagged `@tagged("post_install", "-at_install")`, because the fixtures create products, a partner and a user.

**Fixtures** (`setUpClass`):
- `company` = `env.company`, with `conversion_cost_rate` set to `1500.0`.
- `categ`: a `product.category` with `property_cost_method="average"` and `property_valuation="manual_periodic"`, so valuation layers are made without journal entries.
- `component`: storable, in `categ`, `standard_price` 10,000.
- `garment` and `garment_b`: storable finished products in `categ`.
- `bom`: normal, for `garment`, `product_qty` 1, one line of 2 × `component`, `conversion_minutes` 12.5.
- `bom_b`: normal, for `garment_b`, with the same line and no minutes.
- Every BoM is created with `active=True`: outside test runs `mrp_bom_version` creates BoMs archived (`oca/manufacture/mrp_bom_version/models/mrp_bom.py:22-27`).
- `manager`: a user (login `test.conversion.manager`) in `mrp.group_mrp_manager`, with `company` only.

**Helper:** `_mo(product, qty=1, **vals)` creates an `mrp.production` for `product` with `product_qty` = `qty` and the extra `vals`. The BoM comes from core's `bom_id` compute.

| Test | Asserts |
|---|---|
| `test_mo_gets_minutes_times_rate` | `_mo(garment).extra_cost` = 18,750 (12.5 × 1,500) |
| `test_bom_without_minutes` | `_mo(garment_b).extra_cost` = 0 |
| `test_given_value_wins` | `_mo(garment, extra_cost=5000).extra_cost` = 5,000 |
| `test_later_changes_do_not_reach_existing_mo` | after `_mo(garment)`, changing the company rate to 2,000 and `bom.conversion_minutes` to 20, the MO still holds 18,750, and a new `_mo(garment)` holds 40,000 |
| `test_bom_change_recomputes` | a draft MO for `garment` with `bom` (18,750); a second normal BoM `bom_2` for `garment` with 20 minutes; writing `bom_id = bom_2` gives 30,000 |
| `test_split_keeps_figure` | `_mo(garment, qty=4)` confirmed and split with `_split_productions({mo: [2, 2]})`: both productions hold 18,750 |
| `test_valuation_at_done` | `_mo(garment, qty=2)` with source and destination set to the company's first warehouse's stock location, confirmed; through `Form`, `qty_producing` = 2; raw moves `picked = True`; `button_mark_done()`. The MO is `done`, and the finished move's valuation layer value = 2 × 2 × 10,000 + 2 × 18,750 = 77,500 |
| `test_subcontract_bom_gives_zero` | skipped (`self.skipTest`) when `"subcontract"` is not a value of `mrp.bom`'s `type`. Otherwise: a `subcontract` BoM for `garment_b` with a new partner in `subcontractor_ids` and 12.5 minutes; an MO created with that `bom_id` holds 0 |
| `test_negative_values_refused` | writing `conversion_minutes = -1` on `bom`, then `conversion_cost_rate = -1` on `company`, each followed by a flush, raises `IntegrityError` (each in `mute_logger("odoo.sql_db")` and a savepoint) |
| `test_manager_form` | as `manager`, through `self.env(user=manager, context=dict(self.env.context, allowed_company_ids=[company.id]))` and `Form(env["mrp.production"])`: setting `product_id = garment` shows `extra_cost` 18,750. Setting it to 20,000 and saving stores 20,000 |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | A standard conversion cost for manufactured products: conversion minutes on the BoM × a company rate per minute, copied into each new MO's Extra Unit Cost, which core adds to the finished goods' value. Normal BoMs only, since subcontract MOs carry the subcontractor's price. The figure is copied when the MO is created and can be edited until the MO is done. |
| `readme/USAGE.md` | Set the rate in *Manufacturing → Configuration → Settings → Costing*. Enter *Conversion Minutes* on each normal BoM. A new MO shows the figure as *Extra Unit Cost* (for Manufacturing administrators), and it can be adjusted until the MO is done. Keep work centres' cost per hour at 0, or that cost is counted as well. |
