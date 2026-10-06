# qms_fabric_inspection

Roll-level fabric inspection at receipt: the rolls of a receipt line as rows of its inspection,
4-point entries scored per 100 m², shade per roll, dye lot and shade band on the lot.
Design: `docs/Fabric Inspection — Design.md`. Plan: §8, §10 Phase 3.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Roll inspection settings on the test and their snapshot on the inspection; `qms.inspection.roll` and `qms.inspection.point`; capped total, score per 100 m², points verdict; the rolls in the inspection's `success`; completeness at confirmation; the Rolls page; the advisory defect-code filter; the inspection's `lot_id` hidden on roll inspections | done | 2026-10-06, three runs. First: `exit=255`, the view validator refused `domain="parent.defect_code_domain"` (D6, now `or []`). Second: installed, 3 of 19 tests failed: the plain test's default cap of 4, and the snapshot computed at first read rather than at the write (D1). Third: `-u`, `exit=0`, 19 tests, 0 failures; UI checked: the Rolls page and hidden lot on roll inspections only, the roll's lot dropdown limited to the product, the defect dropdown following the profile and *Show all catalog codes*, capped points and the failing-roll colour, confirmation to *waiting* and the refusal of an unmeasured roll, the page read-only once confirmed |
| 2 | Shade: three ΔE values and the band on the roll, the ΔE maxima on the test and in the snapshot, the ΔE checks in `passed`; `qms_dye_lot` and `qms_shade_band` on the lot, the roll's dye lot; the roll list made editable with a Points button; shared test fixtures in `tests/common.py` | done | 2026-10-06, one pass. `-u`, `exit=0`, 32 tests (13 new), 0 failures; UI checked: the three ΔE maxima on the test, the editable roll list taking lot, measurements, ΔE and band in the row, band normalisation and refusal, the Points button saving and opening the entries with the profile-filtered defect dropdown, the row refreshed on closing, the dialog read-only once confirmed, dye lot and band on the lot form and list, the lot list grouped by dye lot. Within-roll shading confirmed on the spectrophotometer the same day |
| 3 | Load rolls: a button on the Rolls page adding a row for each lot on the inspection's receipt line that has none | done | 2026-10-06, one pass. `-u`, `exit=0`, 37 tests (5 new), 0 failures; UI checked on a receipt-line inspection: the button above the list in *ready* only, one press listing every roll of the receipt line in receipt order with its dye lot, a second press notifying, rows already filled in kept |
| 4 | Populate Defect from point entries, on `qms_quality_control`'s item-values split (its step 5); the roll's name read as superuser for display | specced | |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §5.2: a roll is *scored* when it has a length | when it has a length **and** a width | The score divides by both. A roll with a length and no width would be scored with no score to judge; confirmation refuses it instead (`_qms_check_rolls`) |
| 2 | §5.1 says nothing of a limit left at 0 | 0 means *not judged*: a scored roll passes its points whatever its score | The same convention as the ΔE maxima (§5.1 there). A roll test saved before its limit is filled must not fail every roll with a single point |
| 3 | §5.2 says nothing of when rolls can be edited | the Rolls page is editable in *ready* only | It follows OCA's Questions page (`readonly="state != 'ready'"`, `quality_control_oca/views/qc_inspection_view.xml:95-97`): an inspection is worked in *ready*, and a confirmed one is evidence |
| 4 | §5.2 lists the dye lot on the roll | added in step 2, not step 1 | It is related to the lot's `qms_dye_lot`, which step 2 declares |
| 5 | §6: `success` requires every roll to pass | every roll to pass **when the inspection is a roll inspection** | `set_test` and the *Set test* wizard rebuild only `inspection_lines` (`qc_inspection.py:177-187`, `wizard/qc_test_wizard.py:23-27`), so rolls survive a change of test — reachable as Ready → Cancel → Draft → Set test. After a switch to a plain test the Rolls page is hidden, and a failing roll nobody can see would still fail the inspection. The rows stay and are ignored; switching back brings them into the verdict again |
| 6 | §5.2: positions are whole metres from the roll's start | the metre the defect lies in, counted from 1; required | An Integer left empty reads 0, so with metre 0 allowed an entry nobody positioned is capped together with every other unpositioned one — five 4-point holes would score 4. With 0 refused and the column NOT NULL, a missing position cannot be saved |

## Decisions

| # | Decision |
|---|---|
| D1 | **The snapshot is three stored computes depending on `test` alone.** `test` is read-only on the form (`quality_control_oca/views/qc_inspection_view.xml:79`) and reaches the inspection by a write in both paths — `set_test` writes it with the header (`qc_inspection.py:177-187`), the *Set test* wizard assigns it (`wizard/qc_test_wizard.py`). `write()` calls `modified(vals)` unconditionally (`odoo/odoo/models.py`, `write`), so the snapshot is recomputed even when the same test is written again. Reading the test's fields without depending on them is what freezes the values. **Frozen at computation, not at the write:** a stored compute is marked pending when `test` is written and runs at the next read or flush, so the test's values are copied then. Within one transaction an edit of the test between the two would be copied; across transactions the commit's flush has long since run. Only a test can hit the gap, and the test reads the snapshot first (failed run 2026-10-06) |
| D2 | **`_compute_success` is extended, not replaced:** `super()`, then a roll inspection is also required to have every roll `passed` (divergence 5). The decorator adds `qms_roll_inspection` and `qms_roll_ids.passed`; OCA's dependencies are merged in, not restated (`odoo/odoo/fields.py:557-588`, `resolve_mro`) |
| D3 | **Every value on the roll that reporting reads is stored:** total points, scored, score, points pass, passed. An unscored roll stores `score` as 0.0 — a Float cannot hold *no score* through the ORM — so anything averaging scores filters on `scored`. **The score is stored unrounded:** a Float with `digits` is rounded as it is assigned (`Float.convert_to_cache`, `odoo/odoo/fields.py:1685-1689`), so 28.02 would be stored as 28.0 and pass a limit of 28. The one-decimal display is set on the view, where it decides nothing |
| D4 | **A roll appears once per inspection,** by a SQL unique constraint on (inspection, lot). A duplicate row would count a roll twice in acceptance and in the Pareto: silently wrong data, which is the case that earns a constraint |
| D5 | **Points are 1–4 and positions are 1 or more,** by SQL CHECK, and both are required. A CHECK lets NULL through, so `required=True` (NOT NULL) is what refuses an entry with no position at all. `@api.constrains` does not run on a value left out of `create()` (`addons/CLAUDE.md`, ORM). `points` is required with no default, so the inspector chooses it |
| D6 | **The defect-code domain is computed once on the inspection** and handed down: the roll relates it, the point list reads `parent.defect_code_domain or []`. A point's own compute would have to reach two levels up through records that are still new in the dialog's onchange; one level is the case core's `parent.` supports. **A bare `parent.<field>` fails view validation:** the validator accepts a bare field name (`odoo/odoo/tools/view_validation.py:124-126`) or a domain expression — a list, `+`, `and`/`or`, `if`/`else` (`:76-121`) — and an attribute access falls through to the list branch and raises on `.elts` (`:105`; first install, 2026-10-06, `exit=255`). `or []` makes it a BoolOp (`:82-90`), whose `parent.` name is checked against the roll form, where `defect_code_domain` is present. The client evaluates it as an expression with `parent` the roll; the `[]` never applies, since the domain always carries the quality-leaf terms |
| D7 | **The roll's `lot_id` is restricted in the view to the inspection's product,** not by a constraint — a dropdown filter, as the checklist codes are (`qms_quality_control` doc, *The checklist domain*) |
| D8 | **Load rolls searches move lines; it never reads the move or the lot** (step 3). `stock.move` and `stock.lot` are readable by Inventory users only (`stock/security/ir.model.access.csv:14-16`), `stock.move.line` by every internal user (`:47`), and `quality_control_stock_oca` adds no access of its own. Searching lines by `move_id` takes the move's id from the inspection's `object_id` without reading it, and the lot ids come off the lines without reading a lot, so the button works for an inspector without Inventory rights and needs no `sudo()`. Picking a roll's lot by hand in the dialog does need that read — the dropdown searches `stock.lot` — which is a reason the button exists |
| D9 | **Rows in lot creation order** — the order the lots were entered on the receipt. Not by name, which sorts `-10` before `-2`; not by move line, whose `_order` puts packages first (`stock/models/stock_move_line.py:17`) |
| D10 | **Add-only.** Existing rows are never touched, so a roll already measured keeps its entries; a lot with a row is skipped. A row the inspector deleted comes back at the next press — accepted, as the button is pressed by hand and deleting the row again is one click |
| D12 | **ΔE maxima of 0 mean *not judged*** (step 2), as the points limit does (divergence 2). An unmeasured ΔE reads 0.0 and passes (design §5.2). The three values are stored unrounded and shown with two decimals in the views, for the reason of D3 |
| D13 | **The band is normalised and validated** (step 2): `create` and `write` strip it and upper-case it, and `@api.constrains("shade_band")` accepts one letter `A`–`Z` or three digits `1`–`9`, raising `ValidationError` otherwise (design §5.3). Empty is legal, so a constraint that runs only on written values is enough here |
| D14 | **The dye lot is derived from the lot name** (step 2): `name.rpartition("-")`, the part before the last `-`, or empty when there is none — `JJD1015-1` gives `JJD1015`, `A-B-12` gives `A-B`, `1111` gives nothing. Stored, editable; renaming the lot recomputes it over a hand-corrected value, accepted (design §5.3) |
| D15 | **The lot's band comes from its latest confirmed roll row with a band** (step 2): of the lot's rolls with a band, on a roll inspection in `INSPECTION_DONE_STATES`, the one on the highest inspection id, then roll id. A later confirmed inspection that left the band empty — a roll scored, not banded — keeps the earlier band. Stored and read-only; `compute_sudo` defaults to `store` (`odoo/odoo/fields.py:443`), so it is computed as superuser and an inspector without Inventory rights who confirms still updates the lot |
| D16 | **The roll's dye lot is a stored related field** (step 2), so rolls group by dye lot in reporting; `related_sudo` defaults to true, so it needs no Inventory rights either |
| D17 | **The roll list becomes editable, with a Points button** (step 2). Shade is entered for every roll, and a dialog per roll for a whole receipt line is too slow. Lot, measurements, ΔE values and band are typed in the row; the row's button opens the roll's point entries in a dialog — core's pattern for picking moves (`stock.move.action_show_details`, `stock/models/stock_move.py:847-866`). The o2m's inline form goes, replaced by a form view of its own; in it the point line's `parent` is the roll, so D6 is unchanged. The form is read-only outside *ready* through a related `inspection_state` |
| D11 | **Stock moves only.** The configured trigger makes the move the inspection's `object_id` (design §2); an inspection on a product, a picking or a lot loads nothing and gets the notification |
| D18 | **Point entries become one item per distinct defect code** (step 4, design §6), after the question-line items: the inspection's checklist first, its rolls after, numbered on together by `action_populate_defect`. Codes in order of first appearance — roll order, then position — so the list reads as the inspector entered it |
| D19 | **`qty_affected` is the number of entries** with that code, as the design's *Slub ×14* has it; the rolls they lie on go into the note, which is what a decision on returning rolls needs. Every entry counts, on passing rolls as on failing ones: a defect found is a defect, and the roll's verdict is on its own row |
| D20 | **Only a roll inspection's rolls count,** as in `success` and the lot's band (divergence 5). The notification `qms_quality_control` returns when nothing resolves is left as it is: its text names the checklist only, and a roll inspection with neither coded failures nor point entries is the case it describes |
| D21 | **The roll's name is read as superuser** (step 4). `_compute_display_name` reads `lot_id.sudo().display_name`, and the Points title, the confirmation error and the item note all read the roll's `display_name`. A non-stored compute runs as the user (`compute_sudo` follows `store`, `odoo/odoo/fields.py:443`), and `stock.lot` is readable by Inventory users only, so steps 1–3 raised `AccessError` for the inspector D8 supports as soon as a roll's name was shown outside a list: the Points dialog, the confirmation error. It is core's own rule for a Many2one label, which `web_read` takes as superuser (`odoo/addons/web/models/models.py:122-123`) — the lot name is a label, not a read of the lot |

## Folder structure

```
qms_fabric_inspection/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── qc_test.py
│   ├── qc_inspection.py
│   ├── qms_inspection_roll.py
│   ├── qms_inspection_point.py
│   ├── stock_lot.py                                    # 2
│   └── mgmtsystem_nonconformity.py                     # 4
├── security/ir.model.access.csv
├── views/
│   ├── qc_test_views.xml
│   ├── qc_inspection_views.xml
│   ├── qms_inspection_roll_views.xml                   # 2
│   └── stock_lot_views.xml                             # 2
├── tests/__init__.py, test_qms_fabric_inspection.py
│         common.py                                       # 2
│         test_qms_shade.py                               # 2
│         test_qms_load_rolls.py                          # 3
│         test_qms_populate_defect.py                     # 4
└── readme/ DESCRIPTION.md, USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Fabric Inspection` |
| `summary` | `Roll-level fabric inspection at receipt: 4-point scoring per roll within the receipt line's inspection` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `qms_quality_control`, `quality_control_stock_oca` |
| `data` | `security/ir.model.access.csv`, `views/qc_test_views.xml`, `views/qc_inspection_views.xml`, `views/qms_inspection_roll_views.xml` (step 2), `views/stock_lot_views.xml` (step 2) |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qc_test`, `from . import qms_inspection_point`, `from . import qms_inspection_roll`, `from . import qc_inspection`, `from . import stock_lot` (step 2), `from . import mgmtsystem_nonconformity` (step 4) |
| `tests/__init__.py` | `from . import test_qms_fabric_inspection`, `from . import test_qms_shade` (step 2), `from . import test_qms_load_rolls` (step 3), `from . import test_qms_populate_defect` (step 4) |

## Access — `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_qms_inspection_roll_user` | `model_qms_inspection_roll` | `quality_control_oca.group_quality_control_user` | 1 | 1 | 1 | 1 |
| `access_qms_inspection_point_user` | `model_qms_inspection_point` | `quality_control_oca.group_quality_control_user` | 1 | 1 | 1 | 1 |

The same rights OCA gives the inspection and its lines
(`quality_control_oca/security/ir.model.access.csv:2-3`): rolls and entries are parts of the
inspection and are worked by whoever works it. The manager group implies the user group. The test's
new fields need no row: `qc.test` is writable by the manager group already (`:5`).

## Models

### `qc.test` — `models/qc_test.py`

`_inherit = "qc.test"`

| Field | Type | Attributes |
|---|---|---|
| `qms_roll_inspection` | Boolean | `string="Roll Inspection"`, help: inspections from this test list the rolls of the receipt line, each scored by the 4-point system |
| `qms_points_limit` | Float | `string="Points Limit (per 100 m²)"`, help: the highest score a scored roll may have and pass; 0 means the score is not judged. If the buyer's standard gives the limit per 100 yd², multiply it by 1.196 |
| `qms_points_cap` | Integer | `string="Points Cap per Metre"`, `default=4`, help: the most points one metre of roll can score, 4 under the 4-point system; 0 means no cap |
| `qms_delta_e_max` | Float | step 2; `string="Max ΔE vs Standard"`, help: the largest colour difference from the approved standard a roll may have and pass, as the spectrophotometer reports it; 0 means not judged |
| `qms_delta_e_length_max` | Float | step 2; `string="Max ΔE Head–Tail"`, help: the largest colour difference between a roll's head and tail; 0 means not judged |
| `qms_delta_e_width_max` | Float | step 2; `string="Max ΔE Side–Centre–Side"`, help: the largest colour difference between a roll's sides and its centre; 0 means not judged |

### `qc.inspection` — `models/qc_inspection.py`

`_inherit = "qc.inspection"`

| Field | Type | Attributes |
|---|---|---|
| `qms_roll_inspection` | Boolean | `compute="_compute_qms_test_settings"`, `store=True`, `string="Roll Inspection"` |
| `qms_points_limit` | Float | same compute, `store=True`, `string="Points Limit (per 100 m²)"` |
| `qms_points_cap` | Integer | same compute, `store=True`, `string="Points Cap per Metre"` |
| `qms_delta_e_max`, `qms_delta_e_length_max`, `qms_delta_e_width_max` | Float | step 2; same compute, `store=True`, the test's strings |
| `qms_roll_ids` | One2many → `qms.inspection.roll` | inverse `inspection_id`, `string="Rolls"` |
| `qms_show_all_codes` | Boolean | `string="Show all catalog codes"`, `default=False`, help: offer every quality defect code on the point entries, instead of only those in the catalog profiles assigned to this product — the nonconformity's switch (`qms_nonconformity/models/mgmtsystem_nonconformity.py:44-49`) |
| `qms_defect_code_domain` | Binary | `compute="_compute_qms_defect_code_domain"`, not stored, `string="Defect Code Domain"` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_test_settings` | `@api.depends("test")` | the snapshot fields — three in step 1, six from step 2 — from `test`'s fields of the same name; `False` and zeros without a test (D1) |
| `_compute_success` | `@api.depends("qms_roll_inspection", "qms_roll_ids.passed")` | `super()`, then `success = success and (not qms_roll_inspection or all(qms_roll_ids.mapped("passed")))` (D2). No rolls, or not a roll inspection: OCA's verdict unchanged |
| `_compute_qms_defect_code_domain` | `@api.depends("product_id.qms_effective_profile_ids", "qms_show_all_codes")` | `CHECKLIST_DEFECT_CODE_DOMAIN` (imported from `odoo.addons.qms_quality_control.models.qc_test_question`); plus `("parent_id.profile_ids", "in", profiles.ids)` when the product resolves profiles and the switch is off — the three states of `qms_nonconformity`'s item domain (`qms_nonconformity_item.py:91-116`), with the quality-domain half the checklist codes carry |
| `action_confirm` | — | `self._qms_check_rolls()`, then `super()` |
| `_qms_check_rolls` | — | for each roll of each **roll** inspection — leftover rolls on a plain one are ignored, as in `success` (divergence 5): if it has point entries, a length or a width but not both a length and a width, raise `UserError`: `"Roll %(roll)s: enter both its length and width to score it, or remove its point entries."` with the roll's `display_name` (the lot's name until step 4, D21) |

**The check runs before OCA's** so a roll inspection with an incomplete roll fails on the roll, the
thing the inspector is looking at, and never reaches a state.

**The domain's quality half** — leaf codes of the `qm` or `both` domain — holds in every branch, as on
the checklists: a point entry is a quality finding, and a maintenance code has no place on it. The
profile term only narrows; the switch and a product with no profile both widen back to the quality
half, so the filter stays advisory (design §5.2, plan D7).

### `qc.inspection` — Load rolls (step 3)

Same file.

| Method | Behaviour |
|---|---|
| `_qms_lots_to_load` | `ensure_one`; when `object_id` is a `stock.move`, the lots of its move lines — `stock.move.line` searched by `move_id` and `lot_id != False` (D8) — in lot creation order (`sorted("id")`, D9), less the lots that already have a roll here (D10); otherwise an empty `stock.lot` recordset (D11) |
| `action_qms_load_rolls` | for each inspection, one roll per lot of `_qms_lots_to_load()`, created in one batched `create()` with only `inspection_id` and `lot_id`. If nothing was created at all, return the notification below; otherwise `True`, and the client reloads the form |

A lot on two move lines gives one roll: the lines' lots are a recordset, so a repeat collapses.

**Notification when nothing was loaded** — the pattern of Populate Defect in `qms_quality_control`:

| Key | Value |
|---|---|
| `type` | `"ir.actions.client"` |
| `tag` | `"display_notification"` |
| `params.type` | `"info"` |
| `params.title` | `"No rolls to load"` |
| `params.message` | `"Every lot on this receipt line already has a row. Rolls are loaded from the lots of the inspection's receipt line."` |

### `qms.inspection.roll` — `models/qms_inspection_roll.py`

`_name = "qms.inspection.roll"`, `_description = "Inspected Roll"`, `_order = "inspection_id, id"`

| Field | Type | Attributes |
|---|---|---|
| `inspection_id` | Many2one → `qc.inspection` | `required=True`, `ondelete="cascade"`, `index=True` |
| `lot_id` | Many2one → `stock.lot` | `string="Roll"`, `required=True`, `ondelete="restrict"`, `index=True` |
| `length` | Float | `string="Length (m)"` |
| `width` | Float | `string="Width (cm)"` |
| `point_ids` | One2many → `qms.inspection.point` | inverse `roll_id`, `string="Point Entries"` |
| `defect_code_domain` | Binary | `related="inspection_id.qms_defect_code_domain"` (D6) |
| `total_points` | Integer | `compute="_compute_total_points"`, `store=True`, `string="Points"` |
| `scored` | Boolean | `compute="_compute_scored"`, `store=True` |
| `score` | Float | `compute="_compute_score"`, `store=True`, `string="Score (per 100 m²)"`; no `digits` (D3) |
| `points_pass` | Boolean | `compute="_compute_points_pass"`, `store=True`, `string="Points Pass"` |
| `passed` | Boolean | `compute="_compute_passed"`, `store=True`, `string="Pass"` |
| `dye_lot` | Char | step 2; `related="lot_id.qms_dye_lot"`, `store=True`, `string="Dye Lot"` (D16) |
| `delta_e` | Float | step 2; `string="ΔE vs Standard"`, no `digits` (D12) |
| `delta_e_length` | Float | step 2; `string="ΔE Head–Tail"`, no `digits` |
| `delta_e_width` | Float | step 2; `string="ΔE Side–Centre–Side"`, no `digits` |
| `shade_pass` | Boolean | step 2; `compute="_compute_shade_pass"`, `store=True`, `string="Shade Pass"` |
| `shade_band` | Char | step 2; `string="Shade Band"`, help: the roll's group from shade sorting — one letter, A closest to the standard, meaningful within the dye lot; or a 555 code of three digits 1–9, lightness, chroma and hue against the standard |
| `inspection_state` | Selection | step 2; `related="inspection_id.state"`, not stored — read by the Points form (D17) |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_display_name` | `@api.depends("lot_id")` | the lot's display name, read through `lot_id.sudo()` from step 4 (D21) — the title of the roll's dialog, the name in the confirmation error and in the item note |
| `_compute_total_points` | `@api.depends("point_ids.points", "point_ids.position", "inspection_id.qms_points_cap")` | the entries' points summed per `position`; each metre counts at most `qms_points_cap` when it is above 0; the metres summed |
| `_compute_scored` | `@api.depends("length", "width")` | `length > 0 and width > 0` (divergence 1) |
| `_compute_score` | `@api.depends("scored", "total_points", "length", "width")` | `total_points * 10000 / (length * width)` when scored, else 0.0 (D3) |
| `_compute_points_pass` | `@api.depends("scored", "score", "inspection_id.qms_points_limit")` | true when not scored, when the limit is 0 (divergence 2), or when `score <= limit` |
| `_compute_passed` | `@api.depends("points_pass", "shade_pass")` | `points_pass and shade_pass` — step 1 read `points_pass` alone |
| `_compute_shade_pass` | `@api.depends("delta_e", "delta_e_length", "delta_e_width", "inspection_id.qms_delta_e_max", "inspection_id.qms_delta_e_length_max", "inspection_id.qms_delta_e_width_max")` | step 2; true when each of the three values is within its maximum, a maximum of 0 not judged (D12) |
| `create` | `@api.model_create_multi` | step 2; normalises `shade_band` in each values dict, then `super()` (D13) |
| `write` | — | step 2; normalises `shade_band` when present, then `super()` |
| `_check_shade_band` | `@api.constrains("shade_band")` | step 2; a non-empty band must match `^([A-Z]|[1-9]{3})$`, else `ValidationError`: `"Shade band %(band)s: use one letter (A, B, …) or a 555 code of three digits 1–9."` |
| `action_qms_open_points` | — | step 2; `ensure_one`; an `ir.actions.act_window` on this roll, `view_mode` `form`, `views` the Points form, `target` `new`, `res_id` the roll, `name` `"Points — %(roll)s"` with the roll's `display_name` (D17; the lot's name until step 4, D21) |

**Normalisation** is a module-level helper, `_normalise_band(value)`: `value.strip().upper()`, or
`False` when that leaves nothing — `" a "` becomes `A`, `"455"` stays, `"  "` becomes empty.

| SQL constraint | Definition | Message |
|---|---|---|
| `lot_unique_per_inspection` | `unique(inspection_id, lot_id)` | `A roll can appear only once in an inspection.` (D4) |
| `length_positive` | `check(length >= 0)` | `A roll's length cannot be negative.` |
| `width_positive` | `check(width >= 0)` | `A roll's width cannot be negative.` |

**The formula.** Area in m² is `length × width ÷ 100`, so points per 100 m² is
`points × 100 ÷ area = points × 10000 ÷ (length m × width cm)`. 9 points on 100 m × 150 cm is
150 m², 6.0 per 100 m².

**The cap counts metres, not entries.** Two entries of 3 and 2 at metre 10 count 4; an entry of 1 at
metre 11 counts 1; the roll scores 5. A running defect is entered once per metre it covers, and the
cap is what keeps one metre at 4.

### `mgmtsystem.nonconformity` — `models/mgmtsystem_nonconformity.py` (step 4)

`_inherit = "mgmtsystem.nonconformity"`. `qc_inspection_id` comes from
`mgmtsystem_nonconformity_quality_control_oca`; `_qms_defect_item_values` from `qms_quality_control`
(its step 5).

| Method | Behaviour |
|---|---|
| `_qms_defect_item_values` | `super()`, then — when `qc_inspection_id` is a roll inspection (D20) — one value dict per distinct defect code among the point entries of its rolls, appended in order of first appearance (D18) |

**Values for an item from point entries**

| Item field | Value |
|---|---|
| `nonconformity_id` | this nonconformity |
| `defect_code_id` | the code |
| `qty_affected` | the number of entries with that code (D19) |
| `note` | `"Point entries on rolls %(rolls)s"`, the `display_name` of each roll carrying the code, in roll order, comma-separated (D21) |
| `sequence` | not set: `action_populate_defect` numbers the whole list |
| `severity_id`, `object_part_id`, `cause_id` | not set, as for an item from a line |

The entries are read as `qms_roll_ids.point_ids`: rolls in their `_order`, each roll's entries in
theirs, which is the order D18 names.

### `stock.lot` — `models/stock_lot.py` (step 2)

`_inherit = "stock.lot"`

| Field | Type | Attributes |
|---|---|---|
| `qms_dye_lot` | Char | `compute="_compute_qms_dye_lot"`, `store=True`, `readonly=False`, `index=True`, `string="Dye Lot"`, help: the supplier's dye lot, taken from the lot name up to its last "-" by the [Dye lot]-[Roll] convention; correct it here when a name does not follow it |
| `qms_roll_ids` | One2many → `qms.inspection.roll` | inverse `lot_id`, `string="Inspected Rolls"` — the dependency path of the band; in no view |
| `qms_shade_band` | Char | `compute="_compute_qms_shade_band"`, `store=True`, `string="Shade Band"`, help: the band from this roll's latest confirmed fabric inspection; read with the dye lot |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_dye_lot` | `@api.depends("name")` | the part of `name` before its last `-`, or `False` (D14) |
| `_compute_qms_shade_band` | `@api.depends("qms_roll_ids.shade_band", "qms_roll_ids.inspection_id.state", "qms_roll_ids.inspection_id.qms_roll_inspection")` | the band of the latest qualifying roll, or `False` (D15); `INSPECTION_DONE_STATES` imported from `odoo.addons.qms_quality_control.models.mgmtsystem_nonconformity` |

On install both are computed for every existing lot: dye lots fill from the names, bands stay empty.

### `qms.inspection.point` — `models/qms_inspection_point.py`

`_name = "qms.inspection.point"`, `_description = "Point Entry"`, `_order = "roll_id, position, id"`

| Field | Type | Attributes |
|---|---|---|
| `roll_id` | Many2one → `qms.inspection.roll` | `required=True`, `ondelete="cascade"`, `index=True` |
| `position` | Integer | `string="Position (m)"`, `required=True`, help: the metre of the roll the defect lies in, 1 for the first metre, as read on the inspection machine |
| `defect_code_id` | Many2one → `qms.defect.code` | `string="Defect"`, `required=True`, `ondelete="restrict"` |
| `points` | Integer | `required=True`, help: 1 to 4, by the defect's size under the 4-point system — up to 7.5 cm 1, to 15 cm 2, to 23 cm 3, longer 4; a hole up to 2.5 cm 2, larger 4 |

| SQL constraint | Definition | Message |
|---|---|---|
| `points_range` | `check(points >= 1 and points <= 4)` | `Points must be between 1 and 4.` (D5) |
| `position_positive` | `check(position >= 1)` | `A position must be 1 or more: the metre the defect lies in.` |

`ondelete="restrict"` on the defect code, as on every other link to the catalog: a code in use is
archived, not deleted.

The points help carries the metric 4-point classes so the inspector sees them where the value is
typed; they are guidance, not a computation (design §4).

## Views — `views/qc_test_views.xml`

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `qc_test_form_view` | `quality_control_oca.qc_test_form_view` | `//sheet/group/group` after | `<group string="Roll Inspection" name="qms_roll_inspection_settings">` holding `qms_roll_inspection`, then `qms_points_limit`, `qms_points_cap` and — step 2 — `qms_delta_e_max`, `qms_delta_e_length_max`, `qms_delta_e_width_max`, each `invisible="not qms_roll_inspection"` |

The base form has one inner group (category, pre-fill, company,
`quality_control_oca/views/qc_test_view.xml:27-34`); the new one becomes its second column.

## Views — `views/qc_inspection_views.xml`

One record, `qc_inspection_form_view`, inheriting
`quality_control_stock_oca.qc_inspection_form_view_picking` — the extension that adds `lot_id` — so
its specs see the stock fields and the base form together.

| Position | Content |
|---|---|
| field `product_id` after | `qms_roll_inspection`, `invisible="1"` |
| field `lot_id`, attributes | `invisible`: `qms_roll_inspection` — on a receipt-line inspection OCA's compute names the move's first lot (`quality_control_stock_oca/models/qc_inspection.py:42-57`), one roll among many |
| `//notebook/page[1]` after | page `Rolls` (`name="qms_rolls"`, `invisible="not qms_roll_inspection"`), below |

The Questions page is selected by position: it carries only a translated `string`, which view
inheritance may not select on (`addons/CLAUDE.md`, Views).

**The Rolls page**

| Element | Content |
|---|---|
| group | `qms_points_limit`, `qms_points_cap` and — step 2 — the three ΔE maxima: the snapshot, computed and so read-only, shown so the inspector reads the limits being applied; `qms_show_all_codes` |
| `div` (step 3) | button `action_qms_load_rolls`, `type="object"`, `string="Load rolls"`, `class="btn-secondary"`, `invisible="state != 'ready'"` — above the list it fills, and only where the list is editable. An object button saves the inspection first |
| field `qms_roll_ids` | `nolabel="1"`, `readonly="state != 'ready'"` (divergence 3) |
| its `list` | **from step 2** `editable="bottom"` (D17), `decoration-danger="not passed"`: `lot_id` (`domain="[('product_id', '=', parent.product_id)]"`, `options="{'no_create': True}"`, D7), `dye_lot` (`optional="show"`), `length`, `width`, `total_points`, `score` (`digits="[16,1]"`, display only, D3), button `action_qms_open_points` (`type="object"`, `icon="fa-list"`, `title="Points"`), `delta_e`, `delta_e_length`, `delta_e_width` (each `digits="[16,2]"`, `optional="show"`), `shade_band`, `passed`. Step 1 had a non-editable list and an inline form with the point entries; the form moves to `views/qms_inspection_roll_views.xml` |

**Step 1's list was not editable** because an editable list cannot open a row's form, and the entries
lived in that form. Step 2's shade is entered for every roll, so the list becomes editable and the
entries move behind the row's button (D17). The button saves the inspection before it opens.

## Views — `views/qms_inspection_roll_views.xml` (step 2)

| XML id | Content |
|---|---|
| `qms_inspection_roll_points_form` | form on `qms.inspection.roll`, opened by `action_qms_open_points`. A group with `lot_id` (`readonly="1"`), `dye_lot`, `length`, `width`; a group with `total_points`, `score` (`digits="[16,1]"`), `points_pass`, `passed`; `inspection_state` and `defect_code_domain`, both `invisible="1"`; then `point_ids`, `nolabel="1"`, `readonly="inspection_state != 'ready'"`, as an `editable="bottom"` list of `position`, `defect_code_id` (`domain="parent.defect_code_domain or []"`, `options="{'no_create': True}"`, D6) and `points`. `length` and `width` carry the same `readonly` |

Length and width are in the dialog as well as the row because they make the score the dialog shows;
they are the same fields, so the two cannot disagree.

## Views — `views/stock_lot_views.xml` (step 2)

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `view_production_lot_form` | `stock.view_production_lot_form` | field `ref` after | `qms_dye_lot`, `qms_shade_band` |
| `view_production_lot_tree` | `stock.view_production_lot_tree` | field `product_id` after | `qms_dye_lot`, `qms_shade_band`, both `optional="show"` |
| `search_product_lot_filter` | `stock.search_product_lot_filter` | field `product_id` after; filter `group_by_product` after | the field `qms_dye_lot`; group-by filters `group_by_qms_dye_lot` (`context="{'group_by': 'qms_dye_lot'}"`) and `group_by_qms_shade_band` |

Cutting reads the band with the dye lot (design §5.3), so the lot list can be grouped by dye lot with
the band beside each roll.

## Tests — `tests/test_qms_fabric_inspection.py`

`TestFabricInspection(FabricInspectionCase)`, `@tagged("post_install", "-at_install")`: the fixtures
create a product and lots, core records later modules extend. Codes use `unique_code_prefix()`.

**From step 2 the fixtures and helpers below live in `tests/common.py`,** as
`FabricInspectionCase(TransactionCase)` — no test methods of its own, so nothing is collected from it
— and every test class of the module derives from it. Step 1 wrote them in this file.

Fixtures: a quality defect group *Fabric* with leaf codes *Slub* and *Hole*, and a group *Seam* with
one leaf code; a catalog profile holding *Fabric*; a lot-tracked storable product (`type="consu"`,
`is_storable=True`, `tracking="lot"` — Odoo 18 has no `product` type, `stock/models/product.py:704`, and
lots are offered only for tracked storable products, `stock/models/stock_lot.py:47`) carrying that
profile and a second product carrying none; three lots of the first product, each created with `name` and
`product_id` only (`company_id` is computed, `stock_lot.py:57`); a roll test —
`qms_roll_inspection`, limit 28, cap 4 — with one qualitative question whose answers are *OK*
(`ok=True`) and *Not OK*; a plain test with the same question and no roll inspection.

Helpers: `_inspect(test, target)` creates a *draft* inspection on `target` — the profiled product by default, sets the test
through the *Set test* wizard (`qc.inspection.set.test` with `active_id`), moves it to *ready* with
`action_todo()` and answers the question *OK*; `_roll(inspection, lot, length, width, points, **values)`
creates a roll — with any further field values, the band for one — and one entry per `(position, points)` pair, all with *Slub*. `_user_without_inventory()` (added in step 3, and used by step 2's access test since) creates a user holding *Internal User* and *Quality control · User* only, for the access tests.

| Test | Asserts |
|---|---|
| `test_settings_copied_from_test` | an inspection from the roll test carries its `qms_roll_inspection`, limit and cap; one from the plain test carries `False`, 0.0 and 4 — the cap's default, which a plain test has too; one with no test carries `False`, 0.0 and 0 |
| `test_settings_frozen_after_test_edit` | the inspection's limit and cap are read first — the snapshot is computed at that read, not at the write of `test` (D1) — then the roll test's limit and cap are changed: read back from the database, the existing inspection keeps the old values, and a new inspection gets the new ones |
| `test_settings_follow_test_change` | with the plain test's cap set to 0, writing it onto an inspection from the roll test resets the three values — the write both OCA paths make |
| `test_rolls_ignored_after_test_change` | a roll inspection with a failing roll has `success` false; writing the plain test onto it makes `success` true while the roll still exists; writing the roll test back makes it false again (divergence 5) |
| `test_total_points_capped_per_metre` | entries of 3 and 2 at metre 10 and 1 at metre 11 total 5 |
| `test_no_cap` | with a cap of 0 on the inspection's test at creation, the same entries total 6 |
| `test_total_follows_position` | moving the 2-point entry from metre 10 to metre 12 raises the total from 5 to 6 — the `position` dependency |
| `test_score_formula` | 9 points on 100 m × 150 cm score 6.0 |
| `test_unscored_roll` | a roll with entries and no width is not scored, stores a score of 0.0 and passes its points |
| `test_points_against_limit` | 28 points on 100 m × 100 cm score exactly 28 and pass; 29 points — seven metres at 4 and one at 1 — on 100 m × 103.5 cm score about 28.019 and fail, a value one-decimal rounding would have passed (D3) |
| `test_limit_zero_not_judged` | with a limit of 0, a roll scoring 100 passes (divergence 2) |
| `test_success_includes_rolls` | with the question answered *OK*, a failing roll makes `success` false; deleting the entries that fail it makes it true again — the dependency from entry through roll to inspection |
| `test_lines_still_decide` | with every roll passing and the question answered *Not OK*, `success` is false — OCA's rule kept |
| `test_confirm_failing_roll_waits` | `action_confirm` on an inspection with a failing roll sets *waiting*; `action_approve` then sets *failed* |
| `test_confirm_requires_length_and_width` | `action_confirm` raises `UserError` for a roll with entries and no length, and for a roll with a length and no width; it succeeds with a roll that has neither and no entries — banded-only, in step 2 terms |
| `test_points_range` | an entry of 0 points and one of 5 each raise `IntegrityError`; a position of 0 does too, and so does an entry created without a position (divergence 6) |
| `test_roll_once_per_inspection` | a second roll on the same lot in the same inspection raises `IntegrityError`; the same lot in another inspection is accepted |
| `test_defect_code_restrict` | deleting a defect code a point entry uses raises `IntegrityError` |
| `test_code_domain_follows_profiles` | searching `qms.defect.code` with a roll's `defect_code_domain`: on the profiled product, *Slub* is found and the *Seam* code is not; with `qms_show_all_codes` both are; on the product with no profile both are; no group is ever found |

The three `IntegrityError` tests carry `@mute_logger("odoo.sql_db")`, as every restrict test in the
repository does, and wrap each failing insert in a savepoint.

The rolls in the tests are created on products, not through a receipt: the receipt-line inspection
is OCA's trigger configuration (design §11), and nothing in step 1 reads the move.

**Checked in the UI:** the Rolls page appearing on a roll inspection only; the inspection's lot field
gone there and present on others; the roll dialog's lot dropdown limited to the product's lots; the
defect dropdown in the point list following the profile and the switch — the one-level `parent.`
read of D6 is only proven by a click; the page read-only outside *ready*.

## Tests — `tests/test_qms_shade.py` (step 2)

`TestShade(FabricInspectionCase)`, `@tagged("post_install", "-at_install")`. The common roll test also
carries ΔE maxima of 1.0 vs standard, 0.8 head–tail and 0.8 side–centre–side. `_confirm(inspection)`
calls `action_confirm()`.

| Test | Asserts |
|---|---|
| `test_delta_e_settings_copied` | an inspection from the roll test carries the three maxima |
| `test_shade_pass_each_limit` | for each of the three values in turn: at its maximum the roll's shade passes; above it, `shade_pass` and `passed` are false and so is the inspection's `success` — each value is wired to its own maximum |
| `test_delta_e_max_zero_not_judged` | with all three maxima 0 on the test, a roll with ΔE 5.0 everywhere passes its shade (D12) |
| `test_unmeasured_delta_e_passes` | a roll with no ΔE entered passes its shade |
| `test_passed_needs_points_and_shade` | a roll passing its points and failing its shade is not `passed`; a roll failing its points and passing its shade is not either |
| `test_band_normalised` | `" a "` is stored `A` on create, `"455"` as is, and `" b"` written later is stored `B`; `"  "` is stored empty |
| `test_band_format_refused` | `AB`, `4 55`, `055`, `1234` and `A1` each raise `ValidationError`, on create |
| `test_dye_lot_from_name` | lots named `JJD1015-1`, `A-B-12` and `1111` carry the dye lots `JJD1015`, `A-B` and none; a dye lot typed by hand is kept; renaming the lot recomputes it (D14) |
| `test_roll_dye_lot_follows_lot` | a roll's `dye_lot` is its lot's, and follows when the lot's dye lot is corrected |
| `test_lot_band_from_confirmed_inspection` | a band on a roll of a *ready* inspection does not reach the lot; confirming the inspection writes it; a later inspection banding the same lot `B` and confirmed replaces it; a later confirmed inspection leaving the band empty keeps `B`; a cancelled inspection's band never reaches the lot (D15) |
| `test_lot_band_ignores_plain_test` | a confirmed inspection switched to the plain test, whose roll carries a band, leaves the lot's band empty — leftover rolls are ignored, as in `success` (divergence 5) |
| `test_lot_band_by_inspector_without_inventory` | a user holding *Quality control · User* and no Inventory group bands a roll and confirms; the lot's band is written (D15). The control: the same user reading the lot's `name` raises `AccessError` |
| `test_open_points_action` | `action_qms_open_points` returns a `target` `new` form action on the roll, with its `res_id` and the Points form's view id |

**Checked in the UI:** the test form's three maxima; the editable roll list taking lot, measurements,
ΔE and band in the row, a lowercase band stored upper-case and a malformed one refused; the Points
button saving the inspection and opening the entries, with the defect dropdown still following the
profile; the row's points and score updated on closing; the dialog read-only on a confirmed inspection;
the lot form and list showing dye lot and band, and the lot list grouped by dye lot.

## Tests — `tests/test_qms_load_rolls.py` (step 3)

`TestLoadRolls(FabricInspectionCase)`, `@tagged("post_install", "-at_install")`: the fixtures create a
product, lots, a stock move and users.

Fixtures: those of `tests/common.py` — its three lots are created in the order 1, 2, 3 — plus a draft stock move of the product from
`stock.stock_location_suppliers` to `stock.stock_location_stock`, with five move lines: lots 3, 1 and 2,
a second line on lot 2, and a line with no lot. Lot 3's line comes first so that line order and
creation order differ. The common `_inspect` takes the object to inspect, a product by default and here
the move.

| Test | Asserts |
|---|---|
| `test_load_one_row_per_lot` | on the move's inspection, the button creates three rolls, lots 1, 2, 3 in that order — creation order, not line order (D9); the second line on lot 2 adds nothing and the line without a lot is ignored; it returns `True` |
| `test_load_keeps_existing_rows` | with a roll already on lot 2 carrying a length and a point entry, the button adds lots 1 and 3 only, and lot 2's roll keeps its length and entry (D10) |
| `test_load_twice_notifies` | a second press creates nothing and returns a `display_notification` |
| `test_load_without_move_notifies` | on an inspection of the product itself, the button creates nothing and returns a `display_notification` (D11) |
| `test_load_as_inspector_without_inventory` | a user holding *Quality control · User* and no Inventory group loads the three rolls (D8). The control: the same user reading a field of the move raises `AccessError` — without it the test could pass because the user could read stock after all |

**Checked in the UI:** the button above the list in *ready* and gone otherwise; a press on a receipt
line's inspection listing every roll in receipt order; a second press notifying.

## Tests — `tests/test_qms_populate_defect.py` (step 4)

`TestPopulateDefect(FabricInspectionCase)`, `@tagged("post_install", "-at_install")`. On the common
roll test, the *Not OK* answer carries the *Hole* code. `_nonconformity(inspection)` creates a
nonconformity in Analysis carrying `qc_inspection_id`, with the fields `mgmtsystem_nonconformity`
requires — as `qms_quality_control`'s own Populate Defect tests do.
`_user_without_inventory(*groups)` takes further group XML ids, here
`mgmtsystem.group_mgmtsystem_user`.

| Test | Asserts |
|---|---|
| `test_points_become_items` | rolls on lots 1 and 2 with Slub at metres 1 and 2 and Hole at 3 on lot 1, Slub at 1 on lot 2; after confirming, Populate Defect creates two items: Slub with `qty_affected` 3 and a note naming both rolls, then Hole with 1 and a note naming lot 1 only; `sequence` 10 and 20 |
| `test_lines_come_first` | with the question answered *Not OK*, the line's Hole item comes first with the question as its note, and the point items follow, numbered on from it |
| `test_only_points_resolve` | with every question passing, point entries alone create items and the method returns `True` |
| `test_entries_on_passing_rolls_count` | a roll within its limit still gives its entries' item (D19) |
| `test_plain_test_rolls_ignored` | an inspection switched to the plain test and confirmed creates no point items, and with no coded line returns the notification (D20) |
| `test_populate_by_user_without_inventory` | a user holding *Quality control · User* and *Management system · User* and no Inventory group populates the items, the note naming the rolls (D21). The control: the same user reading the lot raises `AccessError` |
| `test_points_action_by_user_without_inventory` | that user's `action_qms_open_points` returns the action, titled with the roll's name (D21) |

**Checked in the UI:** on a nonconformity raised from a confirmed roll inspection, Populate Defect
listing the checklist's items first and one item per point-entry code after, with counts and roll
names; the Points dialog opening for an inspector without Inventory rights.

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Inspects fabric roll by roll at receipt. A receipt line's inspection lists its rolls — each a lot — with the defects found on each, scored by the 4-point system and normalised to points per 100 m². A roll that exceeds the test's limit fails the inspection. Step 2 adds: each roll's shade, measured on the spectrophotometer against the standard and within the roll, and its shade band; the dye lot and band on the lot, where cutting reads them |
| `readme/USAGE.md` | **Test**: tick *Roll Inspection* on the test and set the limit in points per 100 m² and the cap per metre (4 under the 4-point system). If the buyer's standard gives the limit per 100 yd², multiply it by 1.196. **Trigger**: set the fabric receipt trigger to the *after* timing, without *inspection per lot*, so each receipt line gets one inspection. **Rolls**: on the inspection's *Rolls* page, add a row per roll inspected and pick its lot; enter length in metres and width in centimetres to score it, then each defect with the metre it lies in (1 for the first) and its points, 1 to 4. A roll with neither length nor width is not scored — the rest of a sample. **Load rolls** (step 3), above the list, adds a row for every lot on the receipt line that has none yet, in receipt order, so every roll can be banded while only the sample is scored; rows already there are kept, and a deleted row comes back at the next press. The defect list follows the product's catalog profiles; *Show all catalog codes* widens it. **Shade** (step 2): set the three ΔE maxima on the test — 0 leaves one unjudged; in each roll's row enter the spectrophotometer's ΔE against the standard, head–tail and side–centre–side, and the band from shade sorting, one letter or a 555 code; from step 2 the point entries open from the row's list button. **Lots** (step 2): the dye lot is read from the lot name up to its last "-" and can be corrected on the lot; the band shows on the lot once its inspection is confirmed; group the lot list by dye lot to see bands for cutting. **Nonconformity** (step 4): Populate Defect on a nonconformity raised from a confirmed roll inspection adds, after the checklist's items, one item per defect code found on the rolls, with the number of entries as the quantity and the rolls named in the note. **Verdict**: the inspection succeeds only when every question passes and every roll passes its points and its shade; one failing roll sends it to supervisor approval, which records it as failed — the decision on which rolls are returned belongs on the nonconformity |
