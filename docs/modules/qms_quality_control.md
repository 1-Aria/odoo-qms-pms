# qms_quality_control

Defect capture at inspection, Populate Defect, the action ↔ inspection link, and
nonconformity prefill from an inspection.
Plan: §7.10 (inspection rows), §7.11.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `qms_defect_code_id` on `qc.test.question.value` and on `qc.test.question`, both restricted to quality leaf codes, shown on the question form | done | installed and tested 2026-09-23, `exit=0`, 4 tests, 0 failures; UI checked: the Defect Code column on a qualitative question's answers, the field under the quantitative question's min–max–UoM heading — the placement was accepted as it renders — and both dropdowns offering leaf quality codes only |
| 2 | `qms_defect_code_id` and `qms_qty_failed` on `qc.inspection.line`, shown in the line lists; Populate Defect on the nonconformity, gated on a confirmed inspection and an empty analysis | done | two passes, both 2026-09-23. First: `exit=0`, 19 tests, 0 failures; UI checked — the defect-code column filled on failures only, the button appearing once the inspection is confirmed and going once an item exists, the notification when nothing resolves, and the form opening cleanly for a management-system user outside quality control. A log review then found the group gate did not gate: `groups` reads a comma as *at least one* (`res_users.py:1167-1170`), so naming the management-system group beside the quality-control one passed every management-system user through. Both elements now name the quality-control group alone, `test_view_hides_gate_without_quality_control` covers the arch rather than only the compute, and the two step 1 restrict tests gained the `@mute_logger("odoo.sql_db")` every other restrict test in the repository carries. Second pass added `qms_qty_failed` and its transfer to the item: `exit=0`, 20 tests, 0 failures, both columns and the quantity carry-over checked in the UI |
| 3 | `mgmtsystem.action.qms_inspection_id` and the field on the action form; on the inspection, a three-path action count and a smart button each way, plus the button box the action form lacks | done | upgraded and tested 2026-09-23, `exit=0`, 33 tests, 0 failures; UI checked — the new button box on the action form, the field beside Reference, the inspection opening from the stat button, the actions list opening at a count of zero with the inspection prefilled on New, and the count including actions reached through the nonconformity and through its immediate action without double-counting one reachable both ways. `_compute_qms_action_count` returns 0 for an unsaved record: a `NewId` cannot go into a domain and the compute runs during onchange, the guard core writes as `isinstance(record.id, models.NewId)` (`crm_lead.py:575`) |
| 4 | Nonconformity prefill when created from an inspection | — | |

## Divergences from the plan

| # | Plan | This module | Reason |
|---|---|---|---|
| 1 | §7.11 names the field on `qc.test.question.value` `defect_code_id` | `qms_defect_code_id` | Fields added to OCA models take the `qms_` prefix; a plain `defect_code_id` on a QC model is exactly the name a future OCA field could take |
| 2 | §7.11 puts the defect code on the answer only | also on `qc.test.question`, read for a quantitative question | A quantitative question has no answer record to hang a code on, yet a failed measurement is still a defect: `qc.inspection.line.success` stores `max_value >= amount >= min_value` after converting the UoM (`quality_control_oca/models/qc_inspection.py:271-285`). The question is the only record that describes that failure, and there is exactly one way to fail it — out of tolerance |
| 3 | §7.11: Populate Defect creates "one `qms.nonconformity.item` per distinct defect" | one item per inspection line that resolves a defect code, in line order | Two lines pointing at the same defect are two findings; merging them would hide one. Question 1 → A, question 2 → A, question 3 → B gives two items for A and one for B |
| 4 | §7.11 does not say what a second press does | there is no second press: the button is hidden as soon as the nonconformity holds an item | It can only ever fill an empty analysis, so it never deletes anything a person entered and never orphans a response line. Simpler than the full reset Suggest Response performs (D30), and it needs no Python guard — the visibility rule is the whole of it. Repopulating means deleting the items by hand first, which step 2's readme says |
| 5 | §7.11: "carrying the severity through" to the item | nothing to carry | `qms_nonconformity` derives an item's severity from its defect code in a stored compute (its step 3), for items created in code as well |
| 6 | §7.10 lists NC ↔ Inspection as existing, via the OCA bridge | confirmed: `qc_inspection_id` on the nonconformity, `mgmtsystem_nonconformity_ids` and a count on the inspection, and `action_view_nonconformities` (`mgmtsystem_nonconformity_quality_control_oca/models/`) | Only the prefill context remains to add, in step 4 |
| 7 | §7.11 adds `defect_severity_id`, the code's default severity shown beside it on the answer | omitted | The defect code is enough on a checklist; the severity is visible on the code itself, and the item takes it from there |
| 8 | §7.11 puts no restriction on which defect codes a checklist may name | both fields carry the same domain: leaf codes, of the quality or both domain | A group is administrative, so an item must always carry a leaf code. On the item's own dropdown the §7.6 domain achieves that as a side effect, but Populate Defect creates items in code and bypasses it, so the restriction has to sit where the code is chosen. The `domain_kind` half keeps a maintenance-only code off a quality checklist, which is what D14 makes the field mean |
| 9 | §7.11 has Populate Defect read the inspection's answers itself | the resolution lives on `qc.inspection.line` as `qms_defect_code_id`, a non-stored compute the button reads | The rule "qualitative from the answer, quantitative from the question, nothing when the line passed" then exists once instead of once in a method and once for the UI. It also earns its place on the inspection: an inspector sees which defect each failed check will raise before any nonconformity exists |
| 10 | §7.11 does not say which inspections may be read | only a confirmed one — `waiting`, `success` or `failed` | A defect is not recorded against an inspection nobody has confirmed. It also removes the worst of the unmeasured-line problem: before confirmation a quantitative line reads 0.0 and fails any minimum above zero, so an unconfirmed inspection can resolve codes for questions nobody has answered |

| 11 | §7.11 assumes the analyst can read the inspection | Populate Defect requires `quality_control_oca.group_quality_control_user`, and the button is hidden without it | `qc.inspection` is readable only by that group (`quality_control_oca/security/ir.model.access.csv:2-3`); no management-system group implies it. Anyone who populates defects reads the inspection's lines, so the prerequisite is real rather than cosmetic — but it has to be declared, because the nonconformity form works without it today. See *Known traps* |

| 12 | §7.10 names the field on the action `inspection_id` | `qms_inspection_id` | The prefix rule, as in divergence 1. `mgmtsystem.action` is an OCA model and `inspection_id` is a name a future upstream field could take |
| 13 | §7.10: "count of zero opens a new form carrying the context defaults; count of one or more opens the matching records filtered" | **action → inspection**: the button is hidden when the field is empty. **inspection → actions**: always the filtered list, whatever the count, with the defaults on the action so its New button prefills | The two directions are not symmetric. An inspection is raised by a quality-control trigger or by hand in Quality Control, never sensibly created from an action, so there is nothing to prefill in that direction and a zero count has nothing to offer. Going the other way, one behaviour beats a branch: at zero the list is empty and its New button carries the same defaults, which is what the plan wanted the branch for. OCA's own bridge branches on the count (`mgmtsystem_nonconformity_quality_control_oca/models/qc_inspection.py`) and sets its context defaults **only** in the single-record branch, so creating from the list of many prefills nothing — the bug that behaviour invites |
| 14 | §7.10 gives each link an inverse One2many and a button counting it, so an inspection would count only the actions pointing at it | the inspection's button counts three paths — the direct link, the nonconformity's action plan and its immediate action — through an overridable `_qms_action_domain` | §7.10 was written before the determination engine existed. Generate Actions links an action to the nonconformity, so a direct count reads 0 on the main flow. The other direction keeps the plan's shape: an action has one inspection, and the Many2one is the count |
| 15 | §7.10 does not mention access | both smart buttons and the action's `qms_inspection_id` field carry the one group granting the foreign read, per D31 | `qms_inspection_id` and the inspection button dereference `qc.inspection` (`quality_control_oca.group_quality_control_user`); the actions button dereferences `mgmtsystem.action` (`mgmtsystem.group_mgmtsystem_viewer`). Nothing is granted by ACL — see `docs/Cross_Module_Access_Policy.md` |

**One code per characteristic** is the cost of divergence 2: a quantitative question
records "out of tolerance", never "too low" as against "too high". A second field for the
low side stays additive if a plant ever needs the distinction, with this one as the
fallback.

## Known traps in the base modules

**A Many2one's label is read as superuser; everything else about it is not.** In
`web_read`, a Many2one requested with only `display_name` never reads the comodel at all —
`fields_to_read == ['id']` short-circuits the `read()`, with a comment saying it "avoid[s] a
call to read on the co-model that might have different access rules"
(`odoo/addons/web/models/models.py:79-84`) — and the label itself is taken through
`rec.sudo()` (`:122-123`). Any other field of the comodel goes through
`co_records.web_read(extra_fields)` (`:113-118`), which is access-checked.

So the OCA bridge's `qc_inspection_id` displays fine on the nonconformity form for a
management-system user with no quality-control rights, even though `qc.inspection` grants
read to `group_quality_control_user` alone
(`quality_control_oca/security/ir.model.access.csv:2-3`) and the bridge adds no access rule
of its own. **The first thing to read anything else off that inspection is what raises
`AccessError` for that user** — and `qms_can_populate_defect` reads its `state`. A plain
compute is evaluated as the user (`compute_sudo` defaults to `store`, so `False` here —
`odoo/odoo/fields.py:443`, `309`), which is why the field carries the quality-control group
in the arch: a field the client never requests is never computed.

This is the same shape as the `document.page` trap in `qms_determination` (its divergence
2): the label passes, the real read raises.

**A related field would hide the problem rather than avoid it.** `related_sudo` defaults to
`True` and `compute_sudo` inherits it (`odoo/odoo/fields.py:451`), so a
`related="qc_inspection_id.state"` field is computed as superuser and raises nothing on form
load. The button would then appear for a user who cannot read the inspection, and the error
would arrive when they click it and `action_populate_defect` reads `inspection_lines`.
Failing on load is not better than failing on click; not failing at all is, which is what
the group gives.

**A `groups` attribute listing two groups is a union, not an intersection.** There is no
way to spell "both groups" in a view, so a gate must name the one group that actually
guards the access — see the note under the nonconformity view below.

**Steps 3 and 4 inherit this.** Any field on the nonconformity or the action that reads
inspection data — a smart-button count above all — needs the same group treatment, and the
same is true of the prefill context. A count computed without it turns the form into an
access error for every management-system user outside quality control.

## Folder structure

```
qms_quality_control/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── qc_test_question.py                               # 1
│   ├── qc_test_question_value.py                         # 1
│   ├── qc_inspection_line.py                             # 2
│   ├── mgmtsystem_nonconformity.py                       # 2 (Populate Defect), 4
│   ├── mgmtsystem_action.py                              # 3
│   └── qc_inspection.py                                  # 3, 4
├── views/
│   ├── qc_test_views.xml                                 # 1
│   ├── qc_inspection_views.xml                           # 2 (the code column), 3, 4
│   ├── mgmtsystem_nonconformity_views.xml                # 2
│   └── mgmtsystem_action_views.xml                       # 3
├── tests/__init__.py, test_qms_quality_control.py        # 1
│         test_qms_populate_defect.py                     # 2
│         test_qms_action_inspection.py                   # 3
└── readme/ DESCRIPTION.md, USAGE.md                      # 1 (DESCRIPTION), 2 (USAGE)
```

## Manifest

| Key | Value |
|---|---|
| `name` | `QMS Quality Control` |
| `summary` | `Defect codes on inspection answers, and nonconformity analysis from inspections` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Management System` |
| `depends` | `qms_nonconformity`, `quality_control_oca`, `mgmtsystem_nonconformity_quality_control_oca`, `mgmtsystem_action` |
| `data` | `views/qc_test_views.xml`, `views/qc_inspection_views.xml` (step 2, extended in step 3), `views/mgmtsystem_nonconformity_views.xml` (step 2), `views/mgmtsystem_action_views.xml` (step 3) |
| `installable` | `True` |

No access file: the module adds fields and a button to existing models, whose access
rules come from `quality_control_oca` and `mgmtsystem_nonconformity`. Populate Defect
creates `qms.nonconformity.item` records, which `mgmtsystem.group_mgmtsystem_user`
already has create rights on (`qms_nonconformity/security/ir.model.access.csv`).

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import qc_test_question`, `from . import qc_test_question_value`, `from . import qc_inspection_line` (step 2), `from . import mgmtsystem_nonconformity` (step 2), `from . import mgmtsystem_action`, `from . import qc_inspection` (step 3) |

## The checklist domain

Both fields offer the same codes, so the domain is one module-level constant in
`models/qc_test_question.py`, imported by `models/qc_test_question_value.py`:

```python
CHECKLIST_DEFECT_CODE_DOMAIN = [
    ("parent_id", "!=", False),
    ("domain_kind", "in", ("qm", "both")),
]
```

`parent_id != False` selects leaf codes only — a group is a heading, never a finding.
`domain_kind` keeps the list to the quality side; a `both` code qualifies, a
maintenance-only one does not.

A domain is a dropdown filter, so neither half is enforced against a write from code or
an import, and neither is covered by a test — they are checked in the UI. Enforcing them
in Python would be guard machinery for a case the dropdown already handles, and a
checklist is written by hand in a form.

## Models

### `qc.test.question` — `models/qc_test_question.py`

`_inherit = "qc.test.question"`. OCA's model carries `sequence`, `test`, `name`, `type`,
`ql_values`, `notes`, `min_value`, `max_value` and `uom_id` —
`quality_control_oca/models/qc_test.py:47-99`.

| Field | Type | Attributes |
|---|---|---|
| `qms_defect_code_id` | Many2one → `qms.defect.code` | `string="Defect Code"`, `ondelete="restrict"`, `domain=CHECKLIST_DEFECT_CODE_DOMAIN`, `help="The defect an out-of-tolerance measurement records. Quantitative questions only — a qualitative question carries its defect codes on its answers."` |

Read only for a quantitative question. A qualitative one puts the code on the answer,
where it is more precise: two wrong answers to the same question can be two different
defects. The field is therefore shown only in the form's quantitative group, and
Populate Defect reads it only for a line whose `question_type` is `quantitative`.

### `qc.test.question.value` — `models/qc_test_question_value.py`

`_inherit = "qc.test.question.value"`. OCA's model carries only `test_line`, `name` and
`ok` ("Correct answer?") — `quality_control_oca/models/qc_test.py:103-112`.

| Field | Type | Attributes |
|---|---|---|
| `qms_defect_code_id` | Many2one → `qms.defect.code` | `string="Defect Code"`, `ondelete="restrict"`, `domain=CHECKLIST_DEFECT_CODE_DOMAIN`, `help="The defect this answer records when it is given."` |

`ondelete="restrict"` on both fields, as elsewhere: a defect code a checklist uses is
archived, not deleted.

### `qc.inspection.line` — `models/qc_inspection_line.py` (step 2)

`_inherit = "qc.inspection.line"`. The line is the answered copy of a question: OCA fills
`name`, `test_line`, `question_type`, `min_value`, `max_value` and `possible_ql_values`
from the test at creation (`_prepare_inspection_line`,
`quality_control_oca/models/qc_inspection.py:226-241`), and stores the verdict in
`success` (`_compute_quality_test_check`, `:271-285`).

| Field | Type | Attributes |
|---|---|---|
| `qms_defect_code_id` | Many2one → `qms.defect.code` | `compute="_compute_qms_defect_code_id"`, not stored, `string="Defect Code"`, `help="The defect this line records. Empty while the line passes."` |
| `qms_qty_failed` | Float | `string="Quantity Failed"`, plain stored field, default 0.0 |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_defect_code_id` | `@api.depends("success", "question_type", "qualitative_value.qms_defect_code_id", "test_line.qms_defect_code_id")` | empty when `success`; otherwise the answer's code for a qualitative line and the question's for a quantitative one |

**This is the one place the resolution rule lives.** Populate Defect reads the field
rather than repeating the rule, so the inspection list and the generated items can never
disagree.

**Gated on `success`,** so the field means "the defect this line records", not "the defect
it would record if it failed": blank on every passing row, filled on a failure. The cost
is that an answer misconfigured as correct *and* carrying a defect code shows its code
nowhere on the inspection — accepted, because that misconfiguration is visible where it
was made, the answers list putting `ok` and the code side by side.

**Not stored,** so it cannot be searched or grouped, and an old inspection shows *today's*
checklist codes. Both are fine: the durable copy is the defect code on the nonconformity
item, which Populate Defect writes. It is the same live-reference trade as plan O5.

**An unanswered quantitative line counts as a failure.** `quantitative_value` defaults to
0.0, so a line with a minimum above zero resolves a code before anyone measures anything.
Populate Defect is therefore gated on a confirmed inspection, and the field itself is left
alone: on an unconfirmed inspection the column showing a premature code is information,
not a defect recorded anywhere.

**`qms_qty_failed` is how many units the defect affected**, which the inspection had no way
to say: the header's `qty` is the quantity inspected in the lot, one number for the whole
inspection. Populate Defect copies it to the item's `qty_affected`.

Three things it deliberately does not do:

- **No unit of measure of its own.** The line's existing `uom_id` describes the measurement
  on a quantitative question, not a count of affected units. `qms_qty_failed` is in the same
  unit as the inspection's header `qty`, and nothing converts.
- **No constraint against the header `qty`.** Requiring the failed quantities not to exceed
  the quantity inspected would be wrong: one garment with a torn sleeve *and* a broken
  stitch is two lines of quantity 1 against a header quantity of 1. Defects overlap on
  units, so the sum is not bounded by the size of the inspection.
- **No conditional visibility.** It stays a plain editable column rather than being hidden
  or readonly on a passing line. A quantity left on a line that later passes is ignored,
  because the line then resolves no defect code and Populate Defect skips it.

A plain Float rather than a decimal precision, matching `qty_affected` on the item so the
copy is lossless. `digits="Quality Control"` belongs to measurement values, and
`"Product Unit of Measure"` would imply the UoM handling ruled out above.

### `mgmtsystem.nonconformity` — `models/mgmtsystem_nonconformity.py` (step 2)

`_inherit = "mgmtsystem.nonconformity"`. `qc_inspection_id` comes from
`mgmtsystem_nonconformity_quality_control_oca` and `item_ids` from `qms_nonconformity`.

| Field | Type | Attributes |
|---|---|---|
| `qms_can_populate_defect` | Boolean | `compute="_compute_qms_can_populate_defect"`, not stored, `string="Can Populate Defect"` — the whole visibility rule for the button |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_qms_can_populate_defect` | `@api.depends("state", "item_ids", "qc_inspection_id.state")` | true when the nonconformity is in Analysis, holds no item, and has an inspection whose state is in `INSPECTION_DONE_STATES` |
| `action_populate_defect` | — | per nonconformity: for every line of `qc_inspection_id.inspection_lines` that resolves a `qms_defect_code_id`, create one `qms.nonconformity.item`. Creates only — it never deletes, because the button is gone once the nonconformity holds an item. If nothing was created at all, return a notification (below); otherwise `True` |

**`INSPECTION_DONE_STATES = ("waiting", "success", "failed")`**, a module-level constant:
the three states `qc.inspection` reaches once it has been confirmed
(`quality_control_oca/models/qc_inspection.py:70-81`, `145-172`). `action_confirm` sends a
failing inspection to `waiting` for supervisor approval and a passing one straight to
`success`; `action_approve` then resolves `waiting` into `success` or `failed`. `waiting`
matters most — it is where an inspection sits when defects have just been found, which is
exactly when a nonconformity gets raised. Excluded: `plan`, `draft` and `ready`, where
nothing has been confirmed, and `canceled`, which is a voided inspection.

**A computed Boolean rather than the inspection's state exposed on the form.** Both work;
this one puts the rule in Python, where a test can assert it state by state, and leaves the
view with a single term. It is also the idiom the plan already uses for a view gate,
`can_edit_priority` in §7.12. Exposing `qc_inspection_id.state` as a related field instead
would spread the rule across three terms in the arch, where nothing can test it.

**What the gate does and does not fix.** It removes items generated from an inspection
nobody has confirmed. It does **not** guarantee every measurement was taken:
`action_confirm` refuses an unanswered *qualitative* question but asks only for a unit of
measure on a quantitative one (`:145-166`), so an inspector can confirm without typing a
measurement and the line still reads 0.0 and fails its minimum. Populate Defect will make
an item for it. That residue is accepted — the analyst deletes the item — and it is the
inspection's own validation, which this module does not extend.

**Values for a generated item**

| Item field | Value |
|---|---|
| `nonconformity_id` | this nonconformity |
| `sequence` | 10, 20, 30… in line order, so the items keep the inspection's question order |
| `defect_code_id` | `line.qms_defect_code_id` |
| `note` | `line.name`, the question — without it an item reads *Torn* with no trace of which check raised it |
| `severity_id` | not set: `qms_nonconformity` derives it from the defect code in a stored compute, for items created in code as well (its step 3) |
| `object_part_id`, `cause_id` | not set — left for the analyst, and the wildcard matching in the revised determination plan §5 handles a partial item natively |
| `qty_affected` | `line.qms_qty_failed` — the quantity the inspector recorded against that defect. An unfilled one copies 0.0, which is the item's own default, so there is no special case |

Line order needs no sorting. `qc.inspection.line` declares no `_order`, so it is `id`, and
the lines are created by walking `test.test_lines` (`_prepare_inspection_lines`,
`quality_control_oca/models/qc_inspection.py:217-224`), which is ordered `sequence, id`.

**Notification when nothing resolved** — the same mechanism `qms_determination` uses for
skipped templates, and the only feedback available: the button is visible exactly when the
analysis is empty, so a click that creates nothing would otherwise look broken.

| Key | Value |
|---|---|
| `type` | `"ir.actions.client"` |
| `tag` | `"display_notification"` |
| `params.type` | `"warning"` |
| `params.title` | `"No defects to populate"` |
| `params.message` | `"No line on this inspection records a defect code. Codes are set on the test's questions and answers."` |

No `params.next`: nothing changed, so there is nothing to reload. On the success path the
method returns `True` and the client reloads the form itself.

### `mgmtsystem.action` — `models/mgmtsystem_action.py` (step 3)

`_inherit = "mgmtsystem.action"`

| Field | Type | Attributes |
|---|---|---|
| `qms_inspection_id` | Many2one → `qc.inspection` | `string="Inspection"`, `ondelete="set null"`, `index=True` |

| Method | Behaviour |
|---|---|
| `action_view_qms_inspection` | `ensure_one`, returns an `ir.actions.act_window` on `qc.inspection` with `res_id` set and `view_mode` `form` |

`ondelete="set null"` rather than `restrict`, unlike every other link in this system. An
action is the record of work done and must outlive its source: OCA already refuses to delete
an inspection that is not in draft (`qc_inspection._unlink_except_autogenerated_and_non_draft`),
so the only inspection that can disappear is one nobody confirmed, and an action that survives
it with an empty link loses nothing. `restrict` would instead make a draft inspection
undeletable because someone raised an action from it.

### `qc.inspection` — `models/qc_inspection.py` (step 3)

`_inherit = "qc.inspection"`

| Field | Type | Attributes |
|---|---|---|
| `qms_action_ids` | One2many → `mgmtsystem.action` | inverse `qms_inspection_id`, `string="Directly Linked Actions"`; in no view — see below |
| `qms_action_count` | Integer | `compute="_compute_qms_action_count"`, not stored, `string="# Actions"` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_qms_action_domain` | — | `ensure_one`; the three ways an action belongs to this inspection, as one domain |
| `_compute_qms_action_count` | `@api.depends("qms_action_ids", "mgmtsystem_nonconformity_ids.action_ids", "mgmtsystem_nonconformity_ids.immediate_action_id")` | `search_count(inspection._qms_action_domain())` |
| `action_view_qms_actions` | — | `ensure_one`, returns an `ir.actions.act_window` on `mgmtsystem.action`, `view_mode` `list,form`, `domain=self._qms_action_domain()`, `context={"default_qms_inspection_id": self.id}` |

**The count spans three paths, not one.** Counting `qms_action_ids` alone would read 0 on the
flow this system is built around: inspection → Populate Defect → Suggest Response → Generate
Actions links each action to the *nonconformity*, never to the inspection.

```python
def _qms_action_domain(self):
    self.ensure_one()
    return [
        "|", ("qms_inspection_id", "=", self.id),
        "|", ("nonconformity_ids.qc_inspection_id", "=", self.id),
        ("nonconformity_immediate_id.qc_inspection_id", "=", self.id),
    ]
```

| Arm | Reaches |
|---|---|
| `qms_inspection_id` | an action raised on the inspection directly |
| `nonconformity_ids.qc_inspection_id` | the action plan of a nonconformity raised from it — what Generate Actions writes (`mgmtsystem_nonconformity/models/mgmtsystem_action.py:12-18`) |
| `nonconformity_immediate_id.qc_inspection_id` | that nonconformity's **immediate containment action**, which is a Many2one on the nonconformity and is absent from `action_ids`. OCA's own code treats the full set as `action_ids + immediate_action_id` (`mgmtsystem_nonconformity.py:156`), and plan §7.7 makes `immediate_action_id` the fast path for containment — the action a failed inspection most often produces first |

An action reachable by two arms is counted once: it is one search, not a sum.

**`qms_inspection_id` is not written onto generated actions.** Filling it in Generate Actions
would store the same fact twice, write onto records `qms_determination` owns, and go stale if
a nonconformity's inspection were corrected. The domain states the relation as it is.

**A method, not an inline domain**, because the maintenance side meets the same gap later:
D19 and D22 have `maintenance_mgmtsystem_action` ship the direct arm while `qms_maintenance`
extends it with the nonconformity arms. That split only works if the domain is overridable.

**`qms_action_ids` is kept although nothing counts or displays it**, because a non-stored
compute needs a dependency path and a `search_count` has none. Without it — and without the two
nonconformity paths beside it — the count would be computed once per cache lifetime and never
invalidated, so an action created in the same transaction would not appear. That is also what
would make the tests flaky. The field is in no view, so it cannot disagree with the button.

The count is not stored: it is read on a form, never searched or grouped.

**No `default_name` in the context.** An action's `name` is its subject, and seeding it with
an inspection number would put a placeholder where a sentence belongs. `type_action` is
likewise left for the user: it is required with no default, and guessing it is the mistake
`qms_determination` step 3 already refused to make for untyped templates.

**Both buttons and the action's field carry a group** (D31): the ones reading `qc.inspection`
name `quality_control_oca.group_quality_control_user`, the one reading `mgmtsystem.action`
names `mgmtsystem.group_mgmtsystem_viewer`. A `<field>` inside a gated `<button>` needs no
group of its own — `_postprocess_access_rights` removes the node with its children.

## Views — `views/qc_test_views.xml`

Inherits `quality_control_oca.qc_test_question_form_view`. Answers are edited in the
question form; the test form shows them only as a read-only column, so it needs no
inheritance of its own.

| Position | Content |
|---|---|
| field `ok` inside the `ql_values` list, after | the answer's `qms_defect_code_id` (`options="{'no_create': True}"`) |
| the `div` inside group `name="quantitative"`, after | the question's `qms_defect_code_id` (`options="{'no_create': True}"`) |

The second anchor is the group holding min, max and UoM
(`quality_control_oca/views/qc_test_view.xml:102-133`), which the base form already hides
for a qualitative question — so the question-level code appears exactly where it applies,
with no `invisible` of our own. The group is selected by `@name`, never by `@string`,
which view inheritance rejects as a translated attribute.

## Views — `views/qc_inspection_views.xml` (step 2)

Two inheritances, because `qc.inspection.line` is shown in two places and failures are
reviewed in both.

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `qc_inspection_form_view` | `quality_control_oca.qc_inspection_form_view` | field `valid_values` after (inside the embedded `inspection_lines` list, `views/qc_inspection_view.xml:143`) | `qms_defect_code_id` then `qms_qty_failed`, both `optional="show"` |
| `qc_inspection_line_tree_view` | `quality_control_oca.qc_inspection_line_tree_view` | field `valid_values` after (`:398`) | the same two columns |

The column sits between *Valid values* and *Success?* — what counts as correct, what the
defect is, whether it passed. The standalone list is the more useful of the two: it is
behind the *Inspection Lines* menu, carries `decoration-danger` on failures and has a
Failed filter, so it becomes a cross-inspection defect view for free.

The field is computed and not stored, so no `readonly="1"` is needed; Odoo makes a
compute without an inverse readonly already.

## Views — `views/mgmtsystem_action_views.xml` (step 3)

Inherits `mgmtsystem_action.view_mgmtsystem_action_form`.

| Position | Content |
|---|---|
| `//sheet/div[hasclass('oe_title')]` before | `<div name="button_box" class="oe_button_box">` holding one `oe_stat_button`: `action_view_qms_inspection`, `icon="fa-check-square-o"`, the label *Inspection*, `invisible="not qms_inspection_id"`, `groups="quality_control_oca.group_quality_control_user"` |
| field `reference` after (inside `group[@name='meta']`) | `qms_inspection_id`, `options="{'no_create': True}"`, same group |

**The action form has no button box**, so this module creates it: no `oe_button_box` appears in
`mgmtsystem_action/views/mgmtsystem_action.xml`, nor in any installed module extending that
form (`mgmtsystem_action_template`, `mgmtsystem_action_efficacy`, `mgmtsystem_nonconformity`).
Should a future OCA version add one, this creates a second box beside it rather than failing —
so it is worth re-checking on an upgrade of `mgmtsystem_action`.

**The field is on the form as well as the button**, in the *meta* group beside `reference`.
Without it the link could only ever be set from the inspection side, and an action raised
independently could never be attached to the inspection it came from.

The button is hidden when the field is empty rather than offering to create an inspection — see
divergence 13.

## Views — `views/qc_inspection_views.xml` (step 3 additions)

| Position | Content |
|---|---|
| `//div[hasclass('oe_button_box')]` inside | an `oe_stat_button`: `action_view_qms_actions`, `icon="fa-tasks"`, `qms_action_count` as the stat value with singular and plural labels, `groups="mgmtsystem.group_mgmtsystem_viewer"` |

The button box already exists on the inspection form — OCA's own bridge adds its nonconformity
count into it the same way (`mgmtsystem_nonconformity_quality_control_oca/views/qc_inspection.xml:12-33`),
which is also the model for the singular/plural spans.

Unlike that bridge's button, this one carries a group. Its button is the reason a
quality-control user with no management-system group cannot open an inspection at all, which is
recorded as an upstream bug in `docs/Cross_Module_Access_Policy.md` §6.

## Views — `views/mgmtsystem_nonconformity_views.xml` (step 2)

Inherits `mgmtsystem_nonconformity.view_mgmtsystem_nonconformity_form`.

| Position | Content |
|---|---|
| field `stage_id` (in `<header>`) before | button `action_populate_defect`, `type="object"`, `string="Populate Defect"`, `invisible="not qms_can_populate_defect"`, `groups="quality_control_oca.group_quality_control_user"` |
| field `stage_id` (in `<header>`) before | `qms_can_populate_defect`, `invisible="1"`, same `groups` — the client can only evaluate a field present in the arch |

**Both elements carry `quality_control_oca.group_quality_control_user`**, and the field's
copy is the load-bearing one: it keeps the compute from running for a user who would fail
it. See *Known traps* below.

**One group, never a list.** A comma in `groups` means "member of **at least one**"
(`odoo/addons/base/models/res_users.py:1167-1170`, and the same matching in
`ir_ui_view._postprocess_access_rights`, `:1013-1040`), so adding
`mgmtsystem.group_mgmtsystem_user` beside it would let every management-system user
through — exactly the user this gate exists to stop. The first version of step 2 named
both and therefore gated nothing. Naming the quality-control group alone loses nothing: a
pure quality-control user has no access to `mgmtsystem.nonconformity` and never reaches
this form.

A quality-control user who is only a management-system *viewer* does see the button, and
the click then fails on the item ACL. That is left as is: the model's own access rules are
the right place for it, and a second rule in the view would be the guard machinery this
project avoids.

**Three conditions, all inside the computed field.** The nonconformity is in Analysis, the
phase that owns the analysis; it holds no item, which is what makes the button add-only and
removes any need for a Python guard; and its inspection has been confirmed. The arch
carries no copy of the rule.

Unsaved edits are covered: a non-stored compute is re-evaluated by the onchange protocol
when a dependency changes in the form, so adding the first item hides the button before the
record is saved.

No `confirm=`: the button deletes nothing and cannot run twice over the same analysis.

This module does not depend on `qms_determination`, so when both are installed the
relative order of *Populate Defect* and *Suggest Response* in the header follows view
loading, not a choice made here. Both sit before `stage_id`.

## Tests — `tests/test_qms_quality_control.py`

`TestChecklistDefectCode(TransactionCase)`, `at_install`: the fixtures create catalog codes
and QC test records, no core records. Codes use `unique_code_prefix()` from
`odoo.addons.qms_catalog.tests.common`.

| Test | Asserts |
|---|---|
| `test_answer_takes_defect_code` | an answer value holds its defect code |
| `test_question_takes_defect_code` | a quantitative question holds its defect code |
| `test_answer_defect_code_restrict` | deleting a defect code an answer uses raises `IntegrityError` |
| `test_question_defect_code_restrict` | deleting a defect code a question uses raises `IntegrityError` |

The two domains are dropdown filters and are checked in the UI, as the section above says.

Both restrict tests carry `@mute_logger("odoo.sql_db")`, as every other restrict test in
the repository does: the database error they provoke is expected, and an unmuted `ERROR`
line defeats grepping the log after an upgrade.

## Tests — `tests/test_qms_populate_defect.py` (step 2)

`TestPopulateDefect(TransactionCase)`, `@tagged("post_install", "-at_install")`: the
fixtures create a product and a nonconformity, core models other modules extend. Catalog
codes use `unique_code_prefix()`.

Fixtures: a defect group with two leaf codes, *Torn* (with a default severity) and *Out of
tolerance*; a `qc.test` with a qualitative question whose failing answer carries *Torn* and
a quantitative question in 10–20 carrying *Out of tolerance*; a product; an inspection on
that product from the test; and a nonconformity carrying `qc_inspection_id` plus the fields
`mgmtsystem_nonconformity` requires.

| Test | Asserts |
|---|---|
| `test_resolves_qualitative_code` | a line answered with the failing value resolves that answer's code |
| `test_resolves_quantitative_code` | a measurement outside 10–20 resolves the question's code |
| `test_passing_line_resolves_nothing` | the correct answer, and a measurement inside the range, both resolve empty — the `success` gate |
| `test_unanswered_quantitative_resolves_code` | an unmeasured quantitative line reads 0.0, so it fails its minimum and resolves a code — the residue the state gate does not remove, since `action_confirm` does not require a measurement |
| `test_gate_open_after_confirm` | `qms_can_populate_defect` is true for each of `waiting`, `success` and `failed` |
| `test_gate_closed_before_confirm` | it is false for `draft`, `ready` and `canceled`, and false with no inspection at all |
| `test_gate_closed_once_items_exist` | it is false once the nonconformity holds an item, and false outside the Analysis stage |
| `test_gate_requires_quality_control_group` | as a management-system user **without** `group_quality_control_user`: reading the nonconformity's `description` succeeds — the positive control, without which the test could pass for the wrong reason — and reading `qms_can_populate_defect` raises `AccessError`, which is the prerequisite the view's `groups` exists to respect |
| `test_view_hides_gate_without_quality_control` | `get_view` on the nonconformity form returns an arch containing `qms_can_populate_defect` for a user who has the quality-control group and not containing it for one who does not. The test above proves the field is dangerous; only this one proves the view keeps it away, which is what stops the form raising on load — and it is what a `groups` list of two groups silently failed to do |
| `test_code_follows_checklist_edit` | moving the answer's code to another defect changes what the line resolves, since the field is not stored |
| `test_populate_creates_one_item_per_line` | two failed lines give two items, in line order, with `sequence` 10 and 20 |
| `test_populate_carries_note_and_severity` | an item's `note` is the question's name and its `severity_id` is the defect code's default — the cross-module check that an item created in code still gets a severity |
| `test_populate_carries_quantity` | quantities set on the two coded lines arrive as the matching items' `qty_affected`, and a quantity typed on a line that resolves no code produces no item to carry it |
| `test_populate_skips_uncoded_lines` | a failed line whose answer carries no code produces no item |
| `test_populate_nothing_notifies` | with no line resolving a code, no item is created and the return value is a `display_notification` |
| `test_populate_without_inspection` | on a nonconformity with no inspection the method creates nothing and notifies, so it is safe even though the button is hidden there |

The three gate tests set the inspection's state by writing it, not by calling
`action_confirm`, whose own validation is OCA's business and would drag fixtures along with
it. That the button honours the field is a view rule, so it is checked in the UI.

Sixteen tests in step 2. The admin user the other tests run as is in
`group_quality_control_manager`, which implies the user group
(`quality_control_oca/security/quality_control_security.xml`), so only
`test_gate_requires_quality_control_group` needs a user of its own.

## Tests — `tests/test_qms_action_inspection.py` (step 3)

`TestActionInspection(TransactionCase)`, `@tagged("post_install", "-at_install")`: the fixtures
create a product, an inspection and users. One `qc.test` with a single qualitative question is
enough — the link does not care what the inspection found.

| Test | Asserts |
|---|---|
| `test_direct_action_counts` | an action created with `qms_inspection_id` appears in the inspection's `qms_action_ids` and the count is 1; a second action makes it 2 |
| `test_generated_action_counts` | an action linked to a nonconformity whose `qc_inspection_id` is this inspection counts, though nothing points at the inspection — the arm the main flow uses |
| `test_immediate_action_counts` | an action set as that nonconformity's `immediate_action_id`, and absent from its `action_ids`, counts |
| `test_action_on_unrelated_nonconformity_does_not_count` | an action on a nonconformity with no inspection, and one on a nonconformity from another inspection, are both excluded |
| `test_action_reachable_twice_counts_once` | an action carrying `qms_inspection_id` *and* sitting on a nonconformity from the same inspection counts once |
| `test_count_zero` | an inspection with no actions counts 0, which is what the always-visible button shows |
| `test_count_refreshes_within_transaction` | reading the count, then creating an action by each of the three paths, gives a new number each time — the dependency list is what makes that true, and a `search_count` with no `@api.depends` would fail here |
| `test_view_actions_domain_and_context` | `action_view_qms_actions` returns a `list,form` action whose domain is `_qms_action_domain()` and whose context carries `default_qms_inspection_id`, so New from the list prefills — including when the list is empty |
| `test_view_inspection_res_id` | `action_view_qms_inspection` returns a form action on `qc.inspection` with `res_id` set to the linked inspection |
| `test_draft_inspection_delete_keeps_action` | deleting a **draft** inspection that has an action leaves the action alive with an empty `qms_inspection_id` — the `ondelete="set null"` decision, and the only inspection OCA allows to be deleted |
| `test_combined_groups_read_both_ways` | a user holding *Quality control · User* **and** *Management system · User* reads the action's inspection and the inspection's action count without error — the positive control D31 rests on, and the test that would have caught every access failure found so far |
| `test_action_form_hides_inspection_without_quality_control` | `get_view` on the action form contains `qms_inspection_id` for a user with the quality-control group and not for a management-system user without it — the arch, as in step 2 |
| `test_inspection_form_hides_actions_without_mgmtsystem` | the mirror: `get_view` on the inspection form omits the actions button for a quality-control user with no management-system group. The more exposed of the two, since that button faces every management-system user. It proves our button adds no second failure; it cannot make that user's form work, because OCA's own ungated nonconformity count already breaks it (`docs/Cross_Module_Access_Policy.md` §6) |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Records which defect a failed inspection answer or an out-of-tolerance measurement represents, so a nonconformity raised from the inspection can be analysed from it |
| `readme/USAGE.md` (step 2) | Two sections. **Checklists**: a qualitative question carries a defect code on each answer, a quantitative one on the question; both offer leaf codes of the quality domain, and the inspection lines show which defect each failed line records and how many units it affected. **Populate Defect**: visible on a nonconformity in Analysis whose source inspection has been confirmed and which holds no items yet, it adds one item per recorded defect with the question in the note and the failed quantity carried over; it never deletes, so repopulating means deleting the items by hand first; object part and cause are left for the analyst. The button needs the Quality control / User group, since it reads the inspection |
