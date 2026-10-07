# qms_quality_report

Quality reporting over inspections: Inspection Analysis (DHU, defective %, FTR, defect-free share)
and Defect Analysis (the defect Pareto), and a fabric section over roll rows and point entries.
Design: `docs/QMS Quality Reporting — Design.md`. Plan: §8, §10 Phase 3.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Inspection Analysis and Defect Analysis: the line's and the inspection's `qms_qty_defects`, `qms_workcenter_id`, `qms_defect_free`, the related dimensions, both actions with their domains, pivots, lists and search views, and the *Reporting* menu | done | 2026-10-07, one pass. `-i`, `exit=0`, 11 tests, 0 failures; UI checked as role-matrix users: *Reporting* shown to a quality-control manager and not to a user; as a manager without MRP or Inventory rights, Inspection Analysis opening on *First inspections* with its pivot and four measures, draft and roll inspections absent with the filter removed, grouping by partner, work centre, lot and checkpoint category, the search by product and partner; Defect Analysis's Pareto by code and severity, the *No defect code* group, grouping by month |
| 2 | The fabric section: `qms_accepted`, average aggregators and the related dimensions on rolls, the related dimensions on point entries; Roll, Shade and Fabric Defect Analysis | done | 2026-10-07, one pass. `-u`, `exit=0`, 18 tests (7 new), 0 failures; UI checked as a quality-control manager without Inventory rights: the three menus under *Reporting*, Roll Analysis by partner and month with acceptance and score averaged, Shade Analysis opening on the band distribution with a banded-only roll counted and the ΔE averages changing under *ΔE measured*, Fabric Defect Analysis by defect code with points summed, grouping by roll, a roll inspection switched to a plain test absent from all three |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §5.2 lists the line's related dimensions | adds `qms_test_category_id`, on the inspection and the line | §2 names OCA's `qc.test.category` as the level above the checkpoint; grouping by it needs a field |
| 2 | §5.2 declares the inspection's supplier as related `picking_id.partner_id` and the line's dimensions as related to the inspection | the line's supplier is related `inspection_id.picking_id.partner_id`, straight to the stored field, not through the inspection's related field | A non-stored related field is grouped by joining along its path, which must be Many2one hops ending on a field the database holds (`odoo/odoo/models.py:2932-2954`). Every dimension is declared to end on a stored field (D3) |
| 3 | §5.2 labels `qms_partner_id` *Supplier* | *Partner*, with help naming both cases | It is the picking's partner, and this instance has QC triggers on delivery orders as well as receipts (`qc_trigger` *My Company: Delivery Orders*); there the partner is the customer |
| 4 | §8.1 adds `qms_inspection_state` as a related field on the roll | not added (step 2) | The fabric domains name the state through the path `inspection_id.state` (D8); a related field would serve filtering alone, which a domain path already does |
| 5 | §8.1 does not mention aggregators | `score` and the three ΔE values re-declared to average (step 2, D9) | Shade Analysis's average ΔE and Roll Analysis's average score need it; summed they mean nothing |

## Decisions

| # | Decision |
|---|---|
| D1 | **The report's views are records of their own, at priority 99,** bound to the actions through `view_ids`. OCA's inspection and line views stay the defaults everywhere else, and the report's columns and filters do not leak into the inspection menus |
| D2 | **The finished states are written into the action domains as literals** — `('waiting', 'success', 'failed')`, `INSPECTION_DONE_STATES` of `qms_quality_control`. An XML domain cannot import a Python constant; `test_inspection_action_domain` compares the two, so they cannot drift apart unnoticed |
| D3 | **Every related dimension ends on a stored field,** through Many2one hops only, and is not stored itself (design D13) — the condition for grouping by it in SQL (`odoo/odoo/models.py:2932-2954`) and offering it in the pivot (`odoo/odoo/fields.py:913-926`). `related_sudo` defaults to true, which the traversal requires (`:2935-2936`) |
| D4 | **The menu is *Quality Control → Reporting*,** sequence 30, between *Tests* (20) and *Configuration* (100) (`quality_control_oca/views/qc_menus.xml`), for `quality_control_oca.group_quality_control_manager` (design D9). The app has no reporting menu of its own to extend. The actions carry no group: the menu is the gate, and the manager group already reads inspections and lines through the user group it implies |
| D5 | **The work centre is the production order's work orders' single work centre,** or empty (design D4): `production_id.workorder_ids.workcenter_id`, set when it is exactly one record. Empty without an order, without work orders, or with several work centres |
| D6 | **The line's defects depend on `success` and `qms_qty_failed`;** the inspection's sum on its lines' `qms_qty_defects`. Both stored, so the pivot sums them |
| D8 | **The fabric analyses read `qms_fabric_inspection`'s rows in place** (step 2, design §8.1): Roll and Shade Analysis on `qms.inspection.roll`, Fabric Defect Analysis on `qms.inspection.point`. Their domains name the inspection through the path — `inspection_id.state`, `inspection_id.qms_roll_inspection` — so no related field is added for filtering alone; related fields are added for grouping |
| D9 | **`score` and the three ΔE values average** (step 2): re-declared here with `aggregator="avg"` only. A field declared again in an inheriting model merges onto the earlier definitions' attributes (`odoo/odoo/fields.py:409-425`), so compute, storage and label stay `qms_fabric_inspection`'s. Summed, an average score or ΔE means nothing; the pivot offers each field with its own aggregator |
| D10 | **One search view for both roll analyses** (step 2): Roll and Shade Analysis read the same rows with different domains, and the same filters and group-bys serve both |
| D11 | **The roll inspection is required in every fabric domain** (step 2): rolls left on an inspection switched to a plain test are excluded, as `qms_fabric_inspection` excludes them from the verdict and the lot's band. The lot stays a group-by, not a search field, as D7 has it |
| D12 | **Unread ΔE values are excluded by a filter, not the domain** (step 2). `qms_fabric_inspection` stores an unread ΔE as 0.0 (its D12), and Shade Analysis keeps banded-only rolls for the band distribution, so its ΔE averages would count every unread roll as a perfect 0.0 and look better than the fabric is. The domain cannot drop them without dropping them from the band count; a filter per value — *ΔE measured*, *Head–tail measured*, *Side–centre–side measured* — is applied when reading the averages. One per value because the team may read them on different rolls. A real reading of exactly 0.00 is excluded with the unread ones, which on a spectrophotometer's two decimals is accepted |
| D7 | **Work centre, lot and production order are group-bys, not search fields.** A Many2one search field searches its comodel as the user, and `mrp.workcenter` and `mrp.production` need MRP rights (`mrp/security/ir.model.access.csv:6`), `stock.lot` Inventory rights (`stock/security/ir.model.access.csv:14`) — rights a quality-control manager in the role matrix need not hold. A group's name is read as superuser (`odoo/odoo/models.py:2612`), and a list's Many2one label too, so grouping and listing by them is safe. Product and partner stay search fields: every internal user reads them |

## Folder structure

```
qms_quality_report/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── qc_inspection.py
│   ├── qc_inspection_line.py
│   ├── qms_inspection_roll.py                          # 2
│   └── qms_inspection_point.py                         # 2
├── views/
│   ├── qc_inspection_report_views.xml
│   ├── qc_inspection_line_report_views.xml
│   ├── qms_fabric_report_views.xml                     # 2
│   └── qms_quality_report_menus.xml
├── tests/__init__.py, test_qms_quality_report.py
│         test_qms_fabric_report.py                       # 2
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Quality Report` |
| `summary` | `Inspection and defect analysis: DHU, defective %, FTR, defect-free share and the defect Pareto` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `qms_quality_control`, `qms_fabric_inspection`, `quality_control_mrp_oca`, `quality_control_stock_oca` |
| `data` | `views/qc_inspection_report_views.xml`, `views/qc_inspection_line_report_views.xml`, `views/qms_fabric_report_views.xml` (step 2), `views/qms_quality_report_menus.xml` |
| `installable` | `True` |

No access file: no new model. The analyses read `qc.inspection` and `qc.inspection.line`, which the
quality-control groups read already (`quality_control_oca/security/ir.model.access.csv:2-3`).

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qc_inspection_line`, `from . import qc_inspection`, `from . import qms_inspection_roll`, `from . import qms_inspection_point` (step 2) |
| `tests/__init__.py` | `from . import test_qms_quality_report`, `from . import test_qms_fabric_report` (step 2) |

## Models

### `qc.inspection.line` — `models/qc_inspection_line.py`

`_inherit = "qc.inspection.line"`. The line carries `success` (stored, OCA), `qms_qty_failed`,
`qms_defect_code_id` and `qms_severity_id` (`qms_quality_control`), `product_id`, `picking_id`,
`lot_id` and `production_id` (stored, OCA and its bridges).

| Field | Type | Attributes |
|---|---|---|
| `qms_qty_defects` | Float | `compute="_compute_qms_qty_defects"`, `store=True`, `string="Defects"`, help: on a failed line its quantity failed, or 1 when none was entered; 0 on a passing line |
| `qms_inspection_date` | Datetime | `related="inspection_id.date"`, `string="Inspection Date"` |
| `qms_workcenter_id` | Many2one → `mrp.workcenter` | `related="inspection_id.qms_workcenter_id"`, `string="Work Centre"` |
| `qms_partner_id` | Many2one → `res.partner` | `related="inspection_id.picking_id.partner_id"`, `string="Partner"`, help: the receipt's supplier, or the delivery's customer (divergences 2, 3) |
| `qms_test_id` | Many2one → `qc.test` | `related="inspection_id.test"`, `string="Checkpoint"` |
| `qms_test_category_id` | Many2one → `qc.test.category` | `related="inspection_id.test.category"`, `string="Checkpoint Category"` (divergence 1) |
| `qms_reinspection` | Boolean | `related="inspection_id.qms_reinspection"`, `string="Re-inspection"` |
| `qms_inspection_state` | Selection | `related="inspection_id.state"`, `string="Inspection Status"` |
| `qms_roll_inspection` | Boolean | `related="inspection_id.qms_roll_inspection"`, `string="Roll Inspection"` |

All related fields are not stored (D3).

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_qty_defects` | `@api.depends("success", "qms_qty_failed")` | 0 when `success`; otherwise `qms_qty_failed` when above 0, else 1 (design D12) |

### `qc.inspection` — `models/qc_inspection.py`

`_inherit = "qc.inspection"`. The inspection carries `qms_qty_inspected`, `qms_qty_defective` and
`qms_reinspection` (`qms_quality_control`), `qms_roll_inspection` (`qms_fabric_inspection`),
`production_id`, `picking_id` and `lot_id` (stored, the OCA bridges).

| Field | Type | Attributes |
|---|---|---|
| `qms_qty_defects` | Float | `compute="_compute_qms_qty_defects"`, `store=True`, `string="Defects"`, help: the defects of the inspection's lines |
| `qms_workcenter_id` | Many2one → `mrp.workcenter` | `compute="_compute_qms_workcenter_id"`, `store=True`, `index=True`, `string="Work Centre"`, help: the work centre of the production order's work orders, when they all use one |
| `qms_defect_free` | Float | `compute="_compute_qms_defect_free"`, `store=True`, `aggregator="avg"`, `string="Defect-free (%)"`, help: 100 for an inspection with no failed line, 0 otherwise; averaged, the share of defect-free inspections |
| `qms_partner_id` | Many2one → `res.partner` | `related="picking_id.partner_id"`, `string="Partner"`, help: the receipt's supplier, or the delivery's customer (divergence 3) |
| `qms_test_category_id` | Many2one → `qc.test.category` | `related="test.category"`, `string="Checkpoint Category"` (divergence 1) |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_qty_defects` | `@api.depends("inspection_lines.qms_qty_defects")` | the sum of the lines' `qms_qty_defects` |
| `_compute_qms_workcenter_id` | `@api.depends("production_id.workorder_ids.workcenter_id")` | the work orders' work centres; that one when there is exactly one, else `False` (D5) |
| `_compute_qms_defect_free` | `@api.depends("success")` | 100.0 when `success`, else 0.0 |

**The defect-free share is a plain 100/0** over `success`, not empty outside finished states: a
computed Float cannot store empty (`odoo/odoo/fields.py:1685-1689`), and the action's domain keeps
only finished inspections (design §6, D14).

### `qms.inspection.roll` — `models/qms_inspection_roll.py` (step 2)

`_inherit = "qms.inspection.roll"`. The roll carries `scored`, `score`, `total_points`, `points_pass`,
`shade_pass`, `passed`, `dye_lot` (stored), `shade_band`, `delta_e`, `delta_e_length`, `delta_e_width`
and `lot_id` (`qms_fabric_inspection`).

| Field | Type | Attributes |
|---|---|---|
| `qms_accepted` | Float | `compute="_compute_qms_accepted"`, `store=True`, `aggregator="avg"`, `string="Accepted (%)"`, help: 100 when the roll passes its points, 0 otherwise; averaged over scored rolls, roll acceptance |
| `score` | Float | re-declared with `aggregator="avg"` only (D9) |
| `delta_e`, `delta_e_length`, `delta_e_width` | Float | re-declared with `aggregator="avg"` only (D9) |
| `qms_partner_id` | Many2one → `res.partner` | `related="inspection_id.picking_id.partner_id"`, `string="Partner"`, help: the receipt's supplier |
| `qms_product_id` | Many2one → `product.product` | `related="inspection_id.product_id"`, `string="Fabric"` |
| `qms_inspection_date` | Datetime | `related="inspection_id.date"`, `string="Inspection Date"` |

All related fields are not stored (D3).

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_accepted` | `@api.depends("points_pass")` | 100.0 when `points_pass`, else 0.0 |

An unscored roll passes its points and so carries 100; Roll Analysis's domain keeps scored rolls only
(design D14), so it never reaches the average.

### `qms.inspection.point` — `models/qms_inspection_point.py` (step 2)

`_inherit = "qms.inspection.point"`. The entry carries `roll_id`, `position`, `defect_code_id` and
`points` (`qms_fabric_inspection`).

| Field | Type | Attributes |
|---|---|---|
| `qms_partner_id` | Many2one → `res.partner` | `related="roll_id.inspection_id.picking_id.partner_id"`, `string="Partner"`, help: the receipt's supplier |
| `qms_product_id` | Many2one → `product.product` | `related="roll_id.inspection_id.product_id"`, `string="Fabric"` |
| `qms_inspection_date` | Datetime | `related="roll_id.inspection_id.date"`, `string="Inspection Date"` |
| `qms_dye_lot` | Char | `related="roll_id.dye_lot"`, `string="Dye Lot"` — the roll's stored copy |

All related fields are not stored (D3).

## Views — `views/qc_inspection_report_views.xml`

Records on `qc.inspection`, each `priority` 99 (D1).

| XML id | Type | Content |
|---|---|---|
| `qc_inspection_report_view_pivot` | pivot | `string="Inspection Analysis"`, `sample="1"`; row `test`; col `date` (`interval="month"`); measures `qms_qty_inspected`, `qms_qty_defects`, `qms_qty_defective`, `qms_defect_free` |
| `qc_inspection_report_view_list` | list | `name`, `date`, `test`, `product_id`, `qms_partner_id`, `qms_workcenter_id`, `lot_id` (`optional="hide"`), `user` (`optional="hide"`), `state`, `qms_qty_inspected`, `qms_qty_defects`, `qms_qty_defective` (each `sum="Total"`), `qms_defect_free` (`optional="hide"`); `create="0"` |
| `qc_inspection_report_view_search` | search | fields `test`, `product_id`, `qms_partner_id` (D7); filters below; group-bys below |
| `qc_inspection_report_action` | `ir.actions.act_window` | `name` *Inspection Analysis*, `res_model` `qc.inspection`, `view_mode` `pivot,list,form`, `view_ids` the pivot and the list, `search_view_id` the search view, `domain` `[('state', 'in', ('waiting', 'success', 'failed')), ('qms_roll_inspection', '=', False)]` (D2, design D14), `context` `{'search_default_first_inspections': 1}` |

**Filters:** `first_inspections` — *First inspections*, `[('qms_reinspection', '=', False)]`;
`reinspections` — *Re-inspections*, `[('qms_reinspection', '=', True)]`; separator;
`defect_free` — *Defect-free*, `[('success', '=', True)]`; `with_defects` — *With defects*,
`[('success', '=', False)]`; separator; a date filter on `date`.

**Group-bys:** checkpoint (`test`), checkpoint category (`qms_test_category_id`), product
(`product_id`), work centre (`qms_workcenter_id`), partner (`qms_partner_id`), lot (`lot_id`),
production order (`production_id`), inspector (`user`), month (`date:month`).

## Views — `views/qc_inspection_line_report_views.xml`

Records on `qc.inspection.line`, each `priority` 99 (D1).

| XML id | Type | Content |
|---|---|---|
| `qc_inspection_line_report_view_pivot` | pivot | `string="Defect Analysis"`, `sample="1"`; row `qms_defect_code_id`; col `qms_severity_id`; measure `qms_qty_defects` |
| `qc_inspection_line_report_view_list` | list | `inspection_id`, `qms_inspection_date`, `qms_test_id`, `product_id`, `name`, `qms_defect_code_id`, `qms_severity_id`, `qms_qty_defects` (`sum="Total"`), `qms_partner_id` (`optional="hide"`), `qms_workcenter_id` (`optional="hide"`); `create="0"` |
| `qc_inspection_line_report_view_search` | search | fields `qms_defect_code_id`, `qms_test_id`, `product_id`, `qms_partner_id` (D7); filters below; group-bys below |
| `qc_inspection_line_report_action` | `ir.actions.act_window` | `name` *Defect Analysis*, `res_model` `qc.inspection.line`, `view_mode` `pivot,list`, `view_ids` the pivot and the list, `search_view_id` the search view, `domain` `[('success', '=', False), ('inspection_id.state', 'in', ('waiting', 'success', 'failed'))]` (D2), `context` `{'search_default_first_inspections': 1}` |

**Filters:** `first_inspections` — *First inspections*, `[('qms_reinspection', '=', False)]`;
`reinspections` — *Re-inspections*; separator; `no_code` — *No defect code*,
`[('qms_defect_code_id', '=', False)]`, the configuration gap the design wants visible (§6); a date
filter on `qms_inspection_date`.

**Group-bys:** defect code (`qms_defect_code_id`), severity (`qms_severity_id`), checkpoint
(`qms_test_id`), checkpoint category (`qms_test_category_id`), product (`product_id`), work centre
(`qms_workcenter_id`), partner (`qms_partner_id`), month (`qms_inspection_date:month`).

The Defect Analysis domain keeps roll inspections' failed question lines — weight, width, hand —
which are defects found at receipt (design §6).

## Views — `views/qms_fabric_report_views.xml` (step 2)

Records each `priority` 99 (D1). Every action's domain carries the finished states as literals (D2)
and the roll-inspection term (D11).

| XML id | Type | Content |
|---|---|---|
| `qms_inspection_roll_report_view_search` | search on `qms.inspection.roll` | fields `qms_product_id`, `qms_partner_id`, `dye_lot`, `shade_band`; filters below; group-bys below (D10) |
| `qms_inspection_roll_report_view_pivot` | pivot | `string="Roll Analysis"`, `sample="1"`; row `qms_partner_id`; col `qms_inspection_date` (`interval="month"`); measures `qms_accepted`, `score`, `total_points` |
| `qms_inspection_roll_report_view_list` | list | `inspection_id`, `qms_inspection_date`, `lot_id`, `dye_lot`, `qms_partner_id`, `qms_product_id`, `length`, `width`, `total_points`, `score` (`digits="[16,1]"`), `points_pass`, `qms_accepted` (`optional="hide"`); `create="0"` |
| `qms_inspection_roll_report_action` | `ir.actions.act_window` | `name` *Roll Analysis*, `res_model` `qms.inspection.roll`, `view_mode` `pivot,list`, `view_ids` its pivot and list, `search_view_id` the roll search view, `domain` `[('scored', '=', True), ('inspection_id.state', 'in', ('waiting', 'success', 'failed')), ('inspection_id.qms_roll_inspection', '=', True)]` |
| `qms_inspection_shade_report_view_pivot` | pivot on `qms.inspection.roll` | `string="Shade Analysis"`, `sample="1"`; row `dye_lot`; col `shade_band`; no measure, so it opens on the count of rolls — the band distribution; the three ΔE averages are offered as measures |
| `qms_inspection_shade_report_view_list` | list | `inspection_id`, `qms_inspection_date`, `lot_id`, `dye_lot`, `qms_partner_id`, `delta_e`, `delta_e_length`, `delta_e_width` (each `digits="[16,2]"`), `shade_pass`, `shade_band`; `create="0"` |
| `qms_inspection_shade_report_action` | `ir.actions.act_window` | `name` *Shade Analysis*, `res_model` `qms.inspection.roll`, `view_mode` `pivot,list`, `view_ids` its pivot and list, `search_view_id` the roll search view, `domain` `[('inspection_id.state', 'in', ('waiting', 'success', 'failed')), ('inspection_id.qms_roll_inspection', '=', True)]` — banded-only rolls included |
| `qms_inspection_point_report_view_search` | search on `qms.inspection.point` | fields `defect_code_id`, `qms_product_id`, `qms_partner_id`, `qms_dye_lot`; a date filter on `qms_inspection_date`; group-bys: defect code, partner, fabric, dye lot, month (`qms_inspection_date:month`) |
| `qms_inspection_point_report_view_pivot` | pivot | `string="Fabric Defect Analysis"`, `sample="1"`; row `defect_code_id`; measure `points` |
| `qms_inspection_point_report_view_list` | list | `roll_id`, `qms_dye_lot`, `qms_partner_id`, `qms_inspection_date`, `position`, `defect_code_id`, `points` (`sum="Total"`); `create="0"` |
| `qms_inspection_point_report_action` | `ir.actions.act_window` | `name` *Fabric Defect Analysis*, `res_model` `qms.inspection.point`, `view_mode` `pivot,list`, `view_ids` its pivot and list, `search_view_id` its search view, `domain` `[('roll_id.inspection_id.state', 'in', ('waiting', 'success', 'failed')), ('roll_id.inspection_id.qms_roll_inspection', '=', True)]` |

**Roll search filters:** `failed_rolls` — *Failed rolls*, `[('passed', '=', False)]`;
`out_of_tolerance` — *Shade out of tolerance*, `[('shade_pass', '=', False)]`; `unbanded` — *No band*,
`[('shade_band', '=', False)]`; separator; `delta_e_measured` — *ΔE measured*, `[('delta_e', '!=', 0)]`;
`delta_e_length_measured` — *Head–tail measured*, `[('delta_e_length', '!=', 0)]`;
`delta_e_width_measured` — *Side–centre–side measured*, `[('delta_e_width', '!=', 0)]` (D12); separator;
a date filter on `qms_inspection_date`. **Group-bys:** partner
(`qms_partner_id`), fabric (`qms_product_id`), dye lot (`dye_lot`), band (`shade_band`), lot (`lot_id`),
month (`qms_inspection_date:month`).

## Menus — `views/qms_quality_report_menus.xml`

Loaded last, after the actions it points to.

| XML id | Parent | Name | Sequence | Action | Groups |
|---|---|---|---|---|---|
| `menu_qms_quality_report` | `quality_control_oca.qc_menu` | Reporting | 30 | — | `quality_control_oca.group_quality_control_manager` |
| `menu_qc_inspection_report` | `menu_qms_quality_report` | Inspection Analysis | 10 | `qc_inspection_report_action` | — |
| `menu_qc_inspection_line_report` | `menu_qms_quality_report` | Defect Analysis | 20 | `qc_inspection_line_report_action` | — |
| `menu_qms_inspection_roll_report` | `menu_qms_quality_report` | Roll Analysis | 30 | `qms_inspection_roll_report_action` | — (step 2) |
| `menu_qms_inspection_shade_report` | `menu_qms_quality_report` | Shade Analysis | 40 | `qms_inspection_shade_report_action` | — (step 2) |
| `menu_qms_inspection_point_report` | `menu_qms_quality_report` | Fabric Defect Analysis | 50 | `qms_inspection_point_report_action` | — (step 2) |

## Tests — `tests/test_qms_quality_report.py`

`TestQualityReport(TransactionCase)`, `@tagged("post_install", "-at_install")`: the fixtures create
products, a production order and work centres. Codes use `unique_code_prefix()`.

Fixtures: a quality group with a leaf code *Torn*; a `qc.test` with two qualitative questions whose
failing answers carry *Torn*, and an OK answer each; a roll test (`qms_roll_inspection`) with one
such question; a product; two work centres. `_inspection(test=None, production=None, state="ready")`
creates an inspection on the production order when one is given — `object_id`
`mrp.production,<id>`, since the bridge sets `production_id` from `object_id` only
(`quality_control_mrp_oca/models/qc_inspection.py:18-25`) and the product then comes from the order —
and on the product otherwise; its lines prepared from the test, both answered OK; then writes its
state. `_fail(line, qty=0.0)` answers a line with the failing answer and sets `qms_qty_failed`.

| Test | Asserts |
|---|---|
| `test_line_defects_entered` | a failed line with a quantity failed of 3 counts 3 defects |
| `test_line_defects_at_least_one` | a failed line with no quantity counts 1 (design D12) |
| `test_line_defects_passing_ignored` | a passing line with a quantity failed of 2 counts 0; failing it then counts 2 — the `success` dependency |
| `test_inspection_defects_sum` | lines counting 3 and 1 give the inspection 4; raising the first line's quantity to 5 gives 6 — the dependency through the lines |
| `test_defect_free_follows_success` | 100 with every line passing; 0 once one fails |
| `test_workcenter_single` | an inspection on a production order whose two work orders use one work centre carries it |
| `test_workcenter_several_or_none` | with a work order on a second work centre added, the work centre empties — the dependency through the work orders; an inspection without a production order has none |
| `test_related_dimensions_group` | `_read_group` on lines by `qms_partner_id`, `qms_workcenter_id`, `qms_test_category_id` and `qms_inspection_date:month`, and on inspections by `qms_partner_id`, returns without error — grouping by non-stored related fields (D3) |
| `test_inspection_action_domain` | the action's domain, evaluated, names exactly `INSPECTION_DONE_STATES` (D2); searched with it, inspections in *waiting*, *success* and *failed* are found, one in *ready* and a roll inspection in *success* are not |
| `test_defect_action_domain` | searched with the Defect Analysis domain, a failed line of a *failed* inspection is found; a passing line of it, and a failed line of a *ready* inspection, are not |
| `test_menu_for_managers` | the *Reporting* menu's groups are exactly the quality-control manager group |

The production order is created without a bill of materials and its work orders directly, with
`name`, `workcenter_id`, `product_uom_id` and `production_id` — the fields `mrp.workorder` requires
(`mrp/models/mrp_workorder.py:30-42`).

**Checked in the UI, as role-matrix users, not admin:** *Quality Control → Reporting* shown to a
quality-control manager and not to a quality-control user; as that manager, without MRP or Inventory
rights: Inspection Analysis opening on *First inspections*, its pivot by checkpoint and month with the
four measures, a draft inspection and a roll inspection absent even with the filter removed, grouping
by partner, work centre, lot and checkpoint category, the search by product and partner; Defect
Analysis's Pareto by defect code and severity, a *No defect code* group, grouping by month.

## Tests — `tests/test_qms_fabric_report.py` (step 2)

`TestFabricReport(FabricInspectionCase)`, `@tagged("post_install", "-at_install")`, on the fixtures
and helpers of `odoo.addons.qms_fabric_inspection.tests.common` — the roll test with a limit of 28
and a cap of 4, lots of the [Dye lot]-[Roll] form, `_inspect` and `_roll`.

| Test | Asserts |
|---|---|
| `test_accepted_follows_points_pass` | a scored roll within the limit carries 100; adding entries past the limit makes it 0 — the `points_pass` dependency |
| `test_aggregators` | `qms_accepted`, `score`, `delta_e`, `delta_e_length` and `delta_e_width` aggregate by average, and `score` keeps its compute and storage — the re-declaration merged, not replaced (D9) |
| `test_roll_action_domain` | the Roll Analysis domain, evaluated, carries `INSPECTION_DONE_STATES`; searched with it, a scored roll of a confirmed roll inspection is found, an unscored one, one of a *ready* inspection and one of an inspection switched to the plain test and confirmed are not |
| `test_shade_action_domain` | the Shade Analysis domain finds the unscored roll of the confirmed inspection too, and not the other two |
| `test_point_action_domain` | the Fabric Defect Analysis domain finds an entry of a confirmed roll inspection and not one of a *ready* inspection |
| `test_related_dimensions_group` | `_read_group` on rolls by `qms_partner_id`, `qms_product_id`, `qms_inspection_date:month`, and on point entries by those and `qms_dye_lot`, returns without error (D3) |
| `test_menus_under_reporting` | the three menus have the *Reporting* menu as parent, so the manager group gates them |

**Checked in the UI, as a quality-control manager without Inventory rights:** the three menus under
*Reporting*; Roll Analysis by partner and month with acceptance and score averaged; Shade Analysis
opening on the band distribution by dye lot, ΔE averages as measures, a banded-only roll counted, and
the averages changing when *ΔE measured* is applied; Fabric
Defect Analysis by defect code with points summed; grouping by lot; a roll inspection switched to a
plain test absent from all three.

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Reports on what inspections find, the same way at every checkpoint: Inspection Analysis gives pieces inspected, defects and defective pieces — DHU, defective % and FTR as paired sums — and the share of defect-free inspections, by checkpoint, product, work centre, partner and period; Defect Analysis gives the defect Pareto by code and severity Step 2 adds a fabric section over the roll inspections: roll acceptance and score, shade and band, and the fabric defect Pareto |
| `readme/USAGE.md` | Both analyses are under *Quality Control → Reporting*, for quality-control managers, and read finished inspections only — *waiting*, *success*, *failed*. DHU is defects ÷ pieces inspected × 100, defective % is defective pieces ÷ pieces inspected, FTR is (pieces inspected − defective pieces) ÷ pieces inspected: put the two sums side by side in the pivot. A failed check with no quantity counts one defect. Re-inspections are filtered out by default; fabric roll inspections are left out of Inspection Analysis and read in the fabric section. A *No defect code* group in Defect Analysis is a checklist answer or question missing its code Step 2 adds the fabric section: **Roll Analysis** averages roll acceptance and score over scored rolls, by partner, fabric and dye lot; **Shade Analysis** counts rolls by dye lot and band, with average ΔE as measures, banded-only rolls included — apply *ΔE measured* (or *Head–tail measured*, *Side–centre–side measured*) when reading a ΔE average, since an unread value counts as 0; the band distribution reads all rolls; **Fabric Defect Analysis** sums points and counts entries by defect code. All three read confirmed roll inspections only |
