# QMS Quality Reporting — Design

Oct 4, 2026 · @Peter

The quality-side counterpart of `maintenance_sla`'s *SLA Analysis*: reporting on what inspections
find, in a module of its own, `qms_quality_report` (working name), depending on
`qms_quality_control` and `qms_fabric_inspection`.

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
| Capture of pieces inspected, defective pieces, re-inspection | In (in `qms_quality_control`) | The metrics' denominators and filters do not exist today (§3) |
| Defect code and severity frozen on the inspection line | In (in `qms_quality_control`) | A Pareto must group by them, and must not change when a checklist is edited |
| Work centre from the production order | In | Q2 |
| Fabric section: roll acceptance, points per 100 m², fabric defect Pareto, shade, bands | In, §8.1 | `qms_fabric_inspection` is built first, so the data exists when this module is built |
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

Checked against the running code and database on 2026-10-04.

| Fact | Consequence |
|---|---|
| An inspection carries `test`, `product_id`, `qty`, `state`, `success`, `date`, `date_done`, `user`, `company_id` | The inspection is the natural row of Inspection Analysis |
| `production_id` is stored on the inspection and its lines (`quality_control_mrp_oca/models/qc_inspection.py:41-52`); `picking_id` and `lot_id` too (`quality_control_stock_oca/models/qc_inspection.py:12-19, 91-95`) | Order, receipt, supplier (the receipt's partner) and lot are groupable today. The report module depends on both bridges |
| **`qty` is the lot size**, not what was checked: the order's `product_qty` (`quality_control_mrp_oca/models/qc_inspection.py:15`) or the move's quantity (`quality_control_stock_oca/models/qc_inspection.py:79-84`) | A 50-piece check of a 1,000-piece order would make DHU twenty times too good. Pieces inspected must be its own field |
| **`success` means zero failed lines** (`quality_control_oca/models/qc_inspection.py:19-21`; a line's verdict at `:271-285`) | OCA's "pass" is "defect-free", not the garment notion of within tolerance. Reported under that name |
| `state`: plan, draft, ready, waiting, success, failed, canceled (`qc_inspection.py:70-82`) | Only *success* and *failed* are finished inspections; only they count |
| A line carries `qms_qty_failed` (stored) and `qms_defect_code_id` (**not stored**, a live compute from the checklist) | Defects can be summed but not grouped by code; and an old inspection shows today's checklist codes |
| A defect code carries `default_severity_id` (`qms_nonconformity/models/qms_defect_code.py:11`) | Severity is available for the Pareto, through the code |
| A line counts **defects**; one garment can carry several | Defective pieces — and so defective % and FTR — are not derivable from the lines. They must be entered |
| `mrp.production.workcenter_id` is not stored (`mrp/models/mrp_production.py:80`); the work centre lives on work orders | The line is derived from the order's work orders |
| 1,837 production orders, 1,820 without work orders; the 17 with work orders use one work centre each. 17 inspections, all test data | Derivation works as soon as production runs with work orders, which is planned. Real figures come later |

## 4. Structure

Two analyses on existing models, as *SLA Analysis* is on its evidence: no report model.

| Analysis | Row | Answers |
|---|---|---|
| **Inspection Analysis** | one finished inspection | How much was checked, how much was defective, how many defects — per checkpoint, style, order, line, supplier, lot, inspector, period |
| **Defect Analysis** | one failed inspection line | Which defects, how many, how severe — the same slices, and the Pareto |

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
| `qc.inspection.line` | `qms_defect_code_id` | Many2one, **stored**, indexed | Today a live compute. Stored, it **depends on the line's own answer only** — `success`, `question_type`, `qualitative_value`, `test_line` — not on the codes configured on the checklist, so it is read once when the line is answered and frozen. With the checklist's codes among its dependencies, editing a checklist would recompute every historical line and rewrite the Pareto backwards: the anti-pattern the SLA design excluded for its evidence. Populate Defect reads the field and works unchanged |
| `qc.inspection.line` | `qms_severity_id` | Many2one, stored | The code's `default_severity_id`, frozen the same way, for the same reason |
| `qc.inspection` | `qms_qty_inspected` | Float | *Pieces inspected*; defaults to `qty`, so a full inspection needs no input; corrected when the inspector samples |
| `qc.inspection` | `qms_qty_defective` | Float | *Defective pieces*: garments with at least one defect, entered by the inspector. Not more than pieces inspected |
| `qc.inspection` | `qms_reinspection` | Boolean | *Re-inspection*: a check of reworked pieces. Excluded from the headline metrics, so reworked pieces are not counted twice and FTR stays first-time |

The doc of `qms_quality_control` currently explains why the defect code is not stored; that
paragraph is replaced by the snapshot's reasoning.

### 5.2 In `qms_quality_report` — reporting

| Model | Field | Type | Notes |
|---|---|---|---|
| `qc.inspection` | `qms_qty_defects` | Float, stored compute | Sum of the lines' `qms_qty_failed`: DHU's numerator on the inspection row |
| `qc.inspection` | `qms_workcenter_id` | Many2one, stored compute | The work centre of the production order's work orders when they all use one; empty otherwise, and empty without an order (§7, D4) |
| `qc.inspection` | `qms_defect_free` | Float, `aggregator="avg"` | 100 for *success*, 0 for *failed*, empty otherwise: averaged, the share of defect-free inspections — the `on_time` pattern of `maintenance_sla`. NULL and 0 differ here, so it is written and tested as that module's lesson requires (`addons/CLAUDE.md`, ORM) |
| `qc.inspection.line` | `qms_inspection_date`, `qms_workcenter_id`, `qms_test_id`, `qms_reinspection`, `qms_inspection_state` | related to the inspection, stored | So Defect Analysis can be grouped and filtered as Inspection Analysis is. They are attributes of the inspection, not of the moment the line was answered, so following the inspection is correct |

Views: a pivot and a list for each analysis, a search view each with the filters of §6, an action
each, and a menu for quality-control managers.

## 6. Metrics

All headline metrics read **finished, first inspections**: state *success* or *failed*, not
re-inspection. Both are default filters.

*Inspection Analysis* also excludes **roll inspections** (the test's `qms_roll_inspection`, from
`qms_fabric_inspection`) by default: their `success` reflects the rolls and their `qty` is the
receipt line's area, so they would mix fabric verdicts into the garment figures. Fabric is read in its
own section (§8.1). *Defect Analysis* keeps the failed question lines of fabric tests — weight, width,
hand — since those are defects found at receipt and attributed to the supplier like any other.

| Metric | Definition | In the pivot |
|---|---|---|
| **DHU** | defects ÷ pieces inspected × 100 | `qms_qty_defects` and `qms_qty_inspected`, side by side |
| **Defective %** | defective pieces ÷ pieces inspected | `qms_qty_defective` and `qms_qty_inspected`, side by side |
| **FTR** | (pieces inspected − defective pieces) ÷ pieces inspected | the same two sums |
| **Defect-free inspections %** | share of inspections with no failed line | average of `qms_defect_free` |
| **Defect Pareto** | defects by code, largest first | Defect Analysis: sum of `qms_qty_failed`, grouped by `qms_defect_code_id`, split by `qms_severity_id` |

Odoo's pivot aggregates each column on its own and cannot divide one sum by another, so DHU,
defective % and FTR are read from two sums per group. A ratio column needs an SQL-view report;
it is added if one of these becomes the number read daily.

A failed line whose question or answer carries no defect code shows in the Pareto as its own *no
code* group, never hidden: it is a configuration gap, and the report should make it visible.

## 7. Decisions

| # | Decision |
|---|---|
| D1 | **No checkpoint or profile model.** Checkpoints are OCA trigger lines on product categories; the report groups by test (§2) |
| D2 | **Defects counted on inspection lines,** not on nonconformity items (§4) |
| D3 | **Capture fields live in `qms_quality_control`;** the report module adds only what serves reporting (§5) |
| D4 | **Work centre derived, never entered** (option B). From the production order's work orders, when they all use one work centre. A routing with several work centres per order (cutting → sewing → finishing) leaves it empty; the known extension is a *quality line* flag on the work centre choosing which one an inspection is charged to |
| D5 | **The defect code and its severity are snapshots** on the line, read when the line is answered |
| D6 | **OCA's `success` is reported as *defect-free*,** not as *passed*. Lot acceptance in the garment sense is AQL's, out of scope |
| D7 | **Pieces inspected defaults to `qty`;** defective pieces and the re-inspection flag are entered |
| D8 | **Ratios as paired sums** in v1 (§6) |
| D9 | **Access:** the analyses are for quality-control managers; role design across QM is plan O7 |
| D10 | **The report depends on `qms_fabric_inspection`** and carries the fabric section in v1; roll inspections are excluded from Inspection Analysis by default (§6, §8.1) |

## 8. Waiting and future

The report is built after `qms_fabric_inspection` and after its prerequisite in
`qms_quality_control` (§5.1). Nothing else blocks it.

### 8.1 The fabric section

Roll-level fabric inspection is designed in **`docs/Fabric Inspection — Design.md`**: one inspection
per receipt line, with the rolls as rows of their own inside it — each with its 4-point entries, its
score per 100 m², its shade readings and its band — beside the question lines rather than inside
them. The question lines this report reads are untouched by that module.

The fabric section reads those rows (that note's §8): roll acceptance % over the scored rolls, the
average score, a fabric defect Pareto from the point entries, shade results by supplier and dye lot,
and the band distribution by dye lot. Rolls that were banded but not scored — the rest of a sample —
count in the shade and band analyses and not in roll acceptance. It is a separate grain — DHU does
not apply to fabric, nor points per 100 m² to garments — so §5 is unchanged; §6 gains only the
default exclusion of roll inspections from Inspection Analysis.

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

## 9. Preconditions and open questions

- **Capture pace.** Before relying on inline figures, time one real inline round on a tablet with
  the current inspection form. If entry cannot keep up, inspectors will record on paper and
  transcribe later, and the report will show entry times and thin data where the floor is busiest.
  The MES may change how inline data is captured altogether.
- **Configuration the report assumes:** one test per checkpoint; trigger lines on product
  categories; defect codes on the checklist's questions and answers, each with a default severity.
- **Menu placement** under the Quality Control app, and the exact group, are settled in the
  module's spec.
- **Defective pieces never exceed pieces inspected:** a constraint, or a warning only — settled in
  the spec.

## 10. References

| Source | Used for |
|---|---|
| `quality_control_oca` 18.0 (read from source) | Inspection, line, test, trigger lines, states, verdicts |
| `quality_control_mrp_oca`, `quality_control_stock_oca` 18.0 | `production_id`, `picking_id`, `lot_id`, and how `qty` is filled |
| `qms_quality_control`, `qms_nonconformity`, `qms_catalog` | Defect codes on checklists and lines, `qms_qty_failed`, default severity |
| `maintenance_sla` | The pattern: analyses on the evidence itself, a 100/0 average for a share, NULL and 0 kept apart |
| Apparel quality practice | DHU, defective %, FTR, Pareto; the fabric 4-point system (ASTM D5430); AQL |
