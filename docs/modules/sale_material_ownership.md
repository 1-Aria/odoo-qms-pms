# sale_material_ownership

The garment company's ownership of materials against the trading company's, per material and in
quantities, and its transfer per batch of sales orders:
- materials count as owned from posted vendor bills that carry a correct e-invoice, for goods received;
- confirmed sales orders are grouped into transfer batches and exploded by their BoMs down to materials;
- each batch nets its materials against the owned balance and prepares a draft bill from the trading
  company for the rest, posted to 33889 through a fiscal position;
- once that bill counts, the batch's orders are covered. Orders and deliveries show their coverage.

A temporary module: it blocks no core flow, posts nothing, and is uninstalled when the transfer is done.
Design: `docs/Accounting/Material Ownership Transfer — Design.md`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Configuration; explosion; batches in draft with their need lines; the owned quantities (`_ownership_quantities`) and the balance report; coverage on sales orders (design §2–§5.2, §7.2, §8) | done | 2026-11-14, first run: `-i` with tests: `exit=0`, 18 tests, 0 failures. UI check on the test database: *Add Uncovered Orders* took all 65 confirmed orders, 18 May–18 Aug, every one from before the separation; production would have taken 273 orders, 259 of them older. Fixed by the ownership start (D16) and the capped warning lists. Saving that code broke every page of the running server until `-u` (new stored field on `res.company`). Second run: `-u` with tests: `exit=0`, 21 tests, 0 failures. UI checked by Peter: start date required, older orders *Not needed*, batch filled from a temporary start date |
| 2 | *Request*: netting, request lines, the draft bill; coverage from the bill; *Cancel*; the effective quantity; the bill's link and the delivery banner (design §5.1, §5.3–§5.4, §6, §7.1) | done | 2026-11-14: `-u` with tests: `exit=0`, 35 tests, 0 failures. UI check by Peter on the test database (start 1 Aug 2026; account 33889 and the fiscal position 3399 → 33889 created by hand, the copy predating the cutover): MTB/2026/0076, 9 orders, 4 lines exploded into 32 materials, 5 cut-panel lines not exploded (no BoM on that copy); 32 materials requested, 82,306 + VAT 8,232; the draft bill: 30 lines on 33889, 1331, 3311, no valuation layer; two packaging lines on 6320 at 0 (that copy's packaging category is periodic with no cost; production's is real-time with input 3399). *Cancel* cancelled the bill |
| 3 | The document for the trading company (design §5.5); two more warning lines (zero cost, not real-time) | delivered | 2026-11-14: code delivered, 5 more tests (40 in all); awaiting the `-u` run |

## Divergences from the design

None. The first draft of this spec departed from the design in four places: the balance computed in
Python rather than by a SQL view (design §4.3), a line closed by its quantities rather than by the
order's *locked* flag (§5.4), unexploded products as need lines (§5.2), and *Request* reserved to
accounting users (§6.1). The design note was corrected on 2026-11-14 to match.

## Decisions

| # | Decision |
|---|---|
| D1 | **A material** is a product whose category has `material_ownership` set. The flag is set per category and not inherited. The instance's categories are set by hand, never seeded |
| D2 | **An order line to explode** has a product of type `consu` (not a service or combo), no `display_type`, is not a down payment and has `product_uom_qty > 0`. A line belongs to at most one batch that is not cancelled. An order joins a batch through its lines, so an order with lines added later can appear in a second batch (design O1) |
| D3 | **Explosion** (design §5.2): a material counts itself. Otherwise the first BoM from `_bom_find(product, company_id=company.id)`, any type, is exploded with `explode`, and every component that is not a material is exploded again in the same way, to a depth of 10. A product with no BoM, or beyond the depth, gets a need line with `exploded = False` (design §5.2). BoMs and products are read with `sudo()`. With `mrp_bom_version` installed (it is on the instance), `_bom_find` only finds BoMs in state *active* (`oca/manufacture/mrp_bom_version/models/mrp_bom.py:139-155`); production holds 86 such BoMs |
| D4 | **Need lines are written when an order joins a draft batch** and deleted when it leaves. *Refresh* rewrites all of them. From *Request* on they never change |
| D5 | **A bill counts** (design D11) when it is a posted `in_invoice` and one of its e-invoices has `direction = "received"`, `correction_state != "replaced"` and `amounts_differ = False`: `account.move._material_einvoice_ok()` |
| D6 | **Owned quantities** (design §4.1), per material, in the product's UoM, from the material bill lines of posted `in_invoice` and `in_refund` moves of the company, read with `sudo()`. A refund line counts negative at once, without an e-invoice. Then:<br>• **Lines from a PO line**, grouped per PO line: `counted` = Σ invoice lines of counting bills − Σ refund lines; `received` = the PO line's `qty_received`; *in* += `min(counted, received)`; *not received* += `max(counted − received, 0)`; *awaiting* += Σ invoice lines of bills that do not count.<br>• **Other lines of a batch bill** (`material_batch_id` set): *in* += quantity if the bill counts, else *awaiting* += quantity; refunds count in *in*.<br>• **Any other line**: a refund counts in *in*; an invoice line goes to *no receipt* if its bill counts, else to *awaiting* |
| D7 | **Used quantities**: for every exploded need line of a batch in `requested` or `covered`, `material_qty / line_qty × effective quantity` of its order line. **Pending**: the `request_qty` of the request lines of batches in `requested`. **Balance** = *in* − *used* |
| D8 | **Effective quantity** of an order line, in its product's UoM (design §5.4): 0 when the order is cancelled; `qty_delivered` when `qty_delivered ≥ product_uom_qty` (`float_compare` at the UoM's rounding); otherwise the larger of the frozen `line_qty` and `qty_delivered`. Core refuses to lower an ordered quantity below what was delivered (`odoo/addons/sale_stock/models/sale_order_line.py:438-439`), so a line is closed by lowering it to exactly the delivered quantity; a pending backorder is left as it is |
| D9 | **Netting** at *Request*, per material of the batch's exploded need lines: `need` = Σ `material_qty`; `available` = *balance* + *pending* of the other batches; `shortfall` = `max(0, −available)`; `request` = `max(0, need − available)`, rounded up to the UoM's rounding and 0 when `float_is_zero`; `unit_cost` = the product's `standard_price` in the company; `amount` = `currency.round(request × unit_cost)` |
| D10 | **One request at a time per company**: *Request* locks the company's batches with `SELECT id FROM sale_material_batch WHERE company_id = %s FOR UPDATE` before reading the quantities. A concurrent request fails with a serialization error, and Odoo retries it on fresh data |
| D11 | **The bill** is a draft `in_invoice` of the company: partner `material_owner_partner_id`, fiscal position `material_fiscal_position_id`, `invoice_origin` the batch's name, `material_batch_id` the batch, one line per request line with `request_qty > 0` (product, quantity, product UoM, `price_unit = unit_cost`). Account and taxes come from core's computes: the stock input account mapped by the fiscal position (`odoo/addons/stock_account/models/account_move.py:266-277`) and the product's vendor taxes. It has no PO line, so posting it makes no valuation layer (design §2.2). The module never posts it |
| D12 | **Batch state** is a stored compute: `cancel` when `cancelled`; `draft` without `date_request`; `covered` when no request line has `request_qty > 0`, or when the batch has `in_invoice` bills not cancelled and every one counts (D5); otherwise `requested`. It goes back to `requested` when a bill stops counting |
| D13 | **Order coverage** is a non-stored compute with a search method: no value unless the order's state is `sale`; `not_needed` without lines to explode or when the order is out of scope (D16); `not_batched` when none of them has a need line in a batch that is not cancelled; `partly` when some have none; else, from those batches' states, `draft` if any is draft, `requested` if any is requested, else `covered` |
| D14 | **Nothing outside the module is refused** (design D10). The module's own actions refuse what breaks its records: adding an order whose lines are all batched, changing a batch's orders outside draft, requesting without the company settings, cancelling a batch with a posted bill, deleting a batch that is neither draft nor cancelled |
| D15 | **Roles.** Salespeople read batches and the balance. *Sales / Administrator* and *Accounting / Administrator* create batches and add orders. *Request* needs *Accounting / Invoicing* (`account.group_account_invoice`), checked in the method (design §6.1). Batches, need and request lines and balance rows follow a company rule |
| D16 | **Ownership start** (design D9): the company's `material_ownership_start`, set by hand (24 Oct 2026 for the garment company), never seeded. An order is in scope when its `date_order`, in the user's time zone, is on or after it (`sale.order._material_in_scope()`). Orders out of scope show `not_needed` and cannot join a batch. Without a start date no order is in scope, and adding orders is refused. On production every order confirmed before 24 Oct was fully delivered before 24 Oct (`prod_copy`, 12 Nov), so the confirmation date is a safe dividing line |

## Folder structure

```
sale_material_ownership/
├── __init__.py, __manifest__.py
├── data/
│   └── ir_sequence_data.xml
├── models/
│   ├── __init__.py
│   ├── account_move.py
│   ├── product_category.py
│   ├── res_company.py
│   ├── res_config_settings.py
│   ├── sale_material_batch.py
│   ├── sale_material_ownership_balance.py
│   ├── sale_order.py
│   └── stock_picking.py                       ← step 2
├── report/                                    ← step 3
│   ├── sale_material_batch_reports.xml
│   └── sale_material_batch_templates.xml
├── security/
│   ├── ir.model.access.csv
│   └── sale_material_ownership_security.xml
├── views/
│   ├── account_move_views.xml                 ← step 2
│   ├── product_category_views.xml
│   ├── res_config_settings_views.xml
│   ├── sale_material_batch_views.xml
│   ├── sale_material_ownership_balance_views.xml
│   ├── sale_order_views.xml
│   └── stock_picking_views.xml                ← step 2
├── tests/
│   ├── __init__.py, common.py
│   ├── test_ownership.py                      ← step 1
│   ├── test_request.py                        ← step 2
│   └── test_document.py                       ← step 3
└── readme/
    ├── DESCRIPTION.md
    └── USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Sale Material Ownership` |
| `summary` | `Materials owned per vendor bill and e-invoice; transfer batches of sales orders invoiced by the former owner` |
| `version` | `18.0.1.0.0` (step 2: `18.0.1.1.0`; step 3: `18.0.1.2.0`) |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Sales/Sales` |
| `depends` | `sale_stock`, `mrp`, `purchase_stock`, `l10n_vn_einvoice` |
| `data` | step 1: `security/ir.model.access.csv`, `security/sale_material_ownership_security.xml`, `data/ir_sequence_data.xml`, `views/sale_material_batch_views.xml`, `views/sale_material_ownership_balance_views.xml`, `views/sale_order_views.xml`, `views/product_category_views.xml`, `views/res_config_settings_views.xml`; step 2 adds `views/account_move_views.xml`, `views/stock_picking_views.xml`; step 3 adds `report/sale_material_batch_templates.xml`, `report/sale_material_batch_reports.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import account_move, product_category, res_company, res_config_settings, sale_material_batch, sale_material_ownership_balance, sale_order` (step 2 adds `stock_picking`) |
| `tests/__init__.py` | `from . import test_ownership` (step 2 adds `test_request`, step 3 `test_document`) |

## Access

`security/ir.model.access.csv`:

| id | model | group | r | w | c | d |
|---|---|---|---|---|---|---|
| `access_sale_material_batch_salesman` | `model_sale_material_batch` | `sales_team.group_sale_salesman` | 1 | 0 | 0 | 0 |
| `access_sale_material_batch_sale_manager` | `model_sale_material_batch` | `sales_team.group_sale_manager` | 1 | 1 | 1 | 1 |
| `access_sale_material_batch_account_invoice` | `model_sale_material_batch` | `account.group_account_invoice` | 1 | 1 | 0 | 0 |
| `access_sale_material_batch_account_manager` | `model_sale_material_batch` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_sale_material_batch_need_salesman` | `model_sale_material_batch_need` | `sales_team.group_sale_salesman` | 1 | 0 | 0 | 0 |
| `access_sale_material_batch_need_sale_manager` | `model_sale_material_batch_need` | `sales_team.group_sale_manager` | 1 | 1 | 1 | 1 |
| `access_sale_material_batch_need_account_invoice` | `model_sale_material_batch_need` | `account.group_account_invoice` | 1 | 0 | 0 | 0 |
| `access_sale_material_batch_need_account_manager` | `model_sale_material_batch_need` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_sale_material_batch_request_salesman` | `model_sale_material_batch_request` | `sales_team.group_sale_salesman` | 1 | 0 | 0 | 0 |
| `access_sale_material_batch_request_account_invoice` | `model_sale_material_batch_request` | `account.group_account_invoice` | 1 | 1 | 1 | 0 |
| `access_sale_material_batch_request_account_manager` | `model_sale_material_batch_request` | `account.group_account_manager` | 1 | 1 | 1 | 1 |
| `access_sale_material_ownership_balance_salesman` | `model_sale_material_ownership_balance` | `sales_team.group_sale_salesman` | 1 | 1 | 1 | 1 |
| `access_sale_material_ownership_balance_account_invoice` | `model_sale_material_ownership_balance` | `account.group_account_invoice` | 1 | 1 | 1 | 1 |

The `name` column repeats the id with spaces for underscores.

`security/sale_material_ownership_security.xml`: four global rules, `domain_force`
`[('company_id', 'in', company_ids)]`, on `model_sale_material_batch`, `model_sale_material_batch_need`,
`model_sale_material_batch_request` and `model_sale_material_ownership_balance`; ids
`<model>_company_rule`.

## Data — `data/ir_sequence_data.xml`

`noupdate="1"`. `ir.sequence` `seq_sale_material_batch`: name *Material Transfer Batch*, code
`sale.material.batch`, prefix `MTB/%(year)s/`, padding 4, `company_id` False.

## Models

### `product.category` — `models/product_category.py`

| Field | Type | Attributes |
|---|---|---|
| `material_ownership` | Boolean | string *Counts as Material*; help *Products of this category are materials for ownership between the garment company and the trading company: owned through vendor bills, used by the sales orders that contain them. Not inherited by sub-categories.* |

### `res.company` — `models/res_company.py`

| Field | Type | Attributes |
|---|---|---|
| `material_ownership_start` | Date | string *Ownership Start*; help *Sales orders confirmed from this date on need their materials transferred. Orders confirmed earlier were sold before the separation and are out of scope. Without a date, no order is in scope.* |
| `material_owner_partner_id` | Many2one `res.partner` | string *Material Owner*; help *The company that still owns the materials not covered by a vendor bill, and invoices them per transfer batch.* |
| `material_fiscal_position_id` | Many2one `account.fiscal.position` | string *Material Transfer Fiscal Position*; `domain="[('company_id', '=', id)]"`; help *Set on the material owner's batch bills. It maps the stock input account to the clearing account, so the bills do not value stock again.* |

### `res.config.settings` — `models/res_config_settings.py`

`material_ownership_start`, `material_owner_partner_id` and `material_fiscal_position_id`, each `related="company_id.<same name>"`,
`readonly=False`. The fiscal position repeats its domain as `[('company_id', '=', company_id)]`: a related
field drops a string domain (`odoo/odoo/fields.py:3141-3152`).

### `account.move` — `models/account_move.py`

| Field | Type | Attributes |
|---|---|---|
| `material_batch_id` | Many2one `sale.material.batch` | string *Material Transfer Batch*; `readonly=True`; `copy=False`; `index="btree_not_null"`; `ondelete="set null"`; `check_company=True` |

**`_material_einvoice_ok()`**: `ensure_one()`. True when `state == "posted"`, `move_type == "in_invoice"`
and any record of `l10n_vn_einvoice_ids` has `direction == "received"`, `correction_state != "replaced"`
and not `amounts_differ` (D5).

### `sale.order` and `sale.order.line` — `models/sale_order.py`

`sale.order`:

| Field | Type | Attributes |
|---|---|---|
| `material_batch_ids` | Many2many `sale.material.batch` | relation `sale_material_batch_order_rel`, columns `order_id`, `batch_id`; string *Transfer Batches*; `readonly=True`; `copy=False` |
| `material_coverage` | Selection | `[("not_needed", "Not needed"), ("not_batched", "Not batched"), ("partly", "Partly batched"), ("draft", "In a draft batch"), ("requested", "Requested"), ("covered", "Covered")]`; string *Material Coverage*; non-stored compute `_compute_material_coverage` (D13); `search="_search_material_coverage"` |

**`_compute_material_coverage()`** — `@api.depends("state", "date_order", "company_id.material_ownership_start",
"order_line.material_need_ids.batch_id.state")`. D13, reading `order_line._material_lines()` and
`_material_in_scope()`.

**`_material_in_scope()`**: `ensure_one()`. False without `company_id.material_ownership_start` or
`date_order`; else `fields.Datetime.context_timestamp(self, date_order).date() >= start` (D16).

**`_search_material_coverage(operator, value)`**: `operator` in `=`, `!=`, `in`, `not in`, else
`NotImplementedError`. `values` = `[value]` or `value`. `ids` = the ids of
`self.search([("state", "=", "sale")])` whose `material_coverage` is in `values`. Returns
`[("id", "in", ids)]` for `=`/`in`, `[("id", "not in", ids)]` otherwise.

`sale.order.line`:

| Field | Type | Attributes |
|---|---|---|
| `material_need_ids` | One2many `sale.material.batch.need` | inverse `order_line_id`; `readonly=True`; `copy=False` |

**`_material_lines()`**: `self.filtered` by D2's line conditions (product `type == "consu"`, no
`display_type`, not `is_downpayment`, `product_uom_qty > 0`).

**`_material_batch_needs()`**: `material_need_ids.filtered(lambda n: n.batch_id.state != "cancel")`.

**`_material_effective_qty(line_qty)`** (step 2): `ensure_one()`. D8, with `qty_delivered` and
`product_uom_qty` converted from `product_uom` to `product_id.uom_id`.

### `sale.material.batch` — `models/sale_material_batch.py`

`_name = "sale.material.batch"`, `_description = "Material Transfer Batch"`, `_inherit = ["mail.thread"]`,
`_order = "id desc"`, `_check_company_auto = True`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | required; `readonly=True`; `copy=False`; default `"New"`; set from the sequence `sale.material.batch` in `create` |
| `company_id` | Many2one `res.company` | required; default `self.env.company`; `index=True`; `readonly="state != 'draft'"` in the view |
| `currency_id` | Many2one `res.currency` | `related="company_id.currency_id"` |
| `state` | Selection | `[("draft", "Draft"), ("requested", "Requested"), ("covered", "Covered"), ("cancel", "Cancelled")]`; stored compute `_compute_state` (D12; step 1: `cancel` or `draft` only); `index=True`; `tracking=True` |
| `cancelled` | Boolean | `readonly=True`; `copy=False` |
| `date_request` | Datetime | string *Requested On*; `readonly=True`; `copy=False` |
| `requested_by_id` | Many2one `res.users` | string *Requested By*; `readonly=True`; `copy=False` |
| `order_ids` | Many2many `sale.order` | relation `sale_material_batch_order_rel`, columns `batch_id`, `order_id`; string *Sales Orders*; `copy=False`; `check_company=True`; `domain="[('company_id', '=', company_id), ('state', '=', 'sale')]"` |
| `need_line_ids` | One2many `sale.material.batch.need` | inverse `batch_id`; `readonly=True` |
| `request_line_ids` | One2many `sale.material.batch.request` | inverse `batch_id`; `readonly=True` |
| `bill_ids` | One2many `account.move` | inverse `material_batch_id`; string *Bills*; `readonly=True` |
| `bill_count` | Integer | non-stored compute |
| `amount_total` | Monetary | step 2; string *Requested Amount*; non-stored compute: Σ `request_line_ids.amount` |
| `warning` | Text | non-stored compute `_compute_warning` |
| `note` | Text | |

SQL constraint `name_company_unique`: `UNIQUE (name, company_id)`.

**`create(vals_list)`** — `@api.model_create_multi`: a `name` of `"New"` or missing takes
`self.env["ir.sequence"].with_company(company).next_by_code("sale.material.batch")`. After `super()`, each
batch with orders calls `_explode_orders(batch.order_ids)`.

**`write(vals)`**: when `order_ids` is in `vals`:
1. Any batch not `draft` → `UserError` *%(batch)s is no longer a draft: its orders cannot change.*
2. `before` = each batch's `order_ids`; `super()`.
3. Per batch: the need lines of removed orders are deleted; `_explode_orders(added)`.

**`_material_start()`**: `ensure_one()`. The company's `material_ownership_start`; without one →
`UserError` *Set the ownership start date of %(company)s in Sales settings first (block Material
Ownership).*

**`_explode_orders(orders)`**: `ensure_one()`. `start = _material_start()`. Per order:
1. Not of the batch's company, or `state != "sale"` → `UserError` *%(order)s is not a confirmed order of %(company)s.*
   Not `_material_in_scope()` → `UserError` *%(order)s was confirmed before the ownership start (%(date)s):
   its goods need no transfer.*
2. `lines` = `order.order_line._material_lines()` without lines that already have a need line in this
   batch or in another batch not cancelled.
3. No `lines`: when the order has no line to explode at all → `UserError` *%(order)s has no goods to
   transfer.*; otherwise → `UserError` *%(order)s has nothing left to transfer: its lines are already in
   %(batches)s.* (the names of the batches of `order.order_line._material_batch_needs()`).
4. Per line: `qty` = `line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id,
   round=False)`;
   `materials, unexploded, bom = self._explode(line.product_id, qty)`; one need line per material
   (`exploded=True`) and per unexploded product (`exploded=False`), with `line_qty = qty` and `bom_id = bom`.

**`_explode(product, qty)`** — `@api.model`-style helper on the batch's company: returns
`(materials, unexploded, top_bom)`, the first two `defaultdict(float)` keyed by `product.product`, per D3:

```
def _explode(self, product, qty):
    materials, unexploded = defaultdict(float), defaultdict(float)
    Bom = self.env["mrp.bom"].sudo()
    company = self.company_id

    def walk(prod, quantity, depth):
        if prod.categ_id.material_ownership:
            materials[prod] += quantity
            return None
        bom = Bom._bom_find(prod, company_id=company.id)[prod] if depth <= 10 else Bom
        if not bom:
            unexploded[prod] += quantity
            return None
        factor = prod.uom_id._compute_quantity(quantity, bom.product_uom_id) / (bom.product_qty or 1.0)
        _boms, lines = bom.explode(prod, factor)
        for bom_line, data in lines:
            comp = bom_line.product_id
            walk(comp, bom_line.product_uom_id._compute_quantity(data["qty"], comp.uom_id), depth + 1)
        return bom

    top_bom = walk(product.sudo(), qty, 0)
    return materials, unexploded, top_bom or Bom
```

**`action_add_uncovered()`**: `ensure_one()`; `_material_start()`; draft only (else the `write` error). `orders` =
`env["sale.order"].search([("company_id", "=", company_id.id), ("state", "=", "sale"),
("material_coverage", "in", ["not_batched", "partly"])], order="date_order, id")`;
`self.order_ids = [Command.link(o.id) for o in orders]`. Returns a `display_notification` whose `next` is the `soft_reload` client action, *%(count)s
orders added.* (*No order to add.* when none), type `info`, `sticky=False`.

**`action_refresh()`**: draft only. Deletes all need lines, then `_explode_orders(self.order_ids)`.

**`_compute_warning()`** — `@api.depends("state", "need_line_ids")`. Draft batches only, else False. One
line per case, joined by newlines:
- *Not exploded (no BoM): %(products)s* — products of need lines with `exploded = False`;
- *Bills awaiting their e-invoice: %(materials)s* — the batch's materials with *awaiting* > 0 in
  `_ownership_quantities(company, materials)`, each as `name (qty uom)`;
- *Billed, not received: %(materials)s* — the same with *not received* > 0;
- (step 3) *Zero unit cost, would be requested at 0: %(materials)s* — the batch's materials whose
  `standard_price` in the company is 0;
- (step 3) *Not valued in real time, the bill line would not post to the clearing account: %(materials)s*
  — those whose `valuation` in the company is not `real_time`: their bill line takes the expense account,
  which the fiscal position does not map. Found in step 2's UI check, where two packaging lines went to
  6320 at 0.

Each list goes through `_material_list(items)` (`@api.model`): the first 10 items joined by commas, then
*and %(count)s more (see Sales → Reporting → Material Ownership)* when there are more.

**`_ownership_quantities(company, products=None, exclude_batch=None)`** — `@api.model`. Returns a
`defaultdict` keyed by product id, each a dict with keys `in`, `used`, `pending`, `awaiting`,
`not_received`, `no_receipt` (floats, the product's UoM), per D6 and D7, `exclude_batch`'s own need and
request lines left out. Everything is read with `sudo()`:
- bill lines: `account.move.line` with `company_id = company`, `parent_state = "posted"`,
  `move_id.move_type in ("in_invoice", "in_refund")`, `display_type = "product"`,
  `product_id.categ_id.material_ownership = True`, and `product_id in products` when given; quantity
  `line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)`; `qty_received` with
  `po_line.product_uom._compute_quantity(po_line.qty_received, po_line.product_id.uom_id)`;
- *used* (step 2): need lines with `exploded = True`, `batch_id.company_id = company`,
  `batch_id.state in ("requested", "covered")`; per line
  `material_qty / line_qty × order_line_id._material_effective_qty(line_qty)`;
- *pending* (step 2): request lines with `batch_id.company_id = company`, `batch_id.state = "requested"`.

In step 1 no batch can leave draft, so *used* and *pending* are 0.

**`_unlink_except_requested()`** — `@api.ondelete(at_uninstall=False)`: a batch not in `draft` or `cancel`
→ `UserError` *Only draft or cancelled transfer batches can be deleted.*

Step 2:

**`_compute_state()`** — `@api.depends("cancelled", "date_request", "request_line_ids.request_qty",
"bill_ids.state", "bill_ids.move_type", "bill_ids.amount_untaxed", "bill_ids.amount_tax",
"bill_ids.amount_total", "bill_ids.currency_id", "bill_ids.l10n_vn_einvoice_ids.direction",
"bill_ids.l10n_vn_einvoice_ids.correction_state", "bill_ids.l10n_vn_einvoice_ids.amount_untaxed",
"bill_ids.l10n_vn_einvoice_ids.amount_tax", "bill_ids.l10n_vn_einvoice_ids.amount_total",
"bill_ids.l10n_vn_einvoice_ids.currency_id")`. D12. A stored compute runs as superuser
(`odoo/odoo/fields.py:443`).

**`action_request()`**: `ensure_one()`.
1. Not `draft` → `UserError` *Only a draft batch can be requested.* No exploded need line → `UserError`
   *%(batch)s has no material to request.*
2. The user lacks `account.group_account_invoice` → `AccessError` *Requesting a transfer batch creates a
   vendor bill: it needs the Accounting / Invoicing group.*
3. The company lacks `material_owner_partner_id` or `material_fiscal_position_id` → `UserError` *Set the
   material owner and the material transfer fiscal position in Sales settings first.*
4. Lock (D10).
5. `q = _ownership_quantities(company, materials, exclude_batch=self)`; per material, D9; one request line
   each, materials ordered by `default_code`, then name.
6. `date_request = now`, `requested_by_id = uid`.
7. Any `request_qty > 0` → the bill (D11), created with
   `env["account.move"].with_company(company).with_context(default_move_type="in_invoice")`.
8. Returns True; the state computes to `requested` or `covered`.

**`action_cancel()`**: `ensure_one()`. Already `cancel` → True. `covered` → `UserError` *%(batch)s is covered
and can no longer be cancelled.* Any bill of the batch `posted` → `UserError` *%(batch)s has a posted bill.
Reset the bill to draft or reverse it first.* Draft bills → `button_cancel()`. `cancelled = True`.

**`action_view_bills()`**: `account.action_move_in_invoice_type` read with `_for_xml_id`, domain
`[("id", "in", bill_ids.ids)]`; with one bill, its form; context `{"create": False}`.

**`_material_covered()`**: `ensure_one()`. True when no request line has `request_qty > 0` (at the UoM's
rounding), or when `_material_bills()` is not empty and every one of them `_material_einvoice_ok()`.
`_material_bills()`: `bill_ids` of type `in_invoice` not cancelled.

**`_create_bill(request_lines)`**: D11, returns the bill.

### `sale.material.batch.need` — `models/sale_material_batch.py`

`_name = "sale.material.batch.need"`, `_description = "Material Transfer Batch Need"`,
`_order = "batch_id, order_id, order_line_id, product_id"`

| Field | Type | Attributes |
|---|---|---|
| `batch_id` | Many2one `sale.material.batch` | required; `ondelete="cascade"`; `index=True` |
| `company_id` | Many2one `res.company` | `related="batch_id.company_id"`; `store=True` |
| `order_line_id` | Many2one `sale.order.line` | required; `ondelete="cascade"`; `index=True` |
| `order_id` | Many2one `sale.order` | `related="order_line_id.order_id"`; `store=True`; `index=True` |
| `sold_product_id` | Many2one `product.product` | `related="order_line_id.product_id"`; string *Sold Product* |
| `bom_id` | Many2one `mrp.bom` | string *BoM*; `ondelete="set null"` |
| `line_qty` | Float | string *Sold Quantity*; `digits="Product Unit of Measure"`; required; the order line's quantity in its product's UoM, frozen |
| `product_id` | Many2one `product.product` | string *Material*; required; `ondelete="restrict"` |
| `uom_id` | Many2one `uom.uom` | `related="product_id.uom_id"` |
| `material_qty` | Float | string *Quantity*; `digits="Product Unit of Measure"`; required |
| `exploded` | Boolean | default True |

SQL constraints: `line_material_unique` `UNIQUE (batch_id, order_line_id, product_id)`; `line_qty_positive`
`CHECK (line_qty > 0)`.

### `sale.material.batch.request` — `models/sale_material_batch.py` (step 2)

`_name = "sale.material.batch.request"`, `_description = "Material Transfer Batch Request"`,
`_order = "batch_id, id"`

| Field | Type | Attributes |
|---|---|---|
| `batch_id` | Many2one `sale.material.batch` | required; `ondelete="cascade"`; `index=True` |
| `company_id` | Many2one `res.company` | `related="batch_id.company_id"`; `store=True` |
| `currency_id` | Many2one `res.currency` | `related="batch_id.currency_id"` |
| `product_id` | Many2one `product.product` | string *Material*; required; `ondelete="restrict"` |
| `uom_id` | Many2one `uom.uom` | `related="product_id.uom_id"` |
| `need_qty`, `available_qty`, `shortfall_qty`, `request_qty` | Float | strings *Needed*, *Available*, *Earlier Shortfall*, *Requested*; `digits="Product Unit of Measure"`; `readonly=True` |
| `unit_cost` | Float | `digits="Product Price"`; `readonly=True` |
| `amount` | Monetary | `readonly=True` |
| `billed_qty` | Float | string *Billed*; non-stored compute `_compute_billed_qty` (`@api.depends("request_qty", "batch_id.bill_ids.state", "batch_id.bill_ids.invoice_line_ids.quantity", "batch_id.bill_ids.l10n_vn_einvoice_ids")`): Σ the product's lines on the batch's counting bills (D5), in the product's UoM, minus its lines on posted refunds of the batch; bills read with `sudo()` |
| `difference_qty` | Float | string *Difference*; non-stored compute: `billed_qty − request_qty` |

SQL constraint `batch_product_unique`: `UNIQUE (batch_id, product_id)`.

### `sale.material.ownership.balance` — `models/sale_material_ownership_balance.py`

`_name = "sale.material.ownership.balance"`, `_description = "Material Ownership Balance"`
(`models.TransientModel`), `_order = "categ_id, product_id"`

| Field | Type | Attributes |
|---|---|---|
| `company_id` | Many2one `res.company` | required |
| `currency_id` | Many2one `res.currency` | `related="company_id.currency_id"` |
| `product_id` | Many2one `product.product` | string *Material* |
| `categ_id` | Many2one `product.category` | |
| `uom_id` | Many2one `uom.uom` | |
| `qty_in` | Float | string *Owned by Bills* |
| `qty_used` | Float | string *Used by Batches* |
| `qty_balance` | Float | string *Balance*: `qty_in − qty_used` |
| `qty_pending` | Float | string *Pending Requests* |
| `qty_awaiting` | Float | string *Awaiting E-Invoice* |
| `qty_not_received` | Float | string *Billed, Not Received* |
| `qty_no_receipt` | Float | string *Not Linked to a Receipt* |
| `qty_on_hand` | Float | string *On Hand* |
| `qty_not_owned` | Float | string *On Hand, Not Owned*: `max(qty_on_hand − max(qty_balance, 0), 0)` |
| `unit_cost` | Float | `digits="Product Price"`; `aggregator=None`: `standard_price` in the company |
| `value_on_hand`, `value_not_owned` | Monetary | quantity × `unit_cost` |

Every quantity has `digits="Product Unit of Measure"`. Quantities and values sum in the pivot.

**`action_open()`** — `@api.model`: `company = self.env.company`; `q = sale.material.batch._ownership_quantities(company)`;
on hand from `stock.quant` `_read_group` with `company_id = company`, `location_id.usage = "internal"`,
grouped by `product_id`, `quantity:sum` (read with `sudo()`). One row for each material (D1) with any
figure or on-hand quantity not zero. Returns an `ir.actions.act_window` named *Material Ownership
Balance*, on this model, `view_mode` `list,pivot`, domain `[("id", "in", rows.ids)]`.

### `stock.picking` — `models/stock_picking.py` (step 2)

| Field | Type | Attributes |
|---|---|---|
| `material_coverage` | Selection | the selection of `sale.order.material_coverage`; non-stored compute from `sale_id.material_coverage` (`@api.depends("sale_id")`) |

All messages are translatable (`self.env._(...)`).

## Views

### `views/sale_material_batch_views.xml`

| Record id | Type | Content |
|---|---|---|
| `sale_material_batch_view_list` | list | `name`, `company_id` (`groups="base.group_multi_company"`), `date_request`, `order_ids` (`widget="many2many_tags"`, `optional="show"`); step 2 adds `amount_total` (`sum`) and `currency_id` (`column_invisible="1"`); `state` (`widget="badge"`, `decoration-info="state == 'draft'"`, `decoration-warning="state == 'requested'"`, `decoration-success="state == 'covered'"`, `decoration-muted="state == 'cancel'"`) |
| `sale_material_batch_view_form` | form | **header:** buttons `action_add_uncovered` *Add Uncovered Orders* (`class="btn-primary"`) and `action_refresh` *Refresh*, `invisible="state != 'draft'"`; (step 2) `action_request` *Request*, `class="btn-primary"`, `groups="account.group_account_invoice"`, `invisible="state != 'draft'"`; `action_cancel` *Cancel*, `invisible="state not in ('draft', 'requested')"`, `confirm` *Cancel this batch? Its draft bill is cancelled and its orders become free.*; `state` `widget="statusbar"`, `statusbar_visible="draft,requested,covered"`. **Between header and sheet:** `div class="alert alert-warning mb-0" role="alert" invisible="not warning"` holding `warning` (`nolabel`). **sheet:** `div name="button_box"` with stat button `action_view_bills` (step 2), icon `fa-file-text-o`, `bill_count` as *Bills*, `invisible="not bill_count"`; title `h1` `name`; a group with `company_id` (`groups="base.group_multi_company"`, `readonly="state != 'draft'"`), `date_request`, `requested_by_id` (both `invisible="not date_request"`), `amount_total` (`invisible="state == 'draft'"`); notebook: page `orders` *Sales Orders*: `order_ids` (`readonly="state != 'draft'"`, list `name`, `partner_id`, `date_order`, `amount_untaxed`, `material_coverage`); page `needs` *Materials*: `need_line_ids` list (`order_id`, `sold_product_id`, `line_qty`, `product_id`, `material_qty`, `uom_id`, `bom_id` `optional="hide"`, `exploded` `optional="hide"`, `decoration-warning="not exploded"`); page `requests` *Request* (step 2, `invisible="state == 'draft'"`): `request_line_ids` list (`product_id`, `uom_id`, `need_qty`, `available_qty`, `shortfall_qty` `optional="hide"`, `request_qty`, `unit_cost`, `amount` `sum`, `billed_qty`, `difference_qty` `decoration-danger="difference_qty < 0"`); page `note` *Note*: `note`. Then `<chatter/>` |
| `sale_material_batch_view_search` | search | `name`, `order_ids`; filters `draft` (*Draft*), `requested` (*Requested*), `covered` (*Covered*) on `state`, and `open` (*Open*, `[("state", "in", ["draft", "requested"])]`); group by `state` |
| `action_sale_material_batch` | `ir.actions.act_window` | name *Material Transfer Batches*, `res_model` `sale.material.batch`, `view_mode` `list,form`, context `{"search_default_open": 1}` |
| `menu_sale_material_batch` | menuitem | parent `sale.sale_order_menu`, action above, sequence 30 |
| `menu_account_material_batch` | menuitem | parent `account.menu_finance_payables`, action above, `groups="account.group_account_invoice"`, sequence 30 |

### `views/sale_material_ownership_balance_views.xml`

| Record id | Type | Content |
|---|---|---|
| `sale_material_ownership_balance_view_list` | list | `create="0"`, `edit="0"`, `delete="0"`: `product_id`, `categ_id` (`optional="hide"`), `uom_id`, `qty_in`, `qty_used`, `qty_balance` (`decoration-danger="qty_balance < 0"`), `qty_pending`, `qty_awaiting`, `qty_not_received` (`optional="hide"`), `qty_no_receipt` (`optional="hide"`), `qty_on_hand`, `qty_not_owned`, `unit_cost` (`optional="hide"`), `value_not_owned` (`sum`), `currency_id` (`column_invisible="1"`) |
| `sale_material_ownership_balance_view_pivot` | pivot | rows `categ_id`; measures `qty_balance`, `value_on_hand`, `value_not_owned` |
| `sale_material_ownership_balance_view_search` | search | `product_id`, `categ_id`; filters `negative` (*Short*, `[("qty_balance", "<", 0)]`), `awaiting` (*Awaiting E-Invoice*, `[("qty_awaiting", ">", 0)]`), `not_owned` (*Not Owned on Hand*, `[("qty_not_owned", ">", 0)]`); group by `categ_id` |
| `action_sale_material_ownership_balance` | `ir.actions.server` | name *Material Ownership*, `model_id` `model_sale_material_ownership_balance`, `state` `code`, `code` `action = model.action_open()` |
| `menu_sale_material_ownership_balance` | menuitem | parent `sale.menu_sale_report`, action above, sequence 50 |

### `views/sale_order_views.xml`

| Record id | Inherits | Change |
|---|---|---|
| `view_order_form_material` | `sale.view_order_form` | `//sheet` before: `<field name="material_coverage" invisible="1"/>` and `div class="alert alert-warning" role="alert"`, `invisible="state != 'sale' or material_coverage not in ('not_batched', 'partly', 'draft', 'requested')"`, text *The materials of this order are not yet transferred from the trading company. Coverage:* and `material_coverage` (`readonly`). `//page[@name='other_information']` inside, last: group `material_ownership` *Material Ownership* with `material_coverage` and `material_batch_ids` (`widget="many2many_tags"`) |
| `view_order_tree_material` | `sale.view_order_tree` | `//list` inside, last: `material_coverage` (`optional="show"`, `widget="badge"`, `decoration-success="material_coverage == 'covered'"`, `decoration-warning="material_coverage in ('not_batched', 'partly')"`) |
| `view_sales_order_filter_material` | `sale.view_sales_order_filter` | after `//filter[@name='my_sale_orders_filter']`: `separator`; filters `material_needs_batch` (*Needs a Transfer Batch*, `[("material_coverage", "in", ["not_batched", "partly"])]`) and `material_not_covered` (*Materials Not Covered*, `[("material_coverage", "in", ["not_batched", "partly", "draft", "requested"])]`) |

### `views/product_category_views.xml`

`product_category_form_view_material`, inheriting `product.product_category_form_view`:
`//group[@name='first']` inside: `material_ownership`.

### `views/res_config_settings_views.xml`

`res_config_settings_view_form_material`, inheriting `sale.res_config_settings_view_form`:
after `//block[@name='quotation_order_setting_container']`, `block title="Material Ownership"
name="material_ownership_setting_container"` with three `setting` (`company_dependent="1"`):
`material_ownership_start` (help *Sales orders confirmed from this date on need their materials
transferred.*), `material_owner_partner_id` (help *The company that invoices the materials of each transfer batch.*) and
`material_fiscal_position_id` (help *Maps the stock input account to the clearing account on its bills.*).

### `views/account_move_views.xml` (step 2)

`view_move_form_material`, inheriting `account.view_move_form`: `//group[@id='header_right_group']` inside,
last: `material_batch_id`, `invisible="move_type not in ('in_invoice', 'in_refund') or not material_batch_id"`.

### `views/stock_picking_views.xml` (step 2)

`view_picking_form_material`, inheriting `stock.view_picking_form`: `//sheet` before:
`<field name="material_coverage" invisible="1"/>` and `div class="alert alert-warning" role="alert"`,
`invisible="picking_type_code != 'outgoing' or material_coverage not in ('not_batched', 'partly', 'draft', 'requested')"`,
text *The materials of this order are not yet transferred from the trading company. Deliver once its
transfer batch is covered.*

## Report (step 3)

### `report/sale_material_batch_reports.xml`

`action_report_material_batch`: `model` `sale.material.batch`, `name` *Bảng kê nguyên phụ liệu*,
`report_type` `qweb-pdf`, `report_name` and `report_file` `sale_material_ownership.report_material_batch`,
`binding_model_id` `model_sale_material_batch`, `binding_type` `report`, `print_report_name`
`'Bang ke NPL - %s' % object.name`, `domain` `[("state", "in", ["requested", "covered"])]`.

### `sale.material.batch._material_document_data()` (step 3)

`ensure_one()`; read in `vi_VN`. Products print without their code (`display_default_code=False`). Returns:

| Key | Value |
|---|---|
| `number`, `date` | `name`; `date_request` as a local date (False before *Request*) |
| `seller` | `company_id.material_owner_partner_id` as a dict: `name`, `vat`, `address` (`_display_address(without_company=True)`, its lines joined by commas) |
| `buyer` | `company_id.partner_id`, the same dict |
| `orders` | per order with exploded need lines, by `date_order`, `id`, left out when nothing is requested for it: `name`, `date` (local date of `date_order`), `partner`, `goods` (per order line: `name`, the frozen `line_qty` as `qty`, `uom`), `materials` (rows of `code`, `name`, `uom`, `qty` with `requested` > 0 only, below) |
| `shortfall` | rows for request lines with `shortfall_qty > 0` |
| `totals` | rows for request lines with `request_qty > 0`, with `unit_cost` and `amount` |
| `total`, `currency` | Σ `amount`; `currency_id` |
| `qty_digits`, `price_digits` | the *Product Unit of Measure* and *Product Price* precisions |

Request lines and material rows are ordered by `default_code`, then name.

Allocation per material *m* (design §5.5): `pool = max(available_qty, 0)`; for each order in the order
above, `need` = Σ its need lines of *m*; `owned = min(pool, need)`; `pool −= owned`; `requested = need −
owned`. The per-order quantities plus `shortfall_qty` add up to `request_qty`, up to the rounding in D9.

### `report/sale_material_batch_templates.xml`

**`report_material_batch`**: `web.html_container`; for each `o` of `docs`, `t-call`
`report_material_batch_document` with `t-lang="'vi_VN'"`.

**`material_table`**: a table *STT · Mã · Tên nguyên phụ liệu · ĐVT · Số lượng* of `rows` (quantities as
`float` with `d['qty_digits']`), called for each order and for the shortfall.

**`report_material_batch_document`**: `o` read in `vi_VN`; `d = o._material_document_data()`;
`web.external_layout`; quantities as `float` with `qty_digits`, prices with `price_digits`, amounts with
the currency's `decimal_places`; dates with the `date` widget. In order:

| Part | Content |
|---|---|
| Title | *BẢNG KÊ NGUYÊN PHỤ LIỆU ĐỀ NGHỊ XUẤT HÓA ĐƠN*; *Số:* `number`; *Ngày* `date` |
| Parties | *Bên bán:* seller's name, *Mã số thuế:* its `vat`, *Địa chỉ:*; *Bên mua:* the same for the buyer |
| I | *I. Chi tiết theo đơn bán hàng*. Per order: a line *Đơn hàng* name, *ngày* `date_order`, *khách hàng* partner, then the goods (*Sản phẩm*, *Số lượng*, *ĐVT*), then a table *STT · Mã · Tên nguyên phụ liệu · ĐVT · Số lượng* of its `materials` |
| II | Only with `shortfall`: *II. Thiếu hụt từ các đợt trước*, the same table |
| III | *III. Tổng hợp* (*II.* when there is no shortfall): *STT · Mã · Tên nguyên phụ liệu · ĐVT · Số lượng · Đơn giá · Thành tiền*; last row *Cộng tiền hàng (chưa có thuế GTGT)* with `total` |
| Signatures | two columns: *Người lập biểu* and *Kế toán trưởng*, each *(Ký, họ tên)* |

## Tests

`MaterialOwnershipCase(TransactionCase)` in `tests/common.py` holds the fixtures and no test methods. Test
classes are `@tagged("post_install", "-at_install")`: the fixtures create a company, products, partners
and orders. Not built on `AccountTestInvoicingCommon` (CLAUDE.md, *Lessons*).

**Fixtures (`setUpClass`):**

- A Vietnamese company *Material Ownership Test Company* (`base.vn`, `base.VND`) linked to the test user,
  the `vn` chart loaded with `try_loading("vn", company=…, install_demo=False)`, put in the env's
  `allowed_company_ids`, as `l10n_vn_voucher_stock`'s fixtures do. Its warehouse is `warehouse`.
- Accounts `3399` (`liability_current`), `1599` (`asset_current`) and `33889` (`liability_current`) created
  in it; valuation account `account.<company id>_chart152` (code `1520`).
- `categ_material` (`material_ownership` True) and `categ_goods` (False), each `property_cost_method`
  `average`, `property_valuation` `real_time`, valuation `1520`, input `3399`, output `1599`, journal the
  company's `STJ` (set `with_company`).
- Products, storable (`is_storable`): `fabric` (`categ_material`, UoM `uom.product_uom_meter`),
  `button` (`categ_material`, Units), `panel` and `shirt` (`categ_goods`), `towel` (`categ_goods`, no BoM);
  and `service` (`type="service"`).
  `standard_price` with company: fabric 50,000, button 500. `fabric` and `button` have
  `purchase_method = "receive"`.
- BoMs, all `type="normal"`, `product_qty` 1, created with `active=True` (`mrp_bom_version` creates BoMs
  archived outside tests): `panel` ← 1.5 m `fabric`; `shirt` ← 1 `panel` + 5 `button`.
- Partners `supplier`, `trading` (the material owner) and `customer`. A fiscal position `fp` in the
  company mapping `3399` → `33889`. `company.material_ownership_start` = today − 30 days (`start`),
  `material_owner_partner_id = trading`, `material_fiscal_position_id = fp`.
- Users in the company only: `salesman` (`sales_team.group_sale_salesman`), `sale_manager`
  (`sales_team.group_sale_manager`), `accountant` (`sales_team.group_sale_manager` and
  `account.group_account_invoice`).

**Helpers:**
- `_order(lines, partner=None, confirm=True)`: a sales order for `customer` with `(product, qty)` lines,
  confirmed unless `confirm` is False (a quotation).
- `_stock(product, qty)`: `stock.quant._update_available_quantity` in the warehouse's stock location.
- `_deliver(order, qty=None)`: the order's open outgoing transfer, `action_assign()`, each move's `quantity`
  set to `qty` (its demand when None) and `picked`, validated with `skip_backorder=True` (a backorder
  holds the rest); asserts it is done.
- `_request(batch, user=None)`: `action_request()` as `user` (default `accountant`). `_post(bill)`: sets
  `invoice_date` and posts.
- `_purchase(product, qty, receive=None)`: a PO from `supplier`, confirmed, its receipt validated for
  `receive` (default `qty`; less leaves a backorder).
- `_bill(po)`: the bill from `po.action_create_invoice()`, `invoice_date` today, posted.
- `_direct_bill(partner, lines, refund=False)`: an `in_invoice` (`in_refund`) without PO, posted.
- `_einvoice(move, **overrides)`: an `l10n_vn.einvoice` with `direction="received"`, `move_id=move`,
  `format_version="2.1.0"`, `form="1"`, `symbol="C26TAA"`, a unique `number`, `invoice_date`
  `move.invoice_date`, `seller_vat="0300000001"`, `currency_id` VND, and the move's three amounts times
  −1 for a refund; `overrides` replace any of them.
- `_batch(*orders)`: a batch with those orders. `_q(*products)`: `_ownership_quantities(company, products)`
  as `{product: dict}`.
- `_as(user)` = `self.env(user=user, context=dict(self.env.context, allowed_company_ids=[company.id]))`.

### Step 1 — `tests/test_ownership.py`, `TestOwnership`

| Test | Asserts |
|---|---|
| `test_explode_two_levels` | `_batch(_order([(shirt, 10)]))`: two need lines, `fabric` 15 and `button` 50, both `line_qty` 10, `bom_id` the shirt's BoM, `exploded` True |
| `test_material_sold_as_such` | an order of 20 m `fabric`: one need line, `fabric` 20, no `bom_id` |
| `test_not_exploded` | an order of `towel` and `shirt`: a need line for `towel` with `exploded` False; `warning` names *towel*; `_q(towel)` is empty |
| `test_bill_needs_einvoice` | `_bill(_purchase(fabric, 100))`: `in` 0, `awaiting` 100. After `_einvoice(bill)`: `in` 100, `awaiting` 0 |
| `test_einvoice_amounts_differ` | `_einvoice(bill, amount_total=bill.amount_total + 1000)`: `in` 0, `awaiting` 100 |
| `test_einvoice_replaced` | `e1 = _einvoice(bill)`; a second e-invoice, not attached, with `relation_type="1"` and `related_einvoice_id=e1`: `e1.correction_state` = `replaced`; `in` 0 |
| `test_issued_einvoice_ignored` | `_einvoice(bill, direction="issued")`: `in` 0 |
| `test_billed_not_received` | `fabric.purchase_method = "purchase"`; `_purchase(fabric, 100, receive=60)`, billed 100 with an e-invoice: `in` 60, `not_received` 40 |
| `test_refund_counts_at_once` | a counted bill of 100 m; `_direct_bill(supplier, [(fabric, 30)], refund=True)` without e-invoice: `in` 70 |
| `test_direct_bill_no_receipt` | `_direct_bill(supplier, [(fabric, 10)])` with an e-invoice: `in` 0, `no_receipt` 10 |
| `test_draft_batch_uses_nothing` | a counted bill of 100 m and a draft batch needing 15 m: `in` 100, `used` 0 |
| `test_order_lines_in_one_batch` | an order in draft batch A: `_batch(order)` raises `UserError`. Removing it from A deletes A's need lines; then batch B takes it (positive control) |
| `test_line_added_after_batch` | an order of 10 shirts in batch A; a line of 4 m `fabric` added to the confirmed order: `material_coverage` = `partly`; batch B with the order gets one need line, `fabric` 4 |
| `test_coverage_and_search` | an order of shirts: `not_batched`, found by `search([("material_coverage", "=", "not_batched")])`; in a draft batch: `draft`, no longer found; an order of a service product only: `not_needed`; a quotation: False |
| `test_add_uncovered` | O1 (shirts) and O2 (fabric) uncovered, O3 in another batch, O4 services only: `action_add_uncovered()` on an empty batch gives `order_ids` = O1 + O2 and need lines for both; the notification counts 2 |
| `test_order_with_no_goods_refused` | `_batch` of a services-only order raises `UserError` *no goods* |
| `test_order_before_start_out_of_scope` | an order whose `date_order` is set to noon the day before `start`: `material_coverage` = `not_needed`; `_batch` raises *before the ownership start*; `action_add_uncovered()` on a new batch adds only a recent order |
| `test_start_required` | with `material_ownership_start` cleared: an order shows `not_needed`; `_batch` and `action_add_uncovered()` raise *ownership start date* |
| `test_warning_list_capped` | `_material_list(["a", "b"])` = `"a, b"`; with 12 items: holds `m9`, not `m10`, and *2 more* |
| `test_balance_report` | a counted bill of 100 m received: `action_open()` returns rows; the `fabric` row has `qty_in` 100, `qty_on_hand` 100, `qty_not_owned` 0; with 20 m more received from a PO without a bill, `qty_on_hand` 120, `qty_not_owned` 20 |
| `test_access` | as `salesman`: reading a batch works (positive control); creating one raises `AccessError`. As `sale_manager`: creating a batch with an order works |

### Step 2 — `tests/test_request.py`, `TestRequest`

| Test | Asserts |
|---|---|
| `test_request_nets_against_balance` | 100 m `fabric` owned; a batch of 10 shirts, requested as `accountant`: request lines `fabric` (need 15, available 100, request 0) and `button` (need 50, available 0, request 50, unit cost 500, amount 25,000); state `requested`; one draft bill: partner `trading`, fiscal position `fp`, one line `button` 50 × 500 on account `33889`, `invoice_origin` the batch's name |
| `test_bill_posts_no_stock` | a batch of an order of 50 `button`, requested; its bill posted: no `stock.valuation.layer` on the bill or its lines; 33889 debited 25,000 |
| `test_all_owned_covered_at_once` | 100 m `fabric` and 100 `button` owned: *Request* gives state `covered` and no bill |
| `test_pending_not_requested_twice` | batch A requested for 50 buttons (bill draft); batch B with 4 shirts: `button` available 0, request 20 |
| `test_covered_when_bill_counts` | A's bill posted: `requested`; `_einvoice(bill)`: `covered`, and the order's `material_coverage` is `covered`; the bill reset to draft: `requested` |
| `test_shortfall_next_batch` | A's bill reduced to 45 buttons, posted with an e-invoice: A `covered`, `difference_qty` −5. Batch B with 4 shirts: `button` available −5, shortfall 5, request 25 |
| `test_partial_delivery` | 100 shirts in stock; a requested order of 10 shirts: 6 delivered: `used` `fabric` 15; the line's quantity lowered to 6: `used` 9 |
| `test_return_released` | 10 delivered, 4 returned with `to_refund=True` through `stock.return.picking`: `qty_delivered` 6, `used` 15; the line's quantity lowered to 6: `used` 9 |
| `test_delivered_beyond_order` | 10 shirts batched, the line raised to 12 and 12 delivered: `used` `fabric` 18 |
| `test_cancelled_order_released` | an order in a requested batch, `_action_cancel()`: `used` 0 |
| `test_cancel_batch` | requested batch with a draft bill: `action_cancel()` cancels the bill and frees the order (`not_batched`); with the bill posted, `action_cancel()` raises `UserError` |
| `test_request_requires_settings` | without `material_fiscal_position_id`: `UserError`; nothing written |
| `test_request_access` | as `sale_manager`: `action_request()` raises `AccessError`; as `accountant` it works (positive control) |
| `test_picking_banner_field` | the outgoing transfer of an uncovered order: `material_coverage` = `not_batched`; of a covered order: `covered` |

### Step 3 — `tests/test_document.py`, `TestDocument`

`vi_VN` activated in `setUpClass` (`res.lang._activate_lang`).

| Test | Asserts |
|---|---|
| `test_allocation_oldest_first` | 10 m `fabric` owned; orders O1 and O2 of 10 shirts each (15 m each), batched and requested: `request_qty` 20; O1 prints 5 m, O2 15 m |
| `test_shortfall_section` | a batch with `shortfall_qty` 5 buttons: `shortfall` holds it; per-order quantities + shortfall = `request_qty` |
| `test_render` | a requested batch of an order of 50 `button`: `_render_qweb_html` holds *BẢNG KÊ NGUYÊN PHỤ LIỆU ĐỀ NGHỊ XUẤT HÓA ĐƠN*, the batch's name, the order's name, `25.000` and the seller's name |
| `test_draft_not_printed` | `get_valid_action_reports` keeps the action for a requested batch, not for a draft one |
| `test_warning_cost_and_valuation` | a draft batch with an order of a zero-cost material, a material in a `manual_periodic` category and `button`: the warning names the first under *Zero unit cost* and the second under *Not valued in real time*, and not `button` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Temporary module for the separation of the garment company from the trading company. Materials are owned through posted vendor bills with a correct e-invoice, for goods received; sales orders are grouped into transfer batches, exploded by BoM to materials and netted against that balance; the trading company invoices the rest, booked to the clearing account through a fiscal position. Shows coverage on orders and deliveries; blocks nothing and posts nothing. Uninstall when the transfer is done |
| `readme/USAGE.md` | Mark the material categories (*Counts as Material*). Create a fiscal position for the material owner's bills, *Detect Automatically* off, mapping the stock input account (3399) to the clearing account (33889), with no tax mapping. In Sales settings set the ownership start, the material owner and that fiscal position. Attach the e-invoice XML to every material bill. Create a batch under *Sales → Orders → Material Transfer Batches*, *Add Uncovered Orders*, read the warning, then *Request* (accounting users). Print the *Bảng kê* for the trading company. When its e-invoice arrives, attach it to the batch's draft bill, match the quantities and post. Lower an order line's quantity to what was delivered when the rest will not ship or was returned. *Sales → Reporting → Material Ownership* shows the balance per material |
