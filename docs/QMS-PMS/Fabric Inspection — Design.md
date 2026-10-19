# Fabric Inspection — Design

Oct 5, 2026 · @Peter · Revised Oct 5, 2026

Roll-level fabric inspection at receipt — a point system such as the 4-point system, and shade
control — in a module of its own, `qms_fabric_inspection` (working name), depending on
`qms_quality_control` and `quality_control_stock_oca`. Referenced from
`docs/QMS Quality Reporting — Design.md` §8.1.

**Revision.** The first version made each roll its own inspection and offered two configurable
analysis shapes, a scored defect list and a readings grid. Review against the source and the
fabric workflow replaced both: **one inspection per receipt line, with the rolls as rows inside
it**, and fixed fields in place of the configurable shapes. §2 and §4 give the reasons; §10 lists
what changed.

## 1. Objectives

| ID | Objective | Achieved when |
|---|---|---|
| F1 | **A roll is accepted or rejected by a recognised standard.** | Each scored roll's points are capped, normalised to 100 m² and checked against a limit |
| F2 | **Shade is controlled before cutting.** | Each roll's shade is measured against the standard, along its length and across its width, and the roll carries a shade band that cutting reads with its dye lot |
| F3 | **Inspection follows the floor's practice.** | A sample of rolls can be scored, every roll can be banded, and a shipment's defects reach one nonconformity |
| F4 | **Fabric quality is evidence per supplier and dye lot.** | Scores, defects and bands can be reported by supplier, fabric, dye lot and roll |

### Scope

| Capability | v1 | Reason |
|---|---|---|
| Rolls as rows of the receipt line's inspection | In | F3; §2 |
| 4-point scoring: entries of position, defect code and points; cap per metre; score per 100 m²; limit | In | F1 |
| Shade per roll: ΔE against the standard, head–tail and side–centre–side; the band | In | F2 |
| Roll inspection switched on per test, beside ordinary questions | In | A fabric test also asks weight, width, hand |
| The inspection's verdict including the rolls | In | One result per receipt line |
| Dye lot and shade band on the lot | In | F2, F4; cutting reads them |
| Populate Defect from point entries | In | F3; §6 |
| Configurable analysis shapes (scoring tables, reading grids) | Out | §4 |
| A sampling rule enforced by the system | Out | Which rolls are scored is the inspector's choice |
| Shipment acceptance on the average score | Out | §7, D6 |
| Reporting views | Out | They belong to the QM report; §8 lists what it reads |

## 2. Rolls, lots and the inspection

Checked against the running code and database on 2026-10-05.

| Fact | Consequence |
|---|---|
| Rolls are received as **lots**, one per roll, named **`[Dye lot]-[Roll]`** (`JJD1015-1`, `JJD1015-2`) — the dye lot being the supplier's lot number on the packing list | **The roll is a lot.** Odoo has no unit below the lot; cutting consumes lots, so a band on the lot reaches cutting and an MO keeps per-roll traceability |
| Odoo's packages (`stock.quant.package`) are enabled but unused, and `quality_control_stock_oca` knows nothing of them | Packages would not replace lots: banding and cutting still need one record per roll. Not pursued |
| The dye lot exists only inside the lot's name | The module derives it from the name (§5.3). The manual field `x_dye_lot` held test data only and is deleted, not migrated |
| A receipt trigger with `inspection_per_lot` creates one inspection per move line, with its lot and quantity (`quality_control_stock_oca/models/stock_move.py:67-80`) | **Rejected as the inspection grain.** Every roll would raise an inspection, so sampling means cancelling most of them by hand; a nonconformity raised from one would see one roll, never the shipment; and shade sorting compares rolls with each other, which a one-roll inspection cannot hold |
| Without `inspection_per_lot`, the trigger creates **one inspection per stock move** — one fabric on one receipt — with the move as `object_id` and the receipt as `picking_id` (`quality_control_stock_oca/models/qc_inspection.py:34-40`) | **One inspection = one receipt line.** Its rolls are the lots of the move's lines, and its `picking_id` gives the supplier |
| The *after* timing fires at validation (`quality_control_stock_oca/models/stock_picking.py:80-88`), when the receipt's lots exist; *before* fires at confirmation, before lots are entered | The fabric trigger uses *after* |
| The inspection's `lot_id` is a stored compute taking the **first** lot of the move's lines (`quality_control_stock_oca/models/qc_inspection.py:42-57`) | On a receipt-line inspection it names one roll among many. The module hides it on roll inspections; the rolls section is the truth |
| `test` is read-only on the inspection form (`quality_control_oca/views/qc_inspection_view.xml:79`); it is set by `set_test` (trigger path, `qc_inspection.py:177`) or by the *Set test* wizard, which bypasses `set_test` and writes `test` directly (`wizard/qc_test_wizard.py`) | Anything copied from the test is a stored compute depending on `test` alone, which covers both paths with no hook into either |
| An inspection's `success` is a stored compute over its question lines (`quality_control_oca/models/qc_inspection.py:18-21`); `action_confirm` sends a failing inspection to *waiting* and `action_approve` resolves it into *success* or *failed* (`:145-172`) — approval cannot turn a failing inspection into a pass | The rolls join the verdict by extending that compute (§6) |
| Every fabric product on this instance uses **m²** as its unit | The point system is metric: positions in metres, widths in centimetres, scores per 100 m² |

## 3. Rolls are a section of the inspection

An inspection line answers **one question with one value** and carries one verdict — and in this
project's modules one defect code and one failed quantity, which the QM report's *Defect Analysis*
reads. A roll is a different grain: several rolls per inspection, each with its own measurements,
defect entries and band. Making rolls into question lines would make the line polymorphic, and every
reader of lines — OCA's verdict (`qc_inspection.py:271-285`), its views, the defect-code compute,
`qms_qty_failed`, the report — would branch on the type.

So the line is left alone. **The rolls are a section of the inspection with rows of their own**,
shown when the inspection's test inspects rolls:

```
Inspection — receipt WH/IN/00042, Polyester double knit 190 GSM   (test: Fabric check)
├─ Questions (OCA lines, unchanged)
│    Weight 188 g/m²  ✓     Hand feel: OK  ✓
├─ Rolls                 limit 28 pts/100 m² · cap 4/m · ΔE std ≤ 1.0 · head–tail ≤ 0.8 · side–centre ≤ 0.8
│    Roll         Dye lot   Length  Width   Points  Score   ΔE std  H–T   S–C–S  Band  Pass
│    JJD1015-1    JJD1015   110 m   150 cm  9       5.5     0.6     0.3   0.2    A     ✓
│    JJD1015-2    JJD1015   —       —       —       —       0.8     0.4   0.3    A     ✓   (banded, not scored)
│    JJD1015-3    JJD1015   108 m   150 cm  52      32.1    1.4     0.5   0.3    B     ✗
│      └─ entries: Slub @ 12 m → 1 · Hole @ 40 m → 4 · Shading @ 41–55 m → 4 per metre …
Result: waiting — JJD1015-3 fails its points and its ΔE
```

A fabric test can still carry ordinary questions beside the rolls: they are separate sections.

## 4. Fixed fields, not configurable shapes

The first version built two configurable shapes: a scoring table that turned measured defect sizes
into points, and a readings grid of measures at positions. Neither survives the floor's practice.

- **Points are judged, not computed.** The inspector reads the defect's size class by eye and enters
  1–4 points at a position on the roll, as the 4-point system is practised. A size-to-points table
  would ask for a measurement nobody takes. The table and its model go; what stays configurable is
  the limit and the cap per metre, on the test.
- **Shade is four facts per roll,** read on the spectrophotometer: ΔE against the approved standard,
  ΔE head–tail along the length (*ending*), ΔE side–centre–side across the width (*listing*), and
  the band from shade sorting. Within-roll shading is a comparison between positions, not a value at
  one, so it is recorded as the two standard comparisons. Four fields are cheaper to change than a
  framework of positions and measures.

A buyer with a different limit gets a test of its own. A genuinely new kind of analysis — a
10-point system, width or weight across the roll — is a design question, and so code.

**Why not a form builder** still holds: user-defined fields and formulas need key/value storage, a
safe formula language and views built at run time; the pivot cannot group key/value rows; and a
wrong formula would silently decide acceptance — where evidence matters most.

## 5. Data model

Model and field names are working names, fixed in the module's spec.

### 5.1 Configuration — on `qc.test`

| Field | Content |
|---|---|
| `qms_roll_inspection` | Boolean: the test inspects rolls, so its inspections show the rolls section |
| `qms_points_limit` | maximum score, in points per 100 m², for a scored roll to pass |
| `qms_points_cap` | maximum points per metre of roll; default 4, the 4-point rule; 0 for no cap |
| `qms_delta_e_max` | maximum ΔE against the standard; 0 when not judged |
| `qms_delta_e_length_max` | maximum ΔE head–tail; 0 when not judged |
| `qms_delta_e_width_max` | maximum ΔE side–centre–side; 0 when not judged |

The ΔE formula — CMC 2:1 is the textile norm, CIE2000 the alternative — is set on the instrument;
the system stores the value it reports.

### 5.2 On the inspection

| Model / field | Content |
|---|---|
| `qc.inspection`: the settings above, as snapshots | stored computes depending on `test` alone, so they are copied when the test is set and never follow a later edit of the test |
| `qc.inspection`: `qms_roll_ids` | the rolls |
| `qc.inspection`: `qms_show_all_codes` | widens the point entries' defect-code dropdown past the product's catalog profiles, as the nonconformity's switch does (plan §7.6) |
| `qms.inspection.roll` | inspection, **lot** (required, of the inspection's product), dye lot (related, from the lot), length (m), width (cm), total points, score, points pass, ΔE against the standard, ΔE head–tail, ΔE side–centre–side, band, **pass** |
| `qms.inspection.point` | roll, position (whole metres from the roll's start), defect code, points (1–4) |

**Scored or not.** A roll is *scored* when it has a length. Its total points are the sum over metres
of the lesser of the cap and that metre's points — a running defect is entered once per metre it
covers, and the cap stops one metre scoring more than 4. Its score is
`total points × 10000 ÷ (length m × width cm)`, points per 100 m². An unscored roll — banded but not
point-inspected, as in a sample — has no score and no points verdict.

**A roll passes** when, of the checks that apply to it, none fails: its score is within the limit when
it is scored; each of its three ΔE values is within its maximum when one is set. An unmeasured ΔE
reads 0.0 and passes — *not measured* and *perfect*
cannot be told apart in a Float, the same residue as OCA's unmeasured quantitative line.

**Defect codes** on point entries: leaf codes of the quality domain, filtered by the inspection
product's resolved catalog profiles (`qms_effective_profile_ids`) and widened by the switch above or
when no profile resolves — the advisory pattern of plan §7.6 and D7.

**Definitions are snapshotted onto the inspection,** as an SLA record snapshots its rule: editing a
test's limits changes the inspections made afterwards, never the past ones.

**Load rolls** — a button on a roll inspection before confirmation: adds one roll row for each lot on
the inspection's stock move that has no row yet. Rows can still be added and removed by hand.

### 5.3 On the lot

| Field | Content |
|---|---|
| `stock.lot.qms_dye_lot` | Char, stored compute, editable: the lot's name up to its last `-`; empty when the name has none. Editable so a lot that breaks the convention can be corrected by hand; a later rename of the lot recomputes it |
| `stock.lot.qms_shade_band` | the band of the lot's roll row in its latest inspection in `INSPECTION_DONE_STATES` (`qms_quality_control/models/mgmtsystem_nonconformity.py:11`) — confirmed, whatever the verdict, since the band describes the roll's colour, not its acceptance. Read-only: a band is corrected on the inspection |

**The band** is assigned by whoever does the shade sorting, which covers every roll — a swatch from
each, read together — while 4-point scoring covers a sample. It is a Char on the roll row accepting
either of two conventions, normalised to upper case and refused in any other format:

| Convention | Format | Meaning |
|---|---|---|
| Letters | one letter, `A`–`Z` | groups **within one dye lot**, `A` closest to the approved standard; `A` in one dye lot has nothing to do with `A` in another |
| 555 | three digits `1`–`9`, e.g. `455` | lightness, chroma and hue against the approved standard, `5` on standard; comparable across dye lots |

Cutting reads **(dye lot, band)** together, which is safe under both. Which 555 codes may share a lay
is a cutting tolerance, outside the system.

## 6. Verdict and flow

- **`success`** becomes: every question line succeeds **and** every roll passes. The override of
  `_compute_success` adds the rolls' `pass` to the dependencies; Odoo merges the `@api.depends` of
  every override along the inheritance chain (`odoo/odoo/fields.py:557-588`, `resolve_mro`), so OCA's
  own dependencies need not be restated. The band never decides the verdict.
- **One failing roll fails the inspection.** OCA's approval cannot override a failing verdict, so the
  inspection ends *failed*, which the QM report reads as *defects found* (its D6). Which rolls are
  returned is decided on the nonconformity (plan D12); roll acceptance is reported from the roll rows.
- **Completeness at confirmation:** a roll with point entries requires its length and width. Checked
  before OCA's own checks in `action_confirm`.
- **Populate Defect** on a nonconformity raised from the inspection also adds **one item per distinct
  defect code across the point entries**, with the number of entries as `qty_affected` — *Slub ×14,
  Hole ×3* for the shipment. It needs a small refactor in `qms_quality_control`: the item values are
  built by an overridable method, which this module extends.
- **The approval flow is OCA's,** unchanged.

## 7. Decisions

| # | Decision |
|---|---|
| D1 | **One inspection per receipt line, rolls as rows inside it;** lots stay one per roll; `inspection_per_lot` and packages not used (§2) |
| D2 | **Rolls are an inspection section with their own rows;** question lines and the line-based reporting are untouched (§3) |
| D3 | **Fixed fields, no configurable shapes, no form builder;** points entered by the inspector, limits on the test (§4) |
| D4 | **Roll inspection is switched on by a flag on the test,** beside ordinary questions |
| D5 | **The test's settings are snapshotted** onto the inspection (§5.2) |
| D6 | **The verdict is strict:** every roll must pass. Acceptance on the shipment's average score is deferred |
| D7 | **The dye lot is derived from the lot name,** by the `[Dye lot]-[Roll]` convention, and editable (§5.3) |
| D8 | **The shade band lives on the lot,** read with the dye lot, written from the latest confirmed inspection |
| D9 | **Sampling is the inspector's choice:** unscored rolls carry no points verdict; nothing enforces a rate. Practice is around 10% of rolls, every dye lot represented, more scored when the sample fails — all of it by filling in more rows |
| D10 | **Shade is three ΔE values and a band;** the band accepts letters or 555 codes (§5.3) |

## 8. What reporting reads

The fabric grain is separate from the garment grain of the QM report: DHU does not apply to fabric,
and points per 100 m² does not apply to garments.

| Question | Source |
|---|---|
| Roll acceptance %, by supplier, fabric, dye lot | scored roll rows' points pass, grouped by the inspection's receipt partner, product, and the lot's dye lot |
| Average score | the scored rolls' score, averaged |
| Fabric defect Pareto | point entries: counts and points by defect code |
| Shade results | roll rows: ΔE by supplier and dye lot; rolls out of tolerance |
| Band distribution | lots by dye lot and band |

**The QM report must exclude roll inspections** from *Inspection Analysis*: their `success` reflects
the rolls, so they would mix fabric verdicts into the garment figures. Filtered by the test's
`qms_roll_inspection`. The QM report depends on this module and carries these analyses as its
fabric section (its design §8.1, D10).

## 9. Open questions

- ~~**Within-roll shading on the instrument**~~ — **settled 2026-10-06:** head–tail and
  side–centre–side are read on the spectrophotometer, so all three shade values are ΔE with a
  maximum, as §5.1 has them.
- **Sampling practice:** the rate the team follows and how a failed sample is extended. Nothing in
  the system depends on it (D9).
- **Limits per buyer:** one test per buyer until a per-partner limit is needed.

## 10. Changes from the first version

| First version | Revised | Why |
|---|---|---|
| One inspection per roll, through `inspection_per_lot` | One inspection per receipt line, rolls as rows | Sampling, the nonconformity's view of the shipment, and shade sorting (§2) |
| Two configurable shapes: `qms.point.system` with score rows, and `qms.reading.grid` with positions and measures | Settings on `qc.test`; points entered directly; three ΔE fields and a band per roll | Points are judged by eye; within-roll shading is two standard comparisons, not a grid (§4) |
| Imperial units, chosen per point system | Metric | Fabric is received in m² and measured in metres |
| Points scored from a size table, with a manual-override question | Points entered | The question disappears with the table |
| Readings pre-created in `set_test` | No pre-creation; settings snapshotted by stored computes on `test` | The *Set test* wizard bypasses `set_test` |
| Dye lot as a Char declared by the module, migrated from `x_dye_lot` | Derived from the lot name; `x_dye_lot` deleted | The `[Dye lot]-[Roll]` convention; `x_dye_lot` held test data only |
| "The most derived method's `@api.depends` is the one applied" | Dependencies merge along the inheritance chain | `odoo/odoo/fields.py:557-588` |
| Band written at confirmation or approval — open | At confirmation, from `INSPECTION_DONE_STATES` | The band describes colour, not acceptance |
| A band vocabulary configured on the grid | A Char accepting letters or 555 codes | Both conventions are in use; one validated field covers them |
| No Populate Defect from point entries | One item per distinct code, counted | The shipment-level nonconformity should see the roll defects |

## 11. Prerequisites

- Rolls received as lots, one per roll, named `[Dye lot]-[Roll]` (in place).
- The fabric receipt trigger with the *after* timing and **without** `inspection_per_lot`.
- Fabric defect codes in a catalog profile on the fabric products, for the point entries to offer.
- The manual field `x_dye_lot` deleted.
