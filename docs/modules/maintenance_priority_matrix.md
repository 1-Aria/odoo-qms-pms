# maintenance_priority_matrix

Equipment criticality, reported urgency, and the rule table that turns the two into a
request's priority.
Design: `docs/Maintenance SLA Engine — Technical Design.md` — O1, R1, §3.1, §4.2, §4.4.
Plan: §7.12 (superseded), §8, D20 (superseded 2026-09-30).

The first of the SLA cluster, and deliberately independent of it: consistent priority is worth
having with no SLA at all, and `maintenance_sla` reads only the native `priority` field, so it
never depends on this module.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `criticality` on equipment and category, `maintenance.priority.rule` with its uniqueness index, access, views and menu | done | two passes, both 2026-09-30. First run failed `test_rule_uniqueness`: the constraint was `unique (criticality, urgency, company_id)` and PostgreSQL treats NULLs as distinct, so the company-less rows — the common case — could be duplicated. Replaced by a unique index over `COALESCE(company_id, -1)`, after which an `@api.constrains` added for a readable message failed too and was removed: it cannot front-run the index on either path. Second run `exit=0`, 10 tests, 0 failures; UI checked — the editable grid, duplicates refused, criticality on categories and machines, and the priority dropdown offering core's four values. The UI check also confirmed that setting a category's criticality does not reach equipment already in it, which is the design and stays |
| 2 | Request fields: `criticality` snapshot, `urgency`, `priority_suggested`, the write-time derivation of `priority`, `priority_reason` | done | two passes, both 2026-09-30. First: 20 tests with one failure — `test_priority_override_tracked` asserted on message text, where a tracked change carries no body but `mail.tracking.value` rows; rewritten to read `tracking_value_ids.field_id.name`. Second run `exit=0`, 20 tests, 0 failures. The UI check then changed three things: `criticality` put on the form, because an empty suggestion was unreadable without both inputs visible; `urgency` required for corrective requests; and core's star widget replaced by a selection on the form. The empty suggestion that prompted the first was not a fault — the grid held no row for that criticality and urgency pair. A third pass then made `criticality` read-only rather than editable, since a second editable criticality gave one decision two override points and imported an ITSM shape into a CMMS model, and required `priority` on corrective requests, since an empty priority is a hole in the SLA promise rather than a usable state. A fourth run then failed in `TestRequestPriority.setUpClass`: a grid row added during the UI check occupied a fixture pair, and this vocabulary is closed, so both test classes now clear the table first. Fifth pass removed the `priority` requirement again: a view requirement is evaluated before the save while `create()` fills the field after it, so requiring it made the automatic path unreachable and forced a manual pick on every request. A sixth pass guarded `priority_reason`'s requirement the same way: it too was evaluated before the save and blocked it, since an empty priority differs from a computed suggestion. A seventh pass fixed the create path, which the browser showed empty: the guard tested for the *key* `priority` in the values, and the web client sends `priority: False` for an untouched form field, so nothing was ever filled on a request raised from the form — while the tests passed by omitting the key. Now tested on the value. An eighth pass added the form onchange: changing urgency moved the suggestion while priority waited for the save, so the reason was demanded for a difference the save then removed. The rule now lives in `_should_follow_suggestion`, called by both `write()` and the onchange. Runs: `exit=0`, 21 tests, then 22, 23, 24, and finally 28 with 0 failures; the UI sequence passed — priority filled in the form before saving, following a changed urgency, an override holding with its reason, and the reason demanded only for a real difference |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §4.2 names the model `maintenance.sla.priority.rule` | `maintenance.priority.rule` | §3.1 has this module stand alone precisely because priority is useful without any SLA, and `maintenance_sla` is not among its dependencies. A model carrying `sla` in its name inside a module that knows nothing about SLA would contradict the split the design chose |
| 2 | §4.2 says "one row per combination (15 rows)" | the module ships **no rows**; the company configuration module supplies them | Which priority a criticality × urgency pair deserves is a business judgement each site makes, and seeding a guess would put wrong numbers behind right-looking targets. The unconfigured state is defined instead: no matching row means no suggestion, and `priority` is left exactly as it is |
| 3 | §4.4 makes `priority` a stored compute, "the editable kind" | `priority` stays a plain field, derived at write time | Settled in review on 2026-09-30. Turning a core field into a stored compute recomputes every existing request on install, shifts core's team KPI counters, and contests every other writer. Deriving it in `create()` and in `write()` — and only while the value still equals the last suggestion — gives the same behaviour with none of that, and matches the design's own principle that work happens at write time (§3, choice 4) |
| 4 | R1: "A maintenance manager may override it; the override is tracked with a reason" | anyone with write access may override; the reason is required in the form and the change is tracked | Who may change priority is still open in the design's §8, and the restriction is genuinely deferrable: **priority drives nothing until `maintenance_sla` exists**, and once it does, a commitment is protected by the target snapshotted on its SLA record, not by who may edit the field afterwards. That is also what would change later — an asymmetric guard becomes meaningful the moment a live target hangs off the value. Until then this follows the project's preference for suggesting over enforcing, and D20 was superseded precisely because a write guard bought auditability without consistency. One consequence to accept knowingly: a form-only requirement means an override written by import or RPC carries no reason — a reportable data-quality state, not an impossible one |
| 5 | §4.2 puts `criticality` on the category as "default for new equipment" | the same, and the module does **not** walk the category tree | `maintenance_equipment_category_hierarchy` is installed, so categories have parents, and inheriting criticality up that tree is a plausible future want. It is not in the design, and a default that silently changes when someone reparents a category is a different feature. Left out, noted here |

## Folder structure

```
maintenance_priority_matrix/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── maintenance_priority_rule.py                      # 1
│   ├── maintenance_equipment_category.py                 # 1
│   ├── maintenance_equipment.py                          # 1
│   └── maintenance_request.py                            # 2
├── security/ir.model.access.csv                          # 1
├── views/
│   ├── maintenance_priority_rule_views.xml               # 1
│   ├── maintenance_equipment_views.xml                   # 1 (equipment and category forms)
│   └── maintenance_request_views.xml                     # 2
├── tests/__init__.py, test_maintenance_priority_rule.py  # 1
│         test_maintenance_request_priority.py            # 2
└── readme/ DESCRIPTION.md, USAGE.md                      # 1 (DESCRIPTION), 2 (USAGE)
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Maintenance Priority Matrix` |
| `summary` | `Derive maintenance request priority from equipment criticality and reported urgency` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Maintenance` |
| `depends` | `maintenance` |
| `data` | `security/ir.model.access.csv`, `views/maintenance_priority_rule_views.xml`, `views/maintenance_equipment_views.xml`, `views/maintenance_request_views.xml` (step 2) |
| `installable` | `True` |

No `qms_` prefix on anything here: the module is named in OCA's `<base_module>_<feature>` form
and is meant to be contributable, so its fields carry plain names (the naming rule in
`addons/CLAUDE.md`).

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import maintenance_priority_rule`, `from . import maintenance_equipment_category`, `from . import maintenance_equipment`, `from . import maintenance_request` (step 2) |

## The two selections

Declared once, at module level in `models/maintenance_priority_rule.py`, and imported by the
other files so the values cannot drift apart.

```python
CRITICALITY = [("a", "A — critical"), ("b", "B — important"), ("c", "C — minor")]
URGENCY = [
    ("safety", "Safety risk"),
    ("line_stopped", "Line stopped"),
    ("defects", "Producing defects"),
    ("degraded", "Degraded operation"),
    ("no_impact", "No production impact"),
]
```

Lowercase keys, labels carrying the explanation: the stored value is what rules and reports
match on, so it must not be a letter whose meaning lives only in a label. The five urgency
values are the design's, in descending severity — the order matters only for reading, since
nothing computes from it.

## Models

### `maintenance.priority.rule` — `models/maintenance_priority_rule.py`

`models.Model` · `_name = "maintenance.priority.rule"` · `_description = "Maintenance Priority Rule"` · `_order = "criticality, urgency"`

| Field | Type | Attributes |
|---|---|---|
| `criticality` | Selection `CRITICALITY` | `required=True` |
| `urgency` | Selection `URGENCY` | `required=True` |
| `priority` | Selection | the same selection as `maintenance.request.priority`, read from the field rather than restated — see below; `required=True` |
| `company_id` | Many2one → `res.company` | optional, **no default** — a row with no company is the grid every company uses, and defaulting to the active company would make the global row the one nobody creates by accident |
| `active` | Boolean | `default=True` |

**Uniqueness — one unique index, and no readable message**

| Where | What |
|---|---|
| `_auto_init` | `tools.create_unique_index(self._cr, "maintenance_priority_rule_pair_uniq", self._table, ["criticality", "urgency", "COALESCE(company_id, -1)"])` |

**A plain `unique (criticality, urgency, company_id)` does not work here, and step 1 shipped
with one before a test caught it.** PostgreSQL treats NULLs as distinct in a unique constraint,
so the company-less rows — the grid every company uses, and the common case — could be
duplicated freely. Wrapping the column in `COALESCE(company_id, -1)` makes the absent company
comparable; `ir_filters` solves the same problem the same way
(`base/models/ir_filters.py:185-191`), which is also why this hangs off `_auto_init` with
`self._cr` rather than `init`.

**The message is the raw database one, on every path.** Odoo builds a readable message by
looking `e.diag.constraint_name` up in `pg_constraint` and matching `_sql_constraints`
(`odoo/models.py:7574-7590`); an index is not a constraint, so the lookup fails and the user
sees *duplicate key value violates unique constraint …* with the offending values.

**An `@api.constrains` cannot recover that message, and trying it is how this was learnt.**
On create, `create()` runs its INSERT (`models.py:5224`) before it validates (`:5297`). On
write, the constraint's own `search()` triggers the pre-search flush (`:5795`), which writes
the pending row and makes the database raise *inside* the constraint. A Python check cannot
front-run a database uniqueness rule on its own table.

The one mechanism that would give a readable message everywhere is a table constraint using
PostgreSQL 15's `UNIQUE NULLS NOT DISTINCT`. Not used: Odoo 18 runs on older servers, and a
module that fails to install on PostgreSQL 14 is worse than an ugly message on a configuration
grid that only managers edit.

Uniqueness ignores `active` — a retired row still occupies its pair, since the index has no
`WHERE`.

**One operational consequence.** An index cannot be created over rows that already violate it,
so if company-less duplicates ever arrive by direct SQL, the next upgrade fails at index
creation rather than at the write that made them.

| Method | Decorator | Behaviour |
|---|---|---|
| `_priority_for` | `@api.model` | `(criticality, urgency, company)` → the matching rule's priority, or `False`. Prefers a row for the company over a company-less row, and returns `False` when nothing matches or either input is empty |

**The priority selection is borrowed, not restated.** `maintenance.request.priority` is
core's `[('0','Very Low'), ('1','Low'), ('2','Normal'), ('3','High')]` (`maintenance.py:256`),
and a rule offering different values from the field it feeds would be a bug waiting to happen.
The field therefore resolves the real thing:

```python
selection=lambda self: self.env["maintenance.request"]
    ._fields["priority"]
    ._description_selection(self.env)
```

`_description_selection` (`odoo/fields.py:3020`) handles a list, a callable or a method name and
picks up any `selection_add` a future module contributes. `qms_catalog` already uses it in both
`domain_kind` constraint messages.

### `maintenance.equipment.category` — `models/maintenance_equipment_category.py`

| Field | Type | Attributes |
|---|---|---|
| `criticality` | Selection `CRITICALITY` | `string="Criticality"`, help naming it as the default for new equipment |

### `maintenance.equipment` — `models/maintenance_equipment.py`

| Field | Type | Attributes |
|---|---|---|
| `criticality` | Selection `CRITICALITY` | `compute="_compute_criticality"`, `store=True`, `readonly=False`, `@api.depends("category_id")` |

An editable stored compute, the pattern `qms_nonconformity` uses for item severity: a new
machine takes its category's criticality, a value set by hand stands, and re-categorising a
machine re-derives it — at which point the machine is being reclassified, so re-deriving is
the right answer. A category with no criticality assigns nothing rather than clearing a value
that was set deliberately.

**The category value is a default, not a live inheritance, and existing machines are not
reached.** `@api.depends("category_id")` fires when a *machine's* category changes, never when
a *category's* criticality does — so filling criticality into a category that already has
equipment changes nothing on that equipment. Confirmed in the UI on 2026-09-30 and kept.

Backfilling existing machines is a data job: an import, or a list edit. It is deliberately not
a feature of this module — a button to push a category's criticality onto its equipment was
proposed and rejected as machinery for a setup-time case.

The live-inheritance version was rejected on its own merits too. Adding `category_id.criticality`
to the dependency would either overwrite every hand-set value the moment a category changed, or,
if it assigned only into empty fields, leave an inherited value stored and indistinguishable from
a deliberate one — at which point moving a machine to another category would stop re-deriving.
Telling the two apart needs the remember-the-last-suggestion machinery `priority` uses in step 2,
which is more weight than a field set once per machine is worth.

### `maintenance.request` — `models/maintenance_request.py` (step 2)

| Field | Type | Attributes |
|---|---|---|
| `criticality` | Selection `CRITICALITY` | `compute="_compute_criticality"`, `store=True`, `readonly=False`, `@api.depends("equipment_id")` — a snapshot: later edits to the machine do not rewrite past requests |
| `urgency` | Selection `URGENCY` | `tracking=True` |
| `priority_suggested` | Selection | stored compute from `criticality` and `urgency` through `_priority_for`, `@api.depends("criticality", "urgency", "company_id")` |
| `priority` | native Selection | **not redeclared as a compute.** `tracking=True` is added, and the value is derived at write time — see below |
| `priority_reason` | Char | `tracking=True`, `copy=False` — an override justification must not travel to the next occurrence |

**The rule has one home and two callers.** `_should_follow_suggestion(current, old, old_suggested)`
answers "may this priority follow a moved suggestion?", and both callers differ only in where
*before* comes from — `write()` captures it from the database, the form's onchange reads
`self._origin`. Keeping it a shared predicate is what stops the form and the server disagreeing
about what "overridden" means:

```python
return current_priority == old_priority and old_priority == old_suggested
```

The first term protects a value the user set or cleared in the current edit; in `write()` it is
implied, since a write naming `priority` returns early. The second is what "never an override"
means.

**An onchange moves the priority in the form**, on `equipment_id`, `criticality` and `urgency`.
Without it the form judged a half-finished state: changing urgency moved the suggestion while
priority still held its old value, so `priority_reason` became required for a difference the save
then removed by following the suggestion anyway. This reverses the module's first position, which
was that an onchange would be a second implementation of the rule — true of writing the logic
twice, not of an onchange that calls the shared predicate.

`equipment_id` is named as a trigger in its own right. The recompute does chain into the onchange
today, because the web onchange loop reruns for fields whose value changed and are in the view's
spec (`addons/web/models/models.py:1041-1057`) — but only while `criticality` stays on the form.
Naming `equipment_id` does not depend on the view's contents.

**The derivation, at write time**

| Moment | Behaviour |
|---|---|
| `create()` | after `super()`, a record whose `priority` value is **falsy** takes `priority_suggested` when there is one. On the *value*, never on the key: the web client sends `priority: False` for a form field left untouched, so a `"priority" not in vals` guard filled nothing on any request raised from the form. `"0"` is a truthy string, so an explicit Very Low is still honoured |
| every `write()` | the `(priority, priority_suggested)` pair is read **per record, before** `super()`. Afterwards, a record whose suggestion moved *and* whose priority still equalled the old suggestion follows the new one |
| `write()` including `priority` | left alone: the user is setting it deliberately |

**A caller cannot ask for an empty priority while a suggestion exists.** That state is
indistinguishable from the form's untouched field, so it is filled; clearing the value afterwards
is the way to say it, and counts as an override.

**Captured on every write, not on a trigger list.** `criticality` on the request is itself a
stored compute on `equipment_id`, so reassigning a request to another machine changes the
criticality and therefore the suggestion while `vals` contains neither field. A trigger list
would have to be kept in step with the compute graph; reading the pair before `super()` and
comparing after cannot fall behind it. The cost is two stored-field reads per write.

Three properties of that rule, stated because each is a decision:

- **The capture is per record.** `write()` acts on a recordset, and two requests in it can hold
  different pairs, so the old values are kept per id rather than as one pair.
- **A cleared priority counts as an override.** Emptying the field leaves `priority` unequal to
  the suggestion, so nothing re-derives it afterwards. Someone who blanks a priority meant to.
- **Editing the rule grid does not restate existing suggestions.** `priority_suggested` depends
  on `criticality`, `urgency` and `company_id` — not on the rule rows — so changing the grid
  leaves every existing request as it stands. That is what keeps history stable; if a site ever
  wants the opposite, it is the on-demand re-evaluate button the SLA design lists in its §7, not
  a dependency on the rules.

**No onchange.** The form shows a new suggestion as soon as urgency changes, but `priority` moves
only on save. Smoothing that with an onchange would be a second implementation of the same rule,
and two copies drift — the reason this module has one derivation, in `write()`.

`priority_reason` is required in the form by
`required="priority_suggested and priority != priority_suggested"` — **both terms matter**. With
only the inequality, every request would demand a justification while no suggestion exists: no
rules configured yet, no urgency reported, or equipment with no criticality. That is the
instance's state for the weeks before the grid is agreed, and it would make the field an
obstacle exactly when it means nothing.

There is no Python constraint behind it (divergence 4). Both fields are tracked, so the chatter
holds the override and its reason.

## Security — `security/ir.model.access.csv`

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_maintenance_priority_rule_user` | `maintenance.priority.rule.user` | `model_maintenance_priority_rule` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_maintenance_priority_rule_manager` | `maintenance.priority.rule.manager` | `model_maintenance_priority_rule` | `maintenance.group_equipment_manager` | 1 | 1 | 1 | 1 |

Read for every internal user is not generosity: core grants `maintenance.request` create rights
to `base.group_user` (`maintenance/security/ir.model.access.csv:4`), the suggestion is computed
as whoever creates the request, and a compute that cannot read the rule table would raise on
creation. The other models need no rows — they belong to `maintenance`.

## Views — `views/maintenance_priority_rule_views.xml`

| XML id | Type | Content |
|---|---|---|
| `maintenance_priority_rule_view_list` | list | editable `bottom`: `criticality`, `urgency`, `priority`, `company_id` (`groups="base.group_multi_company"`), `active` (`column_invisible="True"`) |
| `maintenance_priority_rule_view_form` | form | archived ribbon, the four fields in a group |
| `maintenance_priority_rule_view_search` | search | fields `criticality`, `urgency`; filter `archived`; group by `criticality`, then `urgency` |
| `maintenance_priority_rule_action` | action | name `Priority Rules`, `view_mode` `list,form`, `search_view_id`, and a `help` string saying that with no rules configured no priority is suggested |

The list is editable because the table is a grid someone fills in one sitting.

| Menu | Parent | Groups | Sequence |
|---|---|---|---|
| `menu_maintenance_priority_rule` "Priority Rules" | `maintenance.menu_maintenance_configuration` | inherited — core's Configuration menu is already `maintenance.group_equipment_manager` | 20 |

## Views — `views/maintenance_equipment_views.xml`

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `hr_equipment_view_form` | `maintenance.hr_equipment_view_form` | field `category_id` after | `criticality` |
| `hr_equipment_category_view_form` | `maintenance.hr_equipment_category_view_form` | field `technician_user_id` after | `criticality` |

Both ids and both anchors read from the arch: the equipment form's `category_id` sits in the
first inner group (`maintenance/views/maintenance_views.xml:365`, field at `:395`), and the
category form's first group holds `technician_user_id` and `company_id` (`:586`, `:612-614`) —
there is no `category_id` on a category, so the technician field is the anchor there.

## Views — `views/maintenance_request_views.xml` (step 2)

| Position | Content |
|---|---|
| field `priority`, `position="attributes"` | `widget` becomes `selection` |
| field `priority` after, in the request form's second group (`maintenance/views/maintenance_views.xml:131`) | `criticality` (`readonly="1"`); `urgency` with `required="maintenance_type == 'corrective'"`; `priority_suggested` (`readonly="1"`); `priority_reason` with `required="priority_suggested and priority != priority_suggested and (id or priority)"` |
| field `stage_id` after, in the request list (`:192-208`) | `urgency`, `optional="show"` |

**The list has no `priority` column to anchor to.** `priority` appears three times in core's
file — the form at `:131`, the kanban at `:175` and the calendar at `:240` — and the list
(`hr_equipment_request_view_tree`, `:192-208`) carries none of them, so `stage_id` is the anchor
there. Each view record is inherited separately, so the form's `position="after"` is unambiguous.

**`criticality` is on the form**, and editable, as it is on the model. It was left off at first on
the grounds that it is a snapshot the matching reads — which turned out to make an empty
suggestion unreadable: with only urgency visible there is no way to tell that the pair has no
rule from the lookup being broken. Both inputs beside the suggestion make it explain itself.

**`urgency` is required for corrective requests only**, and in the view rather than on the model.
`maintenance_plan` generates preventive requests without it
(`maintenance_equipment.py:81-99`), so a model-level requirement would break plan generation —
and preventive work has no reporter to judge urgency in the first place.

**Priority is deliberately not required**, and the attempt to require it is worth recording.
A view requirement is evaluated *before* the save, while `priority` is filled by `create()`
*after* it — so requiring the field made the automatic path unreachable: the form refused to
save, `create()` never ran, and a requester had to pick a priority on every corrective request,
which is the inconsistency this module exists to remove. It was tried, seen in the UI, and
reverted.

The `required="id and maintenance_type == 'corrective'"` variant would have allowed creation
while blocking a later clearing. Rejected as well: when no rule matches, the request saves with
an empty priority and the next person to edit anything on it is forced to invent one.

**An empty priority is therefore possible, and `maintenance_sla` is where it is answered.** A
rule with no priority matches any priority (design §4.1), so such a request collects a site's
priority-agnostic commitments. That module's spec states it as a decision, with a test, rather
than inheriting the default silently. Wildcard rows in *this* grid — optional criticality and
urgency, empty meaning any — would remove most empty priorities at the source and stay
configuration, but they need a precedence rule (`sequence`, first match wins, since this table
must yield exactly one answer, unlike D26's accumulating rules) and the uniqueness index
extended to COALESCE those columns too. Deferred until real requests turn out to be
unsuggestable: with urgency required on corrective work and criticality set on machines, the
fifteen pairs cover it.

**The star is replaced by a selection on the form.** Core's `widget="priority"` is a one-click
toggle with no confirmation, too casual for the field every SLA target will hang off: a click
meant for one star lands on another and nothing asks. The kanban and list keep the star, where it
is a display rather than an input.

**One trap, twice — and the reason every condition in this section is shaped around it.**
A form expression is evaluated **before** the save, while `create()` fills `priority` **after**
it. So on an untouched new record the suggestion already differs from an empty priority, and any
condition written in the obvious way blocks the very save that would have filled the field. It
caught the priority requirement, which was removed, and then the reason requirement, which was
guarded. Anything added here later that mentions `priority` must be true of an unsaved record
where it is still empty.

**The reason's three terms**, each answering one case:

| Term | Case it answers |
|---|---|
| `priority_suggested` | before the grid is filled — or with no urgency, or a machine with no criticality — there is nothing to differ from, so nothing to justify |
| `priority != priority_suggested` | the override itself |
| `(id or priority)` | the trap: `id` is falsy while unsaved, so an untouched new record saves; a priority picked by hand on that same new record still asks for its reason, which is when an override is likeliest |

On a saved record both remaining cases are covered: a priority moved away from the suggestion,
and a priority cleared, which counts as an override and now has to say why.

## A note both test files carry

**The fixtures clear the rule table first.** The instance holds a configured grid, and this
vocabulary is *closed*: fifteen criticality-urgency pairs exist and no more, so there is no
collision-proof fixture pair — the `unique_code_prefix()` trick that protects the catalog
fixtures has no equivalent. A fixture pair that a site happens to have configured makes the
run fail on the INSERT, which is how this was found: a grid row added during a UI check broke
`TestRequestPriority.setUpClass` on the next run.

Clearing inside the test transaction is safe, because a `TransactionCase` rolls back — the
instance's own rows are untouched — and it makes the fixtures the only rules in play, which the
derivation tests need anyway.

## Tests — `tests/test_maintenance_priority_rule.py` (step 1)

`TestPriorityRule(TransactionCase)`, `@tagged("post_install", "-at_install")`: the fixtures
create equipment, and a later module could extend it.

| Test | Asserts |
|---|---|
| `test_rule_uniqueness_global` | a second **company-less** row for one pair raises `IntegrityError` — the case the original constraint silently allowed |
| `test_rule_uniqueness_within_company` | the same within one company |
| `test_rule_uniqueness_ignores_archived` | an archived row still occupies its pair |
| `test_duplicate_by_write_refused` | editing a row into a duplicate raises `IntegrityError` too — the write path is refused by the index, not by a Python check |
| `test_rule_per_company_allowed` | the same pair in another company is accepted |
| `test_priority_for_match` | `_priority_for` returns the configured priority for a pair |
| `test_priority_for_no_match` | it returns `False` for an unconfigured pair, and for empty inputs — the unconfigured state divergence 2 defines |
| `test_priority_for_prefers_company_row` | with both a company row and a company-less row, the company's wins |
| `test_equipment_criticality_from_category` | new equipment takes its category's criticality; a value set by hand survives a write to another field; re-categorising re-derives it; a category with no criticality assigns nothing |

## Tests — `tests/test_maintenance_request_priority.py` (step 2)

`TestRequestPriority(TransactionCase)`, `@tagged("post_install", "-at_install")`.

| Test | Asserts |
|---|---|
| `test_criticality_snapshot` | a request takes its equipment's criticality, and changing the equipment's afterwards leaves the request alone |
| `test_suggestion_from_rules` | `priority_suggested` follows the rule table for the request's criticality and urgency |
| `test_priority_follows_suggestion_on_create` | a request created without a priority takes the suggestion |
| `test_falsy_priority_in_vals_still_fills` | a request created with `priority=False` — **what the client sends** for an untouched form field — is filled too. The test that was missing: the others omit the key, which the client never does |
| `test_explicit_priority_on_create_kept` | a request created with a priority keeps it |
| `test_priority_follows_new_suggestion` | changing urgency on a non-overridden request moves its priority |
| `test_reassigned_equipment_moves_priority` | moving a request to equipment of another criticality moves the suggestion **and** the priority, though `vals` carried only `equipment_id` — the gap a trigger list on `criticality`/`urgency` would have left |
| `test_cleared_priority_is_an_override` | emptying `priority` survives a later change of urgency: a blank is a decision, not an absence |
| `test_override_survives_new_suggestion` | a priority set by hand is not moved when urgency changes — the override case, and the reason the old pair is read before `super()` |
| `test_no_rules_leaves_priority_alone` | with no rules configured, creating and editing a request never writes `priority` |
| `test_onchange_moves_priority_in_the_form` | on a saved, non-overridden request, changing urgency in the form moves both the suggestion and the priority |
| `test_onchange_leaves_an_override_alone` | an overridden priority is untouched, so the mismatch and the reason requirement are real |
| `test_onchange_leaves_an_unsaved_change_alone` | a priority picked by hand in the current edit survives a later urgency change — the `current == old` term |
| `test_onchange_fills_a_new_record` | on a new request the priority is filled before the save, which is also what stops the reason being demanded on creation |
| `test_priority_form_is_a_plain_selection` | the arch's `priority` field carries `widget="selection"` and **no** `required` — the star is gone and the requirement stays gone |
| `test_reason_requirement_allows_the_unsaved_state` | the arch's `priority_reason` carries all three terms, `(id or priority)` included — the guard that keeps the create path open, pinned so it cannot be simplified away |
| `test_priority_fills_on_save_without_being_required` | a request created with urgency and no priority comes back carrying the suggestion: the path the requirement blocked |
| `test_priority_override_tracked` | an override and its reason reach the chatter, asserted on the message's `tracking_value_ids.field_id.name` rather than on message text: a tracked change carries no body, it carries `mail.tracking.value` rows (`mail/models/mail_tracking_value.py:15`). With the two `self.env.cr.precommit.run()` calls every tracking test here needs |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Derives a maintenance request's priority from the criticality of the machine and the urgency reported with the request, through a rule table, so that priority means the same thing across requesters. Useful on its own; also the first module of the maintenance SLA cluster |
| `readme/USAGE.md` (step 2) | Set criticality on equipment categories and machines; fill the Priority Rules grid; report urgency on a request and the priority follows; an override needs a reason and is recorded in the chatter. With no rules configured nothing is suggested and priority behaves as it does in core |
