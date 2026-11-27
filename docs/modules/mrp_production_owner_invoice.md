# mrp_production_owner_invoice

A wizard that proposes the periodic invoice of contract processing: for one owner and one period, an ordinary draft
customer invoice with a processing-fee line per product style (quantities produced for the owner × the fee from a
pricelist) and one line for the company's material consumed by those orders, at cost; journal items marked as late
attributions are listed for the accountant to add. It writes nothing but the draft invoice, so uninstalling it
leaves only ordinary records. Generic, in OCA's `<base_module>_<feature>` form, with unprefixed field names.
Design: `docs/Accounting/Processing Invoice and Own Subcontracting — Design.md` §2.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Settings (fee product, material product, fee pricelist); the wizard with its fee lines, material value, late-attribution suggestions and duplicate warning; the draft invoice | done | 2026-11-27: `-i`, 7 post-tests passed (Peter's run). UI check: the first *Create Draft Invoice* failed (lines sent without their read-only style); fixed with `force_save`, then a draft invoice for the trading company was created |

## Divergences from the design

None.

## Decisions

| # | Decision |
|---|---|
| D1 | **Orders counted** are those with `owner_id` = the wizard's owner and `production_owned` (contract processing), of the wizard's company, subcontracted orders included. Order processing (`production_owned` False) is invoiced on its sales orders |
| D2 | **Quantities:** done finished moves of those orders whose product is the order's product (by-products left out), with `date` in the period, the period's days read in the user's time zone; summed per product template in the product's unit |
| D3 | **The fee:** the pricelist's rule for the template, `pricelist._get_product_rule(template, quantity)` (`product/models/product_pricelist.py:142-159`), and its price, `pricelist._get_product_price(template, quantity)`. Without a rule the line gets price 0 and the style is listed in the warning: a pricelist without a rule falls back to the sales price, which for finished goods is the selling price, not a fee |
| D4 | **Our material:** minus the sum of `value` of the valuation layers of those orders' component moves created in the period, read as superuser (layers are readable by stock managers only, `stock_account/security/ir.model.access.csv:8`), rounded to the company currency. At cost (Peter, 2026-11-27) |
| D5 | **Late attributions are suggested, not added:** posted journal items of the company in the period on the late-attribution account (default: the material product's expense account) whose label contains the marker text (default "đã dùng cho đơn"), shown in the wizard with their amounts |
| D6 | **The duplicate check warns, never blocks:** a customer invoice of the owner's commercial partner, not cancelled, whose `invoice_origin` equals the wizard's origin text ("Gia công <owner> MM/YYYY", from `date_to`) |
| D7 | **The draft is ordinary:** `out_invoice`, partner the owner, `invoice_date` = `date_to`, `invoice_origin` the origin text, the company's first sales journal; one line per style (fee product, `name` "Phí gia công <style> – MM/YYYY", quantity, price), then, when the value is above zero, the material line (material product, `name` "Vật tư cung cấp cho gia công – MM/YYYY", quantity 1, price the value). Taxes and accounts come from the products. The wizard then opens the draft |
| D8 | **Settings are defaults only:** three company fields, shown in *Settings → Manufacturing*, proposed by the wizard and editable there |

## Folder structure

```
mrp_production_owner_invoice/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_company.py
│   └── res_config_settings.py
├── wizards/
│   ├── __init__.py
│   └── owner_invoice_wizard.py
├── views/
│   ├── res_config_settings_views.xml
│   └── owner_invoice_wizard_views.xml
├── security/
│   └── ir.model.access.csv
├── tests/
│   ├── __init__.py
│   └── test_owner_invoice.py
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `MRP Production Owner Invoice` |
| `summary` | `Propose the periodic invoice of processing done for an owner` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Manufacturing/Manufacturing` |
| `depends` | `mrp_production_partner_owner`, `account` |
| `data` | `security/ir.model.access.csv`, `views/res_config_settings_views.xml`, `views/owner_invoice_wizard_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models`, `from . import wizards` |
| `models/__init__.py` | `from . import res_company`, `from . import res_config_settings` |
| `wizards/__init__.py` | `from . import owner_invoice_wizard` |
| `tests/__init__.py` | `from . import test_owner_invoice` |

## Access

`security/ir.model.access.csv`:

| id | model | group | r w c u |
|---|---|---|---|
| `access_owner_invoice_wizard` | `model_mrp_production_owner_invoice_wizard` | `account.group_account_invoice` | 1 1 1 1 |
| `access_owner_invoice_wizard_line` | `model_mrp_production_owner_invoice_wizard_line` | `account.group_account_invoice` | 1 1 1 1 |

## Models

### `res.company` — `models/res_company.py`

`_inherit = "res.company"`

| Field | Type | Attributes |
|---|---|---|
| `owner_invoice_fee_product_id` | Many2one `product.product` | `string="Processing Fee Product"`, domain `[('type', '=', 'service')]` |
| `owner_invoice_material_product_id` | Many2one `product.product` | `string="Supplied Material Product"`, domain `[('type', '=', 'service')]` |
| `owner_invoice_pricelist_id` | Many2one `product.pricelist` | `string="Processing Fee Pricelist"` |

### `res.config.settings` — `models/res_config_settings.py`

`_inherit = "res.config.settings"`: the three fields as `related="company_id.<field>"`, `readonly=False`.

### `mrp.production.owner.invoice.wizard` — `wizards/owner_invoice_wizard.py`

`_name = "mrp.production.owner.invoice.wizard"`, `_description = "Processing Invoice for an Owner"`,
TransientModel.

| Field | Type | Attributes |
|---|---|---|
| `company_id` | Many2one `res.company` | required, default the env's company |
| `owner_id` | Many2one `res.partner` | `string="Goods Owner"`, required |
| `date_from` | Date | required, default the first day of the previous month |
| `date_to` | Date | required, default the last day of the previous month |
| `pricelist_id` | Many2one `product.pricelist` | required, default the company's `owner_invoice_pricelist_id` |
| `fee_product_id` | Many2one `product.product` | required, default the company's fee product |
| `material_product_id` | Many2one `product.product` | required, default the company's material product |
| `marker` | Char | `string="Late Attribution Marker"`, default "đã dùng cho đơn" |
| `late_account_id` | Many2one `account.account` | computed from `material_product_id` (its expense account), stored, `readonly=False` |
| `origin` | Char | computed: "Gia công <owner name> MM/YYYY" from `date_to` |
| `line_ids` | One2many `mrp.production.owner.invoice.wizard.line` | computed (D2, D3), stored, `readonly=False` |
| `material_amount` | Monetary | computed (D4) |
| `currency_id` | Many2one `res.currency` | related `company_id.currency_id` |
| `late_line_ids` | Many2many `account.move.line` | computed (D5), read-only |
| `warning` | Text | computed: the styles without a fee rule (D3) and the duplicate (D6), one per line; empty when none |

| Method | Decorator | Behaviour |
|---|---|---|
| `_productions` | — | the orders of D1 |
| `_period_bounds` | — | `date_from` 00:00 and `date_to` + 1 day 00:00 in the user's time zone, as UTC datetimes |
| `_compute_line_ids` | `@api.depends("owner_id", "date_from", "date_to", "pricelist_id", "company_id")` | D2, D3: one command per template, ordered by its display name |
| `_compute_material_amount` | `@api.depends("owner_id", "date_from", "date_to", "company_id")` | D4 |
| `_compute_late_line_ids` | `@api.depends("date_from", "date_to", "late_account_id", "marker", "company_id")` | D5 |
| `_compute_warning` | `@api.depends("line_ids", "origin", "owner_id")` | D3, D6 |
| `action_create_invoice` | — | D7; returns the form action of the new invoice |

### `mrp.production.owner.invoice.wizard.line` — same file

`_name = "mrp.production.owner.invoice.wizard.line"`, TransientModel.

| Field | Type | Attributes |
|---|---|---|
| `wizard_id` | Many2one wizard | required, `ondelete="cascade"` |
| `product_tmpl_id` | Many2one `product.template` | required |
| `quantity` | Float | `digits="Product Unit of Measure"` |
| `price_unit` | Float | `digits="Product Price"` |
| `has_rule` | Boolean | whether D3 found a rule |
| `amount` | Float | computed `quantity × price_unit` |

## Views

### `views/res_config_settings_views.xml`

| Record | Inherits | Content |
|---|---|---|
| `res_config_settings_view_form` | `mrp.res_config_settings_view_form` | a `block` *Processing Invoice* after `process_operations_setting_container` in the `mrp` app, with the three settings |

### `views/owner_invoice_wizard_views.xml`

| Record | Content |
|---|---|
| `owner_invoice_wizard_form` | owner, period, pricelist, the two products; `warning` as an alert when set; `line_ids` editable list (style read-only with `force_save`: the lines are computed in the form, and a read-only field is not sent on save without it; quantity, price, amount); `material_amount`; `late_line_ids` read-only list (date, entry, label, debit) under "Late attributions to add by hand"; buttons *Create Draft Invoice* and *Cancel* |
| `action_owner_invoice_wizard` | `target="new"` |
| menu | *Accounting → Customers → Processing Invoice*, `groups="account.group_account_invoice"` |

## Tests

`tests/test_owner_invoice.py`, `TestOwnerInvoice(TransactionCase)`, `@tagged("post_install", "-at_install")`.

**Fixtures:** as `mrp_production_partner_owner`'s (own company with hand-made accounts, AVCO real-time category,
component A at 10, finished F, BoM F ← 1 A, a *Processing* type with *Goods Owner* *Owner*, an *Order Processing*
type with `production_owned` False); a sales journal and an income account; two service products (fee, material,
the material product's expense account the late-attribution account); a pricelist with a rule F = 500. Helper: a
processing order of 10 done from 6 owned + 4 unowned A.

| Test | Asserts |
|---|---|
| `test_fee_lines` | after the helper, a wizard for *Owner* over the current month: one line F, quantity 10, price 500, `has_rule` True |
| `test_style_without_rule` | the pricelist rule removed: the line's price 0, `has_rule` False, `warning` names F |
| `test_material_amount` | `material_amount` 40 (the 4 unowned A at 10) |
| `test_order_processing_left_out` | an order on *Order Processing* done for *Owner*: no line, `material_amount` 0 |
| `test_period` | a wizard over the previous month: no line |
| `test_create_invoice` | `action_create_invoice`: a draft `out_invoice` of *Owner*, `invoice_origin` "Gia công Owner MM/YYYY", `invoice_date` `date_to`, a fee line 10 × 500 and a material line 40; a second wizard of the same month has the duplicate in `warning` |
| `test_late_attributions` | a posted entry in the month on the late-attribution account labelled "Vải X đã dùng cho đơn Owner": in `late_line_ids`; one without the marker: not |

## Readme

- `DESCRIPTION.md`: proposes the periodic invoice of processing done for an owner: fees per style from a
  pricelist, the company's material at cost, late attributions suggested; writes only an ordinary draft invoice.
- `USAGE.md`: set the fee pricelist (one rule per style), the two service products and the pricelist in
  *Settings → Manufacturing → Processing Invoice*; run *Accounting → Customers → Processing Invoice* for the owner
  and month; check the lines and the warnings, add late attributions and other items on the draft, confirm.
