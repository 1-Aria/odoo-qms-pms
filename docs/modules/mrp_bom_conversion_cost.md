# mrp_bom_conversion_cost

A standard conversion cost for manufactured goods, from audited inputs:
- each normal BoM holds its standard conversion minutes per unit, and its chatter tracks each change;
- each company holds dated conversion cost rates, which accounting managers approve and which are locked
  once approved.

When a manufacturing order is done, its *Extra Unit Cost* (`extra_cost`, from `mrp_account`) is set to
the BoM's minutes × the rate in force on the valuation date. The MO keeps the rate and the minutes it used.
Core adds the amount to the finished goods' value.

`ie_valuation` later reads the same rates and takes the minutes from IE's standards for the products it
covers. This module's minutes remain the source for the rest. Design: `docs/IE-MES/IE_Technical_Design_v0.4.md`
TD-52, building on `IE_Fit_Gap_v0.3.md` §9 (FG-06, FG-07).

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Fields, the MO compute, views, Settings, tests | done | 2026-11-04: `-i` with tests: `exit=0`, 10 tests, 0 failures. Existing MOs not recomputed (129 IE-PROTO MOs at 15,017.21 and 38 subcontract MOs at 16,000 unchanged). UI checked by Peter: Settings rate, BoM minutes, MO figure. Work centres' `costs_hour` set to 0 by Peter |
| 2 | Dated, approved rates (`mrp.conversion.cost.rate`) replacing the Settings rate; the figure set at MO done with the rate and minutes kept on the MO; tests rewritten | done | 2026-11-06: `-u` with tests: `exit=0`, 14 tests, 0 failures. `res_company.conversion_cost_rate` column dropped; existing MO figures unchanged. UI checked by Peter: rate approval and lock, estimate, figure, rate and minutes at done |

## Divergences from the design

None.

## Decisions

| # | Decision |
|---|---|
| D1 | **Standard minutes, never logged time.** The BoM's minutes are the style's standard minutes, such as its garment SAM, entered by hand. Work-order time never feeds the figure. Line work centres keep `costs_hour = 0` (FG-06, rule R2). |
| D2 | **The figure is set when the MO is done** (step 2; in step 1 it was copied at creation).<br>• It uses the rate in force on the valuation date, the date stock entries are posted on: `force_period_date` from the context, else today (`odoo/addons/stock_account/models/stock_move.py:675-680`).<br>• The MO stores the rate record and the BoM's minutes it used, and `extra_cost` = minutes × rate.<br>• Before done, the MO shows an estimate at the rate in force today. Nothing is stored. |
| D3 | **The hook is `_cal_price`.** Core calls it for each MO inside `_post_inventory`, before the finished move is valued (`odoo/addons/mrp/models/mrp_production.py:1836-1844`). `mrp_account`'s override then reads `extra_cost` (`odoo/addons/mrp_account/models/mrp_production.py:40-65`). `mrp_subcontracting_account` sets its subcontractor price on the same hook (`odoo/addons/mrp_subcontracting_account/models/mrp_production.py:10-16`).<br>• Step 1's redefinition of `extra_cost` as a stored compute is removed: `extra_cost` is core's plain field again, and the stored values stay.<br>• `extra_cost` can no longer be edited on the MO form. |
| D4 | **Which MOs are covered.** Only MOs whose BoM is of type `normal` with minutes > 0.<br>• Every other MO is left as it is: its `extra_cost` is neither written nor reset. This covers subcontract MOs (core sets their price), BoMs without minutes, and the instance's IE-PROTO MOs.<br>• The type is compared as text, so the module does not depend on `mrp_subcontracting`. |
| D5 | **The rate is a `Float` with the *Product Price* precision, not a `Monetary`.** A `Monetary` rounds to its currency (`odoo/odoo/fields.py:1768`, `1784`), and VND's rounding is 1. The figure is not rounded either: valuation rounds the total. |
| D6 | **The rate table** `mrp.conversion.cost.rate`. Each row holds a company, a start date, the rate per minute and the basis, with a chatter for tracking and attachments.<br>• A rate is *Draft* or *Approved*. Only approved rates apply.<br>• The rate in force on a date is the approved rate of the MO's company with the latest start date on or before that date.<br>• One rate per company and start date.<br>• It replaces step 1's Settings field. On upgrade Odoo removes the field and drops its `res.company` column (`odoo/odoo/addons/base/models/ir_model.py:880-895`, `1023`). Nothing is migrated: the step 1 rate was test data. |
| D7 | **Approved rates are locked.**<br>• Company, start date, rate and approval fields cannot be written, and the record cannot be deleted. The basis note stays editable, and its changes are tracked.<br>• A correction is a new rate with a later start date. |
| D8 | **No back-dating.** A rate cannot be approved with a start date before today. Done MOs cannot be revalued, because their cost is already blended into average cost. A rate may be approved ahead of its start date. |
| D9 | **Roles.**<br>• *Accounting / Administrator* (`account.group_account_manager`) creates, edits, approves and deletes draft rates.<br>• *Manufacturing / User* and *Accounting / Read-only* (`account.group_account_readonly`) read them.<br>• A company record rule limits rates to the user's companies.<br>• The lookup at MO done reads as superuser, so marking an MO done needs no rights on rates.<br>• Menus: *Manufacturing → Configuration* (Manufacturing administrators) and *Accounting → Configuration* (Accounting administrators). |
| D10 | **No approved rate on the valuation date blocks marking the MO done,** with a message naming the MO, the company and the date. This applies only to covered MOs (D4). Once a company has its first approved rate, a rate stays in force until a newer one, so the block can only happen before finance enters the first rate. |
| D11 | **The minutes are not locked** (Peter, 2026-11-06).<br>• They can be edited on a BoM in any state, and the BoM's chatter tracks each change.<br>• The record of audit is the MO's copy of the minutes it was valued with (D2).<br>• Locking them like `mrp_bom_version` locks the components outside draft (`oca/manufacture/mrp_bom_version/views/mrp_bom_view.xml:116-136`) is dropped for now. Each of the instance's 72 active BoMs would need a new version for its first minutes. |
| D12 | **Visibility on the MO** is for *Manufacturing / Administrator*: the estimate before done; then the figure, the rate and the minutes. |
| D13 | **Generic naming.** The module is named in OCA's `<base_module>_<feature>` form and its names are unprefixed: nothing in it is specific to garments or IE. |
| D14 | **Accounting, not module behaviour:**<br>• At MO done, the finished goods' value includes the absorbed amount.<br>• The production account (1541 on all finished-goods and raw-material categories) keeps it as a credit.<br>• Finance clears that monthly against actual labour and overhead (6220, 627x) and posts the remaining variance to 6320.<br>• The accountant confirms this treatment and the rate's basis. |
| D15 | **Hand-over to `ie_valuation`** (TD-52, settled in chunk 4):<br>• `ie_valuation` depends on this module and reads the same rates.<br>• From a start date on the first day of a month, for products with an IE standard, it supplies the minutes (garment SAM) in place of the BoM's. The rate, the hook and the MO's audit fields stay. |

## Folder structure

```
mrp_bom_conversion_cost/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── mrp_bom.py
│   ├── mrp_conversion_cost_rate.py
│   └── mrp_production.py
├── security/
│   ├── ir.model.access.csv
│   └── mrp_conversion_cost_rate_security.xml
├── views/
│   ├── mrp_bom_views.xml
│   ├── mrp_conversion_cost_rate_views.xml
│   └── mrp_production_views.xml
├── tests/
│   ├── __init__.py
│   └── test_conversion_cost.py
└── readme/
    ├── DESCRIPTION.md
    └── USAGE.md
```

Removed in step 2: `models/res_company.py`, `models/res_config_settings.py`, `views/res_config_settings_views.xml`.

## Manifest

| Key | Value |
|---|---|
| `name` | `BoM Conversion Cost` |
| `summary` | `Value manufactured goods with a standard conversion cost: BoM minutes × an approved, dated rate per minute` |
| `version` | `18.0.1.1.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Manufacturing/Manufacturing` |
| `depends` | `mrp_account` |
| `data` | `security/ir.model.access.csv`, `security/mrp_conversion_cost_rate_security.xml`, `views/mrp_conversion_cost_rate_views.xml`, `views/mrp_bom_views.xml`, `views/mrp_production_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import mrp_bom, mrp_conversion_cost_rate, mrp_production` |
| `tests/__init__.py` | `from . import test_conversion_cost` |

## Access

`security/ir.model.access.csv`:

| id | name | model | group | r | w | c | d |
|---|---|---|---|---|---|---|---|
| `access_mrp_conversion_cost_rate_mrp_user` | `mrp.conversion.cost.rate mrp user` | `model_mrp_conversion_cost_rate` | `mrp.group_mrp_user` | 1 | 0 | 0 | 0 |
| `access_mrp_conversion_cost_rate_account_readonly` | `mrp.conversion.cost.rate account readonly` | `model_mrp_conversion_cost_rate` | `account.group_account_readonly` | 1 | 0 | 0 | 0 |
| `access_mrp_conversion_cost_rate_account_manager` | `mrp.conversion.cost.rate account manager` | `model_mrp_conversion_cost_rate` | `account.group_account_manager` | 1 | 1 | 1 | 1 |

`security/mrp_conversion_cost_rate_security.xml`: global record rule `mrp_conversion_cost_rate_company_rule` on `model_mrp_conversion_cost_rate`, `domain_force` `[('company_id', 'in', company_ids)]`.

## Models

### `mrp.conversion.cost.rate` — `models/mrp_conversion_cost_rate.py`

`_name = "mrp.conversion.cost.rate"`, `_description = "Conversion Cost Rate"`, `_inherit = ["mail.thread"]`,
`_order = "company_id, date_from desc, id desc"`

| Field | Type | Attributes |
|---|---|---|
| `company_id` | Many2one `res.company` | required; default `self.env.company`; `index=True`; `tracking=True` |
| `currency_id` | Many2one `res.currency` | `related="company_id.currency_id"`; shown beside the rate |
| `date_from` | Date | string *Valid From*; required; `tracking=True` |
| `rate` | Float | string *Rate per Minute*; `digits="Product Price"`; required; `tracking=True`; help *Cost of one standard minute of conversion work (labour and overhead), in the company's currency.* |
| `note` | Text | string *Basis*; `tracking=True`; help *How the rate was set, e.g. the period's conversion cost and the minutes it is spread over.* |
| `state` | Selection | `[("draft", "Draft"), ("approved", "Approved")]`; default `"draft"`; required; `readonly=True`; `copy=False`; `tracking=True` |
| `approved_by_id` | Many2one `res.users` | string *Approved By*; `readonly=True`; `copy=False` |
| `approved_date` | Datetime | string *Approved On*; `readonly=True`; `copy=False` |
| `production_count` | Integer | non-stored compute `_compute_production_count`: the number of `mrp.production` with `conversion_rate_id` = the record |

SQL constraints:
- `rate_positive`: `CHECK (rate > 0)`, message *The rate per minute must be positive.*
- `company_date_unique`: `UNIQUE (company_id, date_from)`, message *A company can have only one conversion cost rate per start date.*

**`_compute_display_name()`** — `@api.depends("date_from", "rate")`: `"<date_from formatted with odoo.tools.format_date> · <rate formatted with odoo.tools.formatLang, Product Price digits>"`.

**`write(vals)`**: if `vals` holds any of `company_id`, `date_from`, `rate`, `state`, `approved_by_id`, `approved_date`, and any record in `self` is `approved` → `UserError` *An approved conversion cost rate cannot be changed. Approve a new rate with a later start date instead.* Otherwise `super()`.

**`_unlink_except_approved()`** — `@api.ondelete(at_uninstall=False)`: any record `approved` → `UserError` *An approved conversion cost rate cannot be deleted.*

**`action_approve()`**:
1. Any record not `draft` → `UserError` *Only draft rates can be approved.*
2. `today = fields.Date.context_today(self)`. Any `date_from < today` → `UserError` *A conversion cost rate cannot start before today (%(today)s): manufacturing orders already done keep the rate they were valued at.*
3. `self.write({"state": "approved", "approved_by_id": self.env.uid, "approved_date": fields.Datetime.now()})`. The records are still drafts when this runs, so `write` allows it.

**`action_view_productions()`**: an `ir.actions.act_window` on `mrp.production` with domain `[("conversion_rate_id", "in", self.ids)]`, list and form views, name *Valued Manufacturing Orders*.

**`_rate_on(company, date)`** — `@api.model`: `self.sudo().search([("company_id", "=", company.id), ("state", "=", "approved"), ("date_from", "<=", date)], order="date_from desc", limit=1)`. Returns that record, or an empty recordset. Callers only read `rate` and assign its id.

### `mrp.bom` — `models/mrp_bom.py`

`_inherit = "mrp.bom"`

| Field | Type | Attributes |
|---|---|---|
| `conversion_minutes` | Float | string *Conversion Minutes*; `digits=(16, 4)`; default `0.0`; `tracking=True`; help *Standard minutes of conversion work per unit of the product, in the product's unit of measure (for a garment, its SAM). Manufacturing orders are valued at these minutes × the conversion cost rate in force on the day they are done.* |

SQL constraint `conversion_minutes_not_negative`: `CHECK (conversion_minutes >= 0)`, message *Conversion minutes cannot be negative.*

The field keeps the default `copy=True`, so a new `mrp_bom_version` version (`oca/manufacture/mrp_bom_version/models/mrp_bom.py:103`) starts from the previous version's minutes.

### `mrp.production` — `models/mrp_production.py`

`_inherit = "mrp.production"`. Core's `extra_cost` is no longer redefined (D3).

| Field | Type | Attributes |
|---|---|---|
| `conversion_rate_id` | Many2one `mrp.conversion.cost.rate` | string *Conversion Cost Rate*; `readonly=True`; `copy=False`; `ondelete="restrict"`; `index="btree_not_null"` |
| `conversion_minutes` | Float | string *Conversion Minutes*; `digits=(16, 4)`; `readonly=True`; `copy=False`; help *The BoM's conversion minutes when the order was valued.* |
| `conversion_cost_estimate` | Float | string *Estimated Extra Unit Cost*; `digits="Product Price"`; non-stored compute `_compute_conversion_cost_estimate` |

**`_conversion_cost_bom()`**: `ensure_one()`. Returns `self.bom_id` if its `type == "normal"` and `conversion_minutes > 0`, else an empty `mrp.bom`.

**`_compute_conversion_cost_estimate()`** — `@api.depends("bom_id", "bom_id.type", "bom_id.conversion_minutes", "company_id")`. For each production, with `bom = production._conversion_cost_bom()`:
- no `bom` → `0.0`;
- else `rate = env["mrp.conversion.cost.rate"]._rate_on(production.company_id, fields.Date.context_today(production))`, and the estimate is `bom.conversion_minutes * rate.rate`, or `0.0` when there is no rate.

**`_cal_price(consumed_moves)`**: with `bom = self._conversion_cost_bom()`:
1. `bom` empty → `super()` only.
2. `date = self.env.context.get("force_period_date") or fields.Date.context_today(self)`; `rate = env["mrp.conversion.cost.rate"]._rate_on(self.company_id, date)`.
3. No `rate` → `UserError` *%(mo)s cannot be valued: no approved conversion cost rate for %(company)s is in force on %(date)s. An accounting administrator approves one under Configuration → Conversion Cost Rates.*
4. `self.write({"conversion_rate_id": rate.id, "conversion_minutes": bom.conversion_minutes, "extra_cost": bom.conversion_minutes * rate.rate})`, then `return super()._cal_price(consumed_moves)`.

All messages are translatable (`self.env._(...)`).

## Views

### `views/mrp_conversion_cost_rate_views.xml`

| Record id | Type | Content |
|---|---|---|
| `mrp_conversion_cost_rate_view_list` | list | `company_id` (`groups="base.group_multi_company"`), `date_from`, `rate`, `currency_id` (`optional="hide"`), `state` (`widget="badge"`, `decoration-success="state == 'approved'"`, `decoration-info="state == 'draft'"`), `approved_by_id` (`optional="show"`) |
| `mrp_conversion_cost_rate_view_form` | form | **header:** button `action_approve`, string *Approve*, `type="object"`, `class="btn-primary"`, `groups="account.group_account_manager"`, `invisible="state != 'draft'"`; `state` with `widget="statusbar"`. **sheet:** `div name="button_box"` with a stat button `action_view_productions`, icon `fa-cogs`, showing `production_count` as *Valued MOs*; a group with `company_id` (`groups="base.group_multi_company"`), `date_from`, `rate` (followed by `currency_id`, `nolabel`), and `readonly="state != 'draft'"` on these three; `approved_by_id` and `approved_date`, `invisible="state == 'draft'"`; `note` (`placeholder` *How the rate was set*). Then `<chatter/>` |
| `mrp_conversion_cost_rate_view_search` | search | `date_from`, `company_id`; filters `draft` (*Draft*, `[("state", "=", "draft")]`) and `approved` (*Approved*, `[("state", "=", "approved")]`); group by `company_id` |
| `action_mrp_conversion_cost_rate` | `ir.actions.act_window` | name *Conversion Cost Rates*, `res_model` `mrp.conversion.cost.rate`, `view_mode` `list,form` |
| `menu_mrp_conversion_cost_rate` | menuitem | parent `mrp.menu_mrp_configuration`, action above, `groups="mrp.group_mrp_manager"`, sequence 60 |
| `menu_account_conversion_cost_rate` | menuitem | parent `account.menu_finance_configuration`, action above, `groups="account.group_account_manager"`, sequence 60 |

### `views/mrp_bom_views.xml`

| Record id | Inherits | Change |
|---|---|---|
| `mrp_bom_form_view_conversion_cost` | `mrp.mrp_bom_form_view` | unchanged from step 1: after `//field[@name='code']`, `<field name="conversion_minutes" invisible="type != 'normal'"/>` |
| `mrp_bom_tree_view_conversion_cost` | `mrp.mrp_bom_tree_view` | unchanged from step 1: after `//field[@name='code']`, `<field name="conversion_minutes" optional="hide"/>` |

### `views/mrp_production_views.xml`

| Record id | Inherits | Change |
|---|---|---|
| `mrp_production_form_view_conversion_cost` | `mrp.mrp_production_form_view` | after `//field[@name='user_id']`, each field with `groups="mrp.group_mrp_manager"`:<br>• `<field name="conversion_cost_estimate" invisible="state in ('done', 'cancel') or not conversion_cost_estimate"/>`<br>• `<field name="extra_cost" readonly="1" invisible="state != 'done'"/>`<br>• `<field name="conversion_rate_id" invisible="not conversion_rate_id"/>`<br>• `<field name="conversion_minutes" invisible="not conversion_rate_id"/>` |

## Tests

`TestConversionCost(TransactionCase)` in `tests/test_conversion_cost.py`, tagged `@tagged("post_install", "-at_install")`, because the fixtures create a company, products, a partner and users.

**Fixtures** (`setUpClass`):
- `company`: a new `res.company`, *Conversion Cost Test Co*, in VND. It keeps the tests apart from rates entered on the instance. `cls.env` becomes `cls.env(context=dict(cls.env.context, allowed_company_ids=[company.id, *cls.env.companies.ids]))`, as in `l10n_vn_payroll`'s tests, and `warehouse` = that company's warehouse.
- `today = fields.Date.context_today(...)`.
- `rate_1`: a rate for `company` from `today`, 1,500 per minute, approved.
- `categ`: a `product.category` with `property_cost_method="average"` and `property_valuation="manual_periodic"`, so valuation layers are made without journal entries.
- `component`: storable, in `categ`, `standard_price` 10,000.
- `garment` and `garment_b`: storable finished products in `categ`.
- `bom`: normal, for `garment`, `product_qty` 1, one line of 2 × `component`, 12.5 conversion minutes.
- `bom_b`: normal, for `garment_b`, with the same line and no minutes.
- Every BoM is created with `active=True`: outside test runs `mrp_bom_version` creates BoMs archived (`oca/manufacture/mrp_bom_version/models/mrp_bom.py:22-27`).
- Users with `company` as their only company, in these groups:
  - `mrp_user` (login `test.conversion.mrp.user`): `mrp.group_mrp_user`;
  - `mrp_manager` (`test.conversion.mrp.manager`): `mrp.group_mrp_manager`;
  - `account_manager` (`test.conversion.account.manager`): `account.group_account_manager`.

**Helpers:**
- `_rate(date_from, rate, approve=True)` creates a rate for `company` and approves it.
- `_mo(product, qty=1, **vals)` creates an `mrp.production` with source and destination at `warehouse.lot_stock_id`.
- `_done(mo, **ctx)` confirms the MO, sets `qty_producing` = `product_qty` through `Form`, marks the raw moves `picked`, and calls `button_mark_done()` with `ctx` added to the context.
- `_as(user)` = `self.env(user=user, context=dict(self.env.context, allowed_company_ids=[company.id]))`.
- `_finished_value(mo)` = the sum of the finished move's valuation layer values.

| Test | Asserts |
|---|---|
| `test_rate_on_latest_before_date` | with `rate_2 = _rate(today + 10, 2000)`, `_rate_on(company, d)` returns `rate_1` for `today` and `today + 9`, `rate_2` for `today + 10`, and nothing for `today - 1` |
| `test_approved_rate_locked` | on `rate_1`, writing `rate`, then `date_from`, raises `UserError`, and `unlink()` raises `UserError`; writing `note` works (positive control). A draft rate can be written and deleted |
| `test_no_backdated_approval` | `_rate(today - 1, 1000, approve=False).action_approve()` raises `UserError`; the rate stays draft |
| `test_rate_constraints` | a rate of 0, then a second rate for `company` from `today`, each raise `IntegrityError` on flush (in `mute_logger("odoo.sql_db")` and a savepoint) |
| `test_estimate_before_done` | a draft `_mo(garment)`: `conversion_cost_estimate` = 18,750 (12.5 × 1,500); `extra_cost` = 0; no `conversion_rate_id` |
| `test_valuation_at_done` | `_done(_mo(garment, qty=2))`: `state` = `done`; `extra_cost` = 18,750; `conversion_rate_id` = `rate_1`; `conversion_minutes` = 12.5; `_finished_value` = 2 × 2 × 10,000 + 2 × 18,750 = 77,500 |
| `test_valuation_date_decides_rate` | with `rate_2 = _rate(today + 10, 2000)`, an MO created now and done with `force_period_date=today + 10`: `extra_cost` = 25,000; `conversion_rate_id` = `rate_2`; `_finished_value` for qty 2 = 90,000 |
| `test_snapshot_survives_bom_change` | after `_done(_mo(garment))`, writing `bom.conversion_minutes = 20`: the MO still holds 12.5 minutes and 18,750 |
| `test_no_rate_blocks_done` | `rate_1` set back to draft through SQL, then the field invalidated: `_done(_mo(garment))` raises `UserError`, and the MO is not `done` |
| `test_uncovered_mo_untouched` | with `rate_1` set back to draft through SQL, as in the previous test, so no rate is in force: `_done(_mo(garment_b, extra_cost=5000))` is done; `extra_cost` = 5,000; no `conversion_rate_id`; `_finished_value` for qty 1 = 25,000 |
| `test_subcontract_bom_not_covered` | skipped (`self.skipTest`) when `"subcontract"` is not a value of `mrp.bom`'s `type`. Otherwise: a `subcontract` BoM for `garment_b` with a new partner in `subcontractor_ids` and 12.5 minutes; an MO with that `bom_id` has an empty `_conversion_cost_bom()` and an estimate of 0 |
| `test_negative_minutes_refused` | `conversion_minutes = -1` on `bom` raises `IntegrityError` on flush |
| `test_access` | as `mrp_user`: reading `rate_1` works (positive control), and creating a rate raises `AccessError`. As `mrp_manager`: `action_approve()` on a draft rate raises `AccessError`. As `account_manager`: a rate from `today + 20` is created and approved (positive control), with `approved_by_id` = `account_manager` |
| `test_manager_form` | as `mrp_manager`, with `Form(env["mrp.production"])`: setting `product_id = garment` shows `conversion_cost_estimate` 18,750, and assigning `extra_cost` raises `AssertionError` (read-only in the form) |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | A standard conversion cost for manufactured products: the BoM's conversion minutes × the company's approved conversion cost rate in force on the valuation date, set as the MO's Extra Unit Cost when it is done, which core adds to the finished goods' value. The MO keeps the rate and minutes used. Rates are dated, approved by accounting administrators and locked once approved. Normal BoMs with minutes only. Other MOs, subcontracted ones included, are left as they are |
| `readme/USAGE.md` | An accounting administrator creates a rate under *Accounting → Configuration → Conversion Cost Rates* (also under *Manufacturing → Configuration*), with its start date and basis, and approves it. A correction is a new rate with a later start date. Enter *Conversion Minutes* on each normal BoM; the BoM's chatter tracks changes. An MO shows the estimate before done, then the figure, rate and minutes (for Manufacturing administrators). Marking a covered MO done is refused while the company has no approved rate in force. Keep work centres' cost per hour at 0, or that cost is counted as well |
