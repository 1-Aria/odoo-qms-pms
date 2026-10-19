# QMS Quality Reporting — Design

Oct 4, 2026 · @Peter · Revised Oct 6, 2026

The quality-side counterpart of `maintenance_sla`'s *SLA Analysis*: reporting on what inspections
find, in a module of its own, `qms_quality_report` (working name), depending on
`qms_quality_control` and `qms_fabric_inspection`.

**Revision.** Reviewed against the code once `qms_fabric_inspection` was built. The defect count no
longer sums quantities typed on passing lines and no longer loses failed lines without a quantity;
pieces inspected survives OCA rewriting `qty`; *waiting* counts as finished; "finished" and the
fabric exclusion are action domains rather than filters; related fields are not stored; the fabric
section names its fields. §11 lists what changed.

## 1. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| Q1 | **Defects are measured the same way at every checkpoint.** A defect is a property of the product, whatever stage found it | Every failed inspection line counts, with its defect code and severity, wherever it was raised |
| Q2 | **Production lines can be judged on their output.** | Defects found by production-side checks are attributed to the work centre that made the goods |
| Q3 | **Suppliers can be judged on what they deliver.** | Defects found at receipt are attributed to the supplier and the lot |
| Q4 | **Improvement is focused.** | A Pareto of defects by code and severity, per checkpoint, style, line or supplier, over time |

The headline metrics are those of apparel quality practice: **DHU** (defects per hundred units),
**defective %**, **First-Time-Right** (FTR), the share of defect-free inspections, and the defect
Pareto.

### Scope

| Capability | Status | Reason |
|---|---|---|
| Inspection Analysis and Defect Analysis on existing models | In | The core of Q1–Q4 |
| Capture of the sample size, defective pieces, re-inspection | In (in `qms_quality_control`) | The metrics' denominators and filters do not exist today (§3) |
| Defect code and severity frozen on the inspection line | In (in `qms_quality_control`) | A Pareto must group by them, and must not change when a checklist is edited |
| Work centre from the production order | In | Q2 |
| Fabric section: roll acceptance, points per 100 m², fabric defect Pareto, shade, bands | In, §8.1 | `qms_fabric_inspection` exists, so the data does |
| Operator and operation dimension | Out — possible future addition, §8.2 | Deferred; nothing in this design depends on it |
| AQL lot acceptance | Out | Its own design: sample plans and accept/reject numbers |
| A ratio column (DHU, FTR) in the pivot | Out for v1 | §6; an SQL-view report if it becomes necessary |

## 2. Checkpoints need no new concept

A checkpoint is **a test applied at a trigger**. OCA already models exactly that: a trigger line
(`qc.trigger.line`: `trigger`, `test`, `user`, `partners`, `timing`,
`quality_control_oca/models/qc_trigger_line.py:22-41`) hangs on a product, a product template or a
product category (`qc_trigger_product_line.py`, `qc_trigger_product_template_line.py`,
`qc_trigger_product_category_line.py`). A category's trigger lines are an inspection profile —
"this kind of product gets these checks at these points" — and every product in the category
inherits it. A profile model of our own would duplicate it.

The inspection does not record which trigger created it, but it records its `test` and its origin
(`production_id`, `picking_id`). With **one test per checkpoint** — *Fabric check*, *Bundle check*,
*Inline check*, *Finish check* — grouping by test is grouping by checkpoint, and OCA's
`qc.test.category` (`qc_test.py:29`) is available as a level above. The report reads checkpoints;
it does not depend on them: defects are measured the same way everywhere (Q1).

## 3. The data today

Checked against the running code and database on 2026-10-04, and again on 2026-10-06.

| Fact | Consequence |
|---|---|
| An inspection carries `test`, `product_id`, `qty`, `state`, `success`, `date`, `date_done`, `user`, `company_id` | The inspection is the natural row of Inspection Analysis |
| `production_id` is stored on the inspection and its lines (`quality_control_mrp_oca/models/qc_inspection.py:41-54`); `picking_id` and `lot_id` too (`quality_control_stock_oca/models/qc_inspection.py:12-19, 88-96`) | Order, receipt, supplier (the receipt's partner) and lot are reachable. The report module depends on both bridges |
| **`qty` is the lot size**, not what was checked: the order's `product_qty` (`quality_control_mrp_oca/models/qc_inspection.py:15`) or the move's quantity (`quality_control_stock_oca/models/qc_inspection.py:75-85`) | A 50-piece check of a 1,000-piece order would make DHU twenty times too good. The sample size must be its own field |
| **OCA rewrites `qty` after creation:** validating a picking calls `onchange_object_id()` on its existing inspections, which resets `qty` to the move's quantity (`quality_control_stock_oca/models/stock_picking.py:68-69`, `qc_inspection.py:70-73`); the per-lot path writes it after creating each inspection (`stock_move.py:71-76`) | Pieces inspected cannot be an editable copy of `qty` — a rewrite would overwrite the inspector's sample size — nor a default taken at creation, which goes stale (§5.1) |
| **`success` means zero failed lines** (`quality_control_oca/models/qc_inspection.py:18-21`; a line's verdict at `:271-285`, stored) | OCA's "pass" is "defect-free", not the garment notion of within tolerance. Reported under that name |
| `state`: plan, draft, ready, waiting, success, failed, canceled (`qc_inspection.py:70-82`). `action_confirm` sends a failing inspection to *waiting* until a supervisor approves it (`:145-172`) | **Finished means *waiting*, *success* or *failed*** — `INSPECTION_DONE_STATES` in `qms_quality_control`. Leaving out *waiting* would hide every failure not yet approved and show the passes alone |
| A line carries `qms_qty_failed`, a plain Float defaulting to 0.0 on **every** line, passing or failed (`qms_quality_control/models/qc_inspection_line.py:37`), and `qms_defect_code_id`, **not stored**, a live compute from the checklist | Summing `qms_qty_failed` counts quantities left on passing lines, and a failed line without a quantity counts nothing (§5.2). Defects cannot be grouped by code, and an old inspection shows today's checklist codes |
| A defect code carries `default_severity_id` (`qms_nonconformity/models/qms_defect_code.py:11`) | Severity is available for the Pareto, through the code |
| A line counts **defects**; one garment can carry several | Defective pieces — and so defective % and FTR — are not derivable from the lines. They must be entered |
| `mrp.production.workcenter_id` is not stored (`mrp/models/mrp_production.py:80`); the work centre lives on work orders | The line is derived from the order's work orders |
| **Odoo 18 groups by a non-stored related field,** joining in SQL (`odoo/odoo/models.py:2096-2097`), and the pivot offers it as a grouping (`odoo/odoo/fields.py:913-926`) | Dimensions borrowed from the inspection are declared as related fields and not stored (§5.2) |
| A computed Float stores `False` as 0.0 (`odoo/odoo/fields.py:1685-1689`) | A 100/0 share cannot hold "empty" as a compute; it does not need to, since the action's domain keeps only finished rows (§6) |
| Odoo validates the constraints of a stored computed field whenever it is recomputed (`odoo/odoo/models.py:5300-5305`) | A constraint on pieces inspected, which follows `qty`, would run inside picking validation. Rules on the capture fields are checked at confirmation instead (§5.1) |
| 1,837 production orders, 1,820 without work orders; the 17 with work orders use one work centre each. 17 inspections, all test data | Derivation works as soon as production runs with work orders, which is planned. Real figures come later |

## 4. Structure

Two analyses on existing models, as *SLA Analysis* is on its evidence: no report model.

| Analysis | Row | Answers |
|---|---|---|
| **Inspection Analysis** | one finished garment inspection | How much was checked, how much was defective, how many defects — per checkpoint, style, order, line, supplier, lot, inspector, period |
| **Defect Analysis** | one failed line of a finished inspection | Which defects, how many, how severe — the same slices, and the Pareto |

The fabric section adds its own analyses over the roll rows and point entries (§8.1).

**Attribution follows the checkpoint's origin** (Q2, Q3):

| Origin | Attributed to |
|---|---|
| Receipt (`picking_id`) — fabric, components | the supplier, the material, the lot |
| Production order (`production_id`) — triggers at confirmation (*Manufacturing*) and at completion (*Production done*) | the work centre |

Material defects found at receipt are not charged to a production team: the defects internal
process causes are found from the production line up to the packed product, and that is where the
work centre applies.

Nonconformities stay the escalation layer. Most inline and end-of-line defects are fixed on the spot
and never become one, so defects are counted on inspection lines, not on nonconformity items.

## 5. Data model

### 5.1 In `qms_quality_control` — capture

The fields an inspector fills belong to the capture module, so the inspection form asks for them
whether or not reporting is installed.

| Model | Field | Type | Notes |
|---|---|---|---|
| `qc.inspection.line` | `qms_defect_code_id` | Many2one, **stored**, indexed | Today a live compute. Stored, it **depends on the line's own answer only** — `success`, `question_type`, `qualitative_value` — not on the codes configured on the checklist, so it is read once when the line is answered and frozen. With the checklist's codes among its dependencies, editing a checklist would recompute every historical line and rewrite the Pareto backwards: the anti-pattern the SLA design excluded for its evidence. Populate Defect reads the field and works unchanged. **Not `test_line` either:** a question is a plain Many2one with `ondelete="set null"` (`quality_control_oca/models/qc_inspection.py:308`), so depending on it would wipe the codes of every line that asked a question someone deleted; it is set at creation and never changes otherwise, so leaving it out loses nothing (`qms_quality_control` step 7) |
| `qc.inspection.line` | `qms_severity_id` | Many2one, stored | The code's `default_severity_id`, frozen the same way, for the same reason |
| `qc.inspection` | `qms_qty_sampled` | Float | *Sample size*, entered when the inspector checks fewer pieces than the lot; empty for a full inspection |
| `qc.inspection` | `qms_qty_inspected` | Float, stored compute, read-only | *Pieces inspected*: the sample size when entered, otherwise `qty`. It follows OCA's rewrites of `qty` until someone samples, then keeps the sample (§3) |
| `qc.inspection` | `qms_qty_defective` | Float | *Defective pieces*: garments with at least one defect, entered by the inspector |
| `qc.inspection` | `qms_reinspection` | Boolean | *Re-inspection*: a check of reworked pieces, so reworked pieces are not counted twice and FTR stays first-time |

**Checked at confirmation:** defective pieces may not exceed pieces inspected. `action_confirm`
refuses it before OCA's own checks, as `qms_fabric_inspection` checks its rolls. Not
`@api.constrains`: Odoo validates a stored compute's constraints on every recompute (§3), so a
constraint involving pieces inspected would run when OCA rewrites `qty` during picking validation,
and a quality rule could block a receipt. The check guards every confirmed inspection, which is all
the report reads.

**The capture fields mean nothing on a roll inspection,** where the rolls carry their own figures.
`qms_fabric_inspection` hides them there, in a step of its own.

The doc of `qms_quality_control` currently explains why the defect code is not stored; that
paragraph is replaced by the snapshot's reasoning, and `test_code_follows_checklist_edit`, which
asserts the live behaviour, is inverted.

### 5.2 In `qms_quality_report` — reporting

| Model | Field | Type | Notes |
|---|---|---|---|
| `qc.inspection.line` | `qms_qty_defects` | Float, stored compute | *Defects*: on a failed line, `qms_qty_failed` when entered, otherwise **1**; on a passing line 0. A failed check is at least one defect (D12), and a quantity left on a passing line is ignored, as Populate Defect ignores it |
| `qc.inspection` | `qms_qty_defects` | Float, stored compute | The sum of the lines' `qms_qty_defects`: DHU's numerator on the inspection row |
| `qc.inspection` | `qms_workcenter_id` | Many2one, stored compute | The work centre of the production order's work orders when they all use one; empty otherwise, and empty without an order (D4) |
| `qc.inspection` | `qms_partner_id` | Many2one, related `picking_id.partner_id`, not stored | *Supplier*, for grouping (§3) |
| `qc.inspection` | `qms_defect_free` | Float, stored compute, `aggregator="avg"` | 100 when `success`, 0 otherwise; averaged over the finished rows the action keeps, the share of defect-free inspections — the 100/0 pattern of `maintenance_sla`'s `on_time` |
| `qc.inspection.line` | `qms_inspection_date`, `qms_workcenter_id`, `qms_partner_id`, `qms_test_id`, `qms_reinspection`, `qms_inspection_state`, `qms_roll_inspection` | related to the inspection, **not stored** | So Defect Analysis is grouped and filtered as Inspection Analysis is (§3). They are attributes of the inspection, not of the moment the line was answered, so following the inspection is correct |

Views: a pivot and a list for each analysis, a search view each, an action each with the domain of
§6, and a menu for quality-control managers.

## 6. Metrics

**"Finished" is part of each action's domain, not a default filter** (D14). A filter can be removed
in the search bar, and the 100/0 averages would then take in draft and ready inspections as zeros
and drop silently. The domain cannot be removed.

| Action | Domain | Default filter |
|---|---|---|
| Inspection Analysis | state in `INSPECTION_DONE_STATES`; not a roll inspection | first inspections — not re-inspection |
| Defect Analysis | the line failed (`success` false); its inspection's state in `INSPECTION_DONE_STATES` | first inspections |

Re-inspection stays a filter: including re-inspections is a legitimate view. The roll exclusion is a
domain: fabric has its own section (§8.1), and a roll inspection's `success` reflects the rolls and
its `qty` the receipt line's area, so it would mix fabric verdicts into the garment figures. *Defect
Analysis* keeps the failed question lines of fabric tests — weight, width, hand — since those are
defects found at receipt and attributed to the supplier like any other.

| Metric | Definition | In the pivot |
|---|---|---|
| **DHU** | defects ÷ pieces inspected × 100 | `qms_qty_defects` and `qms_qty_inspected`, side by side |
| **Defective %** | defective pieces ÷ pieces inspected | `qms_qty_defective` and `qms_qty_inspected`, side by side |
| **FTR** | (pieces inspected − defective pieces) ÷ pieces inspected | the same two sums |
| **Defect-free inspections %** | share of inspections with no failed line | average of `qms_defect_free` |
| **Defect Pareto** | defects by code, largest first | Defect Analysis: sum of the line's `qms_qty_defects`, grouped by `qms_defect_code_id`, split by `qms_severity_id` |

Odoo's pivot aggregates each column on its own and cannot divide one sum by another, so DHU,
defective % and FTR are read from two sums per group. A ratio column needs an SQL-view report;
it is added if one of these becomes the number read daily.

A failed line whose question or answer carries no defect code shows in the Pareto as its own *no
code* group, never hidden: it is a configuration gap, and the report should make it visible.

**A skipped measurement counts one defect.** `action_confirm` does not require a measurement on a
quantitative question, so an unmeasured one reads 0.0 and fails its minimum — the residue
`qms_quality_control` already documents. Under D12 it adds 1 to DHU. Accepted: OCA already records
the line as failed and sends the inspection to *waiting*, so the supervisor sees it at approval, and
the count follows OCA's own verdict. A check refusing confirmation cannot tell an unmeasured line from
a measured 0.0 in a Float; if inflated figures show in practice, the narrow form — 0.0 and out of
tolerance refuses confirmation — is a small addition to `qms_quality_control`.

## 7. Decisions

| # | Decision |
|---|---|
| D1 | **No checkpoint or profile model.** Checkpoints are OCA trigger lines on product categories; the report groups by test (§2) |
| D2 | **Defects counted on inspection lines,** not on nonconformity items (§4) |
| D3 | **Capture fields live in `qms_quality_control`;** the report module adds only what serves reporting (§5) |
| D4 | **Work centre derived, never entered.** From the production order's work orders, when they all use one work centre. A routing with several work centres per order (cutting → sewing → finishing) leaves it empty; the known extension is a *quality line* flag on the work centre choosing which one an inspection is charged to |
| D5 | **The defect code and its severity are snapshots** on the line, read when the line is answered |
| D6 | **OCA's `success` is reported as *defect-free*,** not as *passed*. Lot acceptance in the garment sense is AQL's, out of scope |
| D7 | **Pieces inspected is the sample size when entered, otherwise `qty`** — a stored compute over an entered `qms_qty_sampled`, so OCA's later rewrites of `qty` reach it until someone samples; defective pieces and the re-inspection flag are entered |
| D8 | **Ratios as paired sums** in v1 (§6) |
| D9 | **Access:** the analyses are for quality-control managers; role design across QM is plan O7 |
| D10 | **The report depends on `qms_fabric_inspection`** and carries the fabric section in v1 |
| D11 | **Finished means *waiting*, *success* or *failed*** — `INSPECTION_DONE_STATES` — so failures awaiting approval are counted |
| D12 | **A failed line is at least one defect:** its quantity when entered, otherwise 1; a passing line is none. Nothing is required of the inspector |
| D13 | **Dimensions borrowed from the inspection are related fields, not stored** (§3) — no copies to keep in step, and no rewrite of every line when an inspection changes state |
| D14 | **"Finished", the roll exclusion and `scored` are action domains,** which the user cannot remove; re-inspection is a default filter (§6, §8.1) |
| D15 | **Defective ≤ inspected is checked at confirmation,** not by a constraint that would run inside picking validation (§5.1) |

## 8. Waiting and future

The report is built after its prerequisite in `qms_quality_control` (§5.1). `qms_fabric_inspection`
exists. Nothing else blocks it.

### 8.1 The fabric section

Roll-level fabric inspection is built in `qms_fabric_inspection` (`docs/Fabric Inspection —
Design.md`, `docs/modules/qms_fabric_inspection.md`): one inspection per receipt line, with the rolls
as rows of their own beside the question lines. It is a separate grain — DHU does not apply to
fabric, nor points per 100 m² to garments.

| Source | Fields the section reads |
|---|---|
| `qms.inspection.roll` | `scored`, `score`, `points_pass`, `shade_pass`, `passed`, `dye_lot` (stored), `shade_band`, `delta_e`, `delta_e_length`, `delta_e_width`, `total_points` |
| `qms.inspection.point` | `defect_code_id`, `points` |

Added on them by this module:

| Model | Field | Type | Notes |
|---|---|---|---|
| `qms.inspection.roll` | `qms_accepted` | Float, stored compute, `aggregator="avg"` | 100 when `points_pass`, 0 otherwise; averaged over scored rolls, roll acceptance % |
| `qms.inspection.roll` | `qms_partner_id`, `qms_product_id`, `qms_inspection_date`, `qms_inspection_state` | related through `inspection_id`, not stored | supplier (`picking_id.partner_id`), fabric, date, state |
| `qms.inspection.point` | `qms_partner_id`, `qms_product_id`, `qms_inspection_date`, `qms_dye_lot` | related through `roll_id`, not stored | the same slices for the fabric defect Pareto |

| Analysis | Row | Domain | Answers |
|---|---|---|---|
| **Roll Analysis** | one scored roll of a finished roll inspection | `scored`; inspection state in `INSPECTION_DONE_STATES`; a roll inspection | roll acceptance % (average of `qms_accepted`), average score, by supplier, fabric, dye lot |
| **Shade Analysis** | one roll of a finished roll inspection | inspection state in `INSPECTION_DONE_STATES`; a roll inspection | average ΔE by supplier and dye lot, rolls out of tolerance (`shade_pass` false), band distribution by dye lot |
| **Fabric Defect Analysis** | one point entry of a finished roll inspection | the same | counts and points by defect code |

Rolls banded but not scored — the rest of a sample — count in Shade Analysis and not in Roll
Analysis. Leftover rolls on an inspection switched to a plain test are excluded by the roll-inspection
term, as `qms_fabric_inspection` excludes them from the verdict.

### 8.2 Operator and operation — a possible future addition

Attributing a defect to the operation and operator that caused it is standard in apparel quality
(the operation bulletin and its defect library), and is **deferred**: not part of this design, and
not a dependency of it.

The idea as stated, for whenever it is taken up: Odoo's operation (`mrp.routing.workcenter`) is
unique per bill of materials and work centre, so the same garment operation exists as unrelated
records across styles. An **operation template** — a shared operation library each BoM operation
refers to — would give the operation a stable identity, and assigning templates to defect groups
(catalog profiles) would link operation to defect, and through the work order's operator, operator
to defect. Community edition records who worked on a work order in its time logs
(`mrp.workcenter.productivity.user_id`, `mrp/models/mrp_workcenter.py:525`). It would build on the
MES / bundle system Peter plans for the production pipeline, which captures each operator's
operation through work orders.

If taken up, the report would gain operation and operator groupings; nothing in §5 or §6 depends
on them.

### 8.3 Other extensions

| Addition | Note |
|---|---|
| AQL lot acceptance | Sample plans, accept/reject numbers by severity; its own design |
| Ratio columns | An SQL-view report computing DHU, defective % and FTR per group (§6) |
| Quality line flag on work centres | When routings carry several work centres per order (D4) |
| Severity-weighted Pareto | Weights per severity, if a plain count turns out misleading |
| Skipped-measurement check | 0.0 and out of tolerance refuses confirmation, if D12 inflates figures in practice (§6) |

## 9. Preconditions and open questions

- **Capture pace.** Before relying on inline figures, time one real inline round on a tablet with
  the current inspection form. If entry cannot keep up, inspectors will record on paper and
  transcribe later, and the report will show entry times and thin data where the floor is busiest.
  The MES may change how inline data is captured altogether.
- **Configuration the report assumes:** one test per checkpoint; trigger lines on product
  categories; defect codes on the checklist's questions and answers, each with a default severity.
- **Menu placement** under the Quality Control app, and the exact group, are settled in the
  module's spec.

## 10. References

| Source | Used for |
|---|---|
| `quality_control_oca` 18.0 (read from source) | Inspection, line, test, trigger lines, states, verdicts |
| `quality_control_mrp_oca`, `quality_control_stock_oca` 18.0 | `production_id`, `picking_id`, `lot_id`, how `qty` is filled and rewritten |
| `qms_quality_control`, `qms_nonconformity`, `qms_catalog` | Defect codes on checklists and lines, `qms_qty_failed`, default severity, `INSPECTION_DONE_STATES` |
| `qms_fabric_inspection` | Roll rows, point entries, the roll-inspection flag, the confirmation-check pattern |
| `maintenance_sla` | The pattern: analyses on the evidence itself, a 100/0 average for a share |
| Odoo 18 core (`odoo/odoo/models.py`, `fields.py`) | Grouping by non-stored related fields, Float caching, constraints on recompute |
| Apparel quality practice | DHU, defective %, FTR, Pareto; the fabric 4-point system (ASTM D5430); AQL |

## 11. Changes from the first version

| First version | Revised | Why |
|---|---|---|
| DHU's numerator the sum of the lines' `qms_qty_failed` | A line's `qms_qty_defects`: its quantity when failed and entered, 1 when failed without one, 0 when passing; summed on the inspection | `qms_qty_failed` sits on every line, so passing lines' leftovers counted, and a failed line without a quantity vanished from DHU and the Pareto |
| `qms_qty_inspected` defaults to `qty` | `qms_qty_sampled` entered; `qms_qty_inspected` computed from it or `qty` | OCA rewrites `qty` after creation (§3) |
| Finished: *success* or *failed* | *waiting*, *success*, *failed* | Failures awaiting approval were hidden |
| Finished and the roll exclusion as default filters | Action domains; re-inspection stays a filter | A removed filter silently broke the 100/0 averages |
| `qms_defect_free` empty outside *success*/*failed*, written like `on_time` | A stored compute, 100/0 on `success` | A computed Float cannot store empty; the domain makes it unnecessary |
| Related fields on the line stored | Not stored | Odoo 18 groups by non-stored related fields |
| Defective ≤ inspected: a constraint or a warning, open | Checked at confirmation | A constraint would run inside picking validation |
| Fabric section described in outline | Its analyses, fields and domains (§8.1) | `qms_fabric_inspection` exists |
| — | The skipped-measurement residue stated (§6) | A consequence of D12 |
| The snapshot depends on `success`, `question_type`, `qualitative_value`, `test_line` | Without `test_line` — amended Oct 7, at `qms_quality_control` step 7 | Deleting a question would have wiped its lines' codes |
