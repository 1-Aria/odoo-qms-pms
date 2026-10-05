# Fabric Inspection — Design

Oct 5, 2026 · @Peter

Roll-level analyses on fabric receipt inspections — a point system such as the 4-point system, and
shade control — as **configurable analysis shapes** rather than fixed fields. A module of its own,
`qms_fabric_inspection` (working name), depending on `qms_quality_control` and
`quality_control_stock_oca`. Referenced from `docs/QMS Quality Reporting — Design.md` §8.1.

## 1. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| F1 | **A roll is accepted or rejected by a recognised standard.** | Each roll's defects are scored, the score is normalised, and the roll passes or fails against a limit |
| F2 | **Shade is controlled before cutting.** | Each roll's colour is measured against the standard and across the roll, and the roll carries a shade band that cutting can read |
| F3 | **Analyses are configured, not coded.** | A new point system or a new set of shade readings is created as records, within the two shapes of §4 |
| F4 | **Fabric quality is evidence per supplier and dye lot.** | Scores, defects and bands can be reported by supplier, fabric, dye lot and roll |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| The *scored defect list* shape, configured as the 4-point system | In | F1 |
| The *readings grid* shape, configured as the site's shade analysis | In | F2 |
| Analyses switched on per test, beside ordinary questions | In | A fabric test also asks weight, width, hand |
| The inspection's verdict including the analyses | In | One result per roll |
| Dye lot and shade band on the lot | In | F2, F4; cutting reads the band |
| User-defined fields and formulas (a form builder) | Out | §4.3 |
| Reporting views | Out | They belong to the QM report; §8 lists what it reads |
| Rolls as packages within a lot | Out | §2 |

## 2. The roll and the dye lot

Checked against the running code and database on 2026-10-05.

| Fact | Consequence |
|---|---|
| Rolls are received as **lots**, one per roll, named after the supplier's lot (`JJD1015-1`, `JJD1015-2`) | The roll is a lot. A workaround — Odoo has no unit below the lot — but a sufficient one |
| Odoo's packages (`stock.quant.package`), the closest thing to a handling unit, are enabled but unused; `quality_control_stock_oca` knows nothing of packages | Rolls as packages inside a dye-lot lot would read better, but would need inspection per package, written from scratch, and package discipline across the warehouse. Not pursued |
| A receipt trigger with **`inspection_per_lot`** (`quality_control_stock_oca/models/qc_trigger.py:14`) creates one inspection per move line, with its `lot_id` and quantity (`stock_move.py:68-77`) | **One inspection = one roll**, natively. Its `picking_id` gives the supplier |
| The dye lot exists only inside the lot's name, and as a field created by hand on this instance, `x_dye_lot` (Char, manual) | Rolls of one dye lot are expected to share a shade, so banding and reporting group by it. The module declares its own field (§5.3); a manual field exists only in this database, so code and tests cannot rely on it |
| An inspection's `success` is a stored compute over its question lines (`quality_control_oca/models/qc_inspection.py:18-21, 83-87`); `action_confirm` and `action_approve` turn it into *success*, *waiting* or *failed* (`:145-172`) | The analyses join the verdict by extending that compute; the approval flow is unchanged |

## 3. Questions stay, analyses are sections

An inspection line answers **one question with one value** and carries one verdict — and in this
project's modules one defect code and one failed quantity, which the QM report's *Defect Analysis*
reads. A point system is a list of scored defects normalised over the roll; a shade analysis is a set
of readings and a band. Making them new question types would make the line polymorphic, and every
reader of lines — OCA's verdict (`qc_inspection.py:271-285`), its views, the defect-code snapshot,
`qms_qty_failed`, the report — would branch on the type.

So the line is left alone. **An analysis is a section of the inspection with rows of its own**,
shown when the inspection's test has that analysis configured:

```
Inspection — roll JJD1015-2  (test: Fabric check)
├─ Questions (OCA lines, unchanged)
│    Weight 182 g/m²  ✓     Width 58"  ✓     Hand feel: OK  ✓
├─ Point system: 4-point
│    Length inspected 120 yd · width 58"
│    Slub      @ 12 yd    2"   → 1 pt
│    Hole      @ 40 yd         → 4 pts
│    Shading   @ 88 yd    7"   → 3 pts
│    8 pts → 4.1 pts / 100 yd²   (limit 28)  ✓
└─ Readings: Shade
     ΔE vs standard                0.8   (max 1.0)  ✓
     Grade, head / middle / tail   4–5 / 4–5 / 4  (min 4)  ✓
     Shade band: B   → written to the lot
Result: success — every question ✓ and every configured analysis ✓
```

A fabric test can still carry ordinary questions beside the analyses: they are separate sections.

## 4. Two configurable shapes

The shapes are code; everything that makes one analysis differ from another is configuration.
A manager creates *4-point (yd)*, *4-point (m)* or *10-point* as records and assigns one to a test.

### 4.1 Scored defect list

Entries of (defect, measured size) scored by a table, summed, normalised over the roll, and checked
against a limit.

| Configuration | Notes |
|---|---|
| Name, active | |
| Defect codes offered | A catalog profile or defect group from `qms_catalog`, so the entries use the same codes as the rest of the system and feed a Pareto |
| Score rows | Size from, size to, points — e.g. up to 3" = 1, 3"–6" = 2, 6"–9" = 3, over 9" = 4 |
| Fixed scores per code | A code scored the same whatever its size — e.g. a hole is always 4 |
| Size unit | inch or cm, for the entries |
| Normalisation | a fixed choice: per 100 square yards, per 100 square metres, per 100 linear yards / metres. The formula of each is code, e.g. 100 yd²: points × 3600 ÷ (yards inspected × width in inches) |
| Cap per unit of length | optional: the 4-point rule that one linear yard scores at most 4 |
| Limit | the maximum normalised score for a roll to pass |

4-point (ASTM D5430) is one configuration: the length classes above, holes at 4, per 100 yd², cap 4
per linear yard, and the buyer's limit — commonly 28 to 40.

Other point systems — the 10-point system, a points-per-piece audit — are other configurations of
the same shape.

### 4.2 Readings grid

Measurements of configured measures at configured positions, each against a tolerance, and
optionally a band for the roll.

| Configuration | Notes |
|---|---|
| Name, active | |
| Positions | ordered, e.g. head / middle / tail, or left / centre / right, or one position *Standard* |
| Measures | per measure: a name, numeric or grade, and its tolerance (a maximum for ΔE, a minimum grade for the grey scale); which positions it is read at |
| Band | whether the roll is assigned a shade band, and the band vocabulary |

The site's shade analysis is one configuration: ΔE against the approved standard (maximum, e.g. 1.0),
grey-scale grades along the roll (minimum, e.g. 4), and a band. Within-roll grading is included from
the start, so the readings can be used when wanted without changing the structure. The exact
readings are to be confirmed against the fabric team's practice (§9).

Other measurement grids — width or weight across the roll, shrinkage at positions — are other
configurations.

### 4.3 Why not a form builder

User-defined fields and formulas would make analyses fully open, at a cost of a different order:
key/value storage, a formula language evaluated safely, validation of what users configure, views
built at run time. The pivot cannot group or total key/value rows without a SQL view per
configuration, and a wrong formula would silently decide acceptance — where evidence matters most.
The two shapes cover point systems and measurements at positions, which is most of textile and
garment inspection; a single extra value with a tolerance is already an ordinary OCA question; a
single extra attribute is a manual field. A genuinely new shape is a design question, and so code.

## 5. Data model

Model names are working names, fixed in the module's spec.

### 5.1 Configuration

| Model | Content |
|---|---|
| `qms.point.system` | §4.1: name, active, defect profile, size unit, normalisation, cap, limit |
| `qms.point.system.rule` | score rows: size from, size to, points; or a defect code with fixed points |
| `qms.reading.grid` | §4.2: name, active, band on/off, band vocabulary |
| `qms.reading.grid.position` | ordered positions |
| `qms.reading.grid.measure` | name, numeric or grade, tolerance, positions read |
| `qc.test` | `qms_point_system_id`, `qms_reading_grid_id`: a test has an analysis when the field is set; empty means none |

### 5.2 On the inspection

| Model / field | Content |
|---|---|
| `qc.inspection`: roll length, roll width | entered by the inspector, in the point system's units |
| `qc.inspection`: point system snapshot | normalisation, cap, limit, units copied from the test's point system when the test is set |
| `qc.inspection`: total points, normalised score, points pass | computed from the entries and the snapshot |
| `qms.inspection.point.entry` | inspection, defect code, measured size, position on the roll, **points** — scored when the entry is made and stored |
| `qms.inspection.reading` | inspection, position, measure, value, tolerance (copied), within tolerance — **pre-created** from the grid when the test is set, as OCA pre-creates question lines from the test (`set_test`, `qc_inspection.py:177`) |
| `qc.inspection`: shade band | chosen by the inspector from the grid's vocabulary |
| `qc.inspection`: readings pass | all readings within tolerance |

**Definitions are snapshotted onto the inspection,** as an SLA record snapshots its rule: an entry's
points are scored when it is made, the normalisation and limit are copied when the test is set, and
a reading copies its tolerance. Editing a point system or a grid changes the inspections made
afterwards, never the past ones — the evidence rule of `maintenance_sla` (its design §9) and of the
QM report's defect snapshot.

### 5.3 On the lot

| Field | Content |
|---|---|
| `stock.lot` dye lot | Char: the supplier's dye lot the roll belongs to |
| `stock.lot` shade band | the band of the roll's latest finished inspection with a readings grid, written when the inspection is confirmed or approved |

**Migration from `x_dye_lot`:** after installing the module, copy `x_dye_lot` into the new field once,
then delete the manual field, so the instance carries one dye lot, not two.

## 6. Verdict and flow

- **`success`** becomes: every question line succeeds, **and** the points pass when a point system is
  configured, **and** the readings pass when a grid is configured. The override of
  `_compute_success` restates OCA's dependencies (`inspection_lines.success`) beside the analyses' — the
  most derived method's `@api.depends` is the one applied. The band never decides the verdict.
- **Completeness at confirmation:** confirming an inspection with a point system requires roll length
  and width; with a grid, every reading. Checked before OCA's own checks in `action_confirm`.
- **The approval flow is OCA's,** unchanged: a failing roll goes to *waiting supervisor approval*, and
  approval decides *success* or *failed* (`qc_inspection.py:145-172`).

## 7. Decisions

| # | Decision |
|---|---|
| D1 | **One inspection per roll,** through lots and `inspection_per_lot`; packages not pursued (§2) |
| D2 | **Analyses are inspection sections with their own rows;** question lines and the line-based reporting are untouched (§3) |
| D3 | **Two parameterised shapes, no form builder** (§4) |
| D4 | **An analysis is switched on by setting it on the test;** one point system and one grid per test at most, and both may be set |
| D5 | **Definitions are snapshotted** onto the inspection (§5.2) |
| D6 | **The verdict includes the analyses;** the band is recorded, never judged (§6) |
| D7 | **The module declares the dye lot,** and the instance migrates `x_dye_lot` into it (§5.3) |
| D8 | **The shade band lives on the lot,** where cutting will read it |

## 8. What reporting reads

The fabric grain is separate from the garment grain of the QM report: DHU does not apply to fabric,
and points per 100 yd² does not apply to garments.

| Question | Source |
|---|---|
| Roll acceptance %, by supplier, fabric, dye lot | the inspection's points pass, grouped by the receipt's partner, `product_id`, the lot's dye lot |
| Average score | the normalised score, averaged |
| Fabric defect Pareto | point entries: points and counts by defect code |
| Shade results | readings: ΔE by supplier and dye lot; out-of-tolerance readings by position |
| Band distribution | lots by dye lot and band |

These are added to the QM report once this module exists (its design §8.1).

## 9. Open questions

- **The shade readings themselves** — which positions, which measures (ΔE formula: CMC, CIE2000),
  the tolerances, the band vocabulary — confirmed with the fabric team before the grid is
  configured.
- **Manual override of points:** whether an inspector may correct an entry's points against the
  table — e.g. a defect judged worse than its length — or the table always decides.
- **Limits per buyer:** the 4-point limit is often set by the buyer. v1 holds one limit per point
  system; one system per buyer is the configuration answer until a per-partner limit is needed.
- **Units:** whether fabric is received in yards or metres, and widths in inches or centimetres —
  settled per point system.
- **Band at confirmation or approval:** a failing roll waits for approval; whether its band is written
  to the lot at confirmation, or only once approved.

## 10. Prerequisites

- Rolls received as lots, one per roll (in place).
- The fabric receipt trigger set with `inspection_per_lot`.
- Fabric defect codes in a catalog profile, for the point system to offer.
- After install, the migration of `x_dye_lot` (§5.3).
