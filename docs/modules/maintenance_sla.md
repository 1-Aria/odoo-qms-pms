# maintenance_sla

Configured commitments on maintenance requests, and immutable evidence of what happened to
each one.
Design: `docs/Maintenance SLA Engine — Technical Design.md` — the whole document. Plan: §7.12
(superseded, points there), §8, D20 (superseded).

The engine of the SLA cluster. It reads the native `priority` field and nothing else from
`maintenance_priority_matrix`, so the two are independent.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Configuration: `maintenance.sla` rules and their constraints, `sla_cancel` on stages, access, views, menu | done | 2026-10-01, one pass. `exit=0`, 10 tests, 0 failures; UI checked: the SLA Rules menu and form, the domain editor offering request fields, an `h:mm` target, *Cancels SLA* in the stage list, and a cancel flag on a target refused from both ends |
| 2 | Evidence: `maintenance.request.sla` and its snapshots, `reported_at`, `_sla_apply()` at creation | done | 2026-10-01, two passes. The first failed `test_requester_creates_records` with an `AccessError` on create: `hr_maintenance` computes `owner_user_id` from an employee (`hr_maintenance/models/equipment.py:87-97`), and `create()` checks record rules (`odoo/models.py:5298`) before mail subscribes the creator (`mail/models/mail_thread.py:294-299`), so a plain internal user failed the own-requests rule before this module ran. The test now makes the requester the request's responsible. Second run `exit=0`, 27 tests, 0 failures; UI checked: *Reported At* editable before the first save, one running record per matching rule with its deadline, a backdated report giving an overdue deadline, records read-only, existing requests without records |
| 3 | The clock: stage transitions, pause and resume, achieved and late, cancel, cycles | — | |
| 4 | Re-matching on request changes, waivers, `reported_at` correction | — | |
| 5 | Live state, the request's `next_deadline` and `sla_live_state`, kanban ordering and filters | — | |
| 6 | Reporting: the pivot and graph actions and their menu | — | |

Reporting is a step here rather than a module of its own: with the grouping dimensions living on
the evidence (design §4.3), the report is one action and a menu, and a separate module would be
an install-time decision with nothing in it.

## What the company configuration module supplies

The stage flow the rules target is **not** in this module. `<company>_maintenance_sla_config`
(data only) carries the stage records and their SLA flags, the rule rows, the priority grid rows
and the escalation Automated Actions — and, on this instance, the resequencing of the four
existing stages into the seven of design §5.4.

That module is therefore a **prerequisite for useful behaviour**, not a follow-up: a rule needs a
target stage, and the design's target stages do not exist yet. The engine installs and passes its
tests without it, because the tests build their own stages and rules.

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §3.1 makes `maintenance_sla_report` a separate module | reporting is step 6 of this module | With the dimensions on the evidence where §4.3 puts them, the report is an action plus a menu. A module boundary there buys the ability to withhold a pivot, and costs a manifest, a dependency edge and a second place to look |
| 2 | §4.1 lists the rule's fields without saying whether the optional `domain` is validated | a domain that does not parse, uses `uid` or another dynamic form, or names a field the request does not have is refused when the rule is saved | A rule's domain is evaluated while a request is being created. A broken one would raise for whoever raises the request, turning optional configuration into a blocked workflow — the project's standing rule is that optional setup must degrade, never break. Refusing it at save keeps the failure with the person who caused it |
| 3 | §4.1 gives `target_stage_id` no explicit requirement | required, and constrained not to be a cancel stage, from both ends | A commitment with no target is not a commitment. The cancel-stage exclusion is the design's own sentence, enforced rather than described |
| 4 | §4.1 has `start_from` (`reported` / `scheduled`) on the rule | no such field: the start follows the request's type — `reported_at` for corrective, `schedule_date` for preventive, falling back to `reported_at` when a preventive request has no scheduled date, and to `create_date` when `reported_at` is empty | R6 already ties the start to the type, and no rule the design names needs the other combination. A field that can only ever hold the value its type implies is a way to misconfigure a rule. The fallbacks exist because core does not require `schedule_date` and only `maintenance_plan` always sets it — a preventive request raised by hand would otherwise be unmeasured — and because `reported_at` is not required either, while a record's `start_at` is |
| 5 | §4.1 matches `equipment_category_ids` without saying how | exact match on the request's category; no `child_of` | `child_of` on a model without `_parent_store` reads `_fields['parent_id']` (`odoo/osv/expression.py:902`), which only exists while `maintenance_equipment_category_hierarchy` is installed. A module meant for contribution cannot depend on it. A site that has the hierarchy can still write `[('category_id', 'child_of', X)]` in the rule's `domain`, which divergence 2's check accepts there |
| 6 | §4.3 makes the grouping dimensions `related, stored` | plain fields, copied at record creation and refreshed by `_sla_apply()` while the record is open; only `company_id` stays related | A related stored field rewrites every record when the request changes, finished ones included, which breaks O2. Copied only at creation, a request reassigned to another team would leave its open record credited to the old one. Refreshed while open and fixed once finished, the dimensions describe the request as it stood when the commitment was met |
| 7 | §4.3 delegates access to the request with `return result or self.request_id._check_access(operation)`, as `helpdesk.ticket.sla` does | no delegation: the evidence is readable by every internal user | Settled in review on 2026-10-01: the restriction accomplishes nothing. `_check_access` governs reading records, not finding them — `search` and `read_group` apply record rules only — so the pivot would count and group every record whatever it hid. What it would hide is a rule name and some times. The snippet is also defective as written: it returns the request's records as the forbidden ones, while `_filtered_access` subtracts them from this model's (`odoo/models.py:4460-4461`), which raises `TypeError` (`:6963-6964`) |

## Decisions for later steps

Settled before the code exists, so that steps 2–4 are specced against them.

| # | Decision | Step |
|---|---|---|
| D1 | **One matching function.** `_sla_apply()` on `maintenance.request`, run as `sudo()`, safe to run twice. Per target stage it computes the winner — the matching rule with the lowest `(sequence, id)` — creates the missing record, and cancels an open record whose rule is no longer the winner. `create()` and `write()` both call it; nothing else creates records | 2, 4 |
| D2 | **`sudo()` is required, not a convenience.** A Many2many read applies the comodel's record rules (`odoo/fields.py`, `Many2many.read`, `_apply_ir_rules`), and `base_maintenance_group`'s `only_subscribe_maintenance_team` would show a non-member an empty `team_ids` — which reads as *any team*. `sudo()` keeps `env.uid`, so the records still carry the real creator | 2 |
| D3 | **What a rule matches.** `maintenance_type` equal; `priority` equal or empty on the rule; `team_ids` containing the request's team or empty; `equipment_category_ids` containing the request's category or empty (exact, divergence 5); `company_id` equal or empty on the rule; `domain` satisfied | 2 |
| D4 | **An empty priority collects only the rules with no priority set.** `maintenance_priority_matrix` allows an empty priority when no grid row matches; such a request gets the site's priority-agnostic commitments and no others. Tested | 2 |
| D5 | **No backfill.** Records are created by `create()` and `write()` only. Requests that exist when the module is installed get none, and nothing re-matches when a *rule* changes | 2 |
| D6 | **The current stage is evaluated at creation.** Step 2 creates a record `paused` when the request starts in one of its rule's pause stages. Step 3 adds the reached case: a request created at or past a target — a kanban quick-create in a later column — has that record finished straight away | 2, 3 |
| D7 | **When `write()` re-matches.** `priority`, `maintenance_team_id`, `category_id`, `maintenance_type` and `company_id` are read per record before `super()`, and `_sla_apply()` runs for the records where any of them changed. Captured, not read from `vals`: `category_id` is a stored related on `equipment_id`, so a reassigned machine changes it while `vals` names neither — the lesson `maintenance_priority_matrix` learnt for its own suggestion. A rule's `domain` is evaluated only at those moments: a change to a field only the domain reads triggers nothing | 4 |
| D8 | **Load order does not matter.** `maintenance_priority_matrix` writes `priority` from inside its `create()`. Whichever module loads last, either our `write()` runs inside `super().create()` before our own matching, or after it. Two tests cover both: create-then-write-priority leaves exactly one record per target stage, held by the winner; and a second `_sla_apply()` on an unchanged request changes nothing | 2, 4 |
| D9 | **Reached target stages are left alone.** A target stage whose latest record is finished and which the request still sits at or past gets no new record from re-matching | 4 |
| D10 | **A replacement carries the clock.** A record replacing a cancelled open one takes its `start_at`, `consumed`, `paused_time` and `cycle`; the new rule's target, duration and at-risk % apply from then on. A record with no predecessor — a rule newly matching — has no pause history, so its clock counts from `start_at` | 4 |
| D11 | **The next cycle is opened by `_sla_apply()` too.** For a target stage with no open record, whose latest record is finished, while the request now sits below that stage: a new record from the *current* winner, with `cycle + 1` and `start_at` the moment of the move. Only the latest record counts, and only when no open record exists for that stage, so a finished record cannot open a cycle twice. If priority changed in between, the next cycle follows the current rule — where design §5.2's `_open_next_cycles` reopens from the same rule, the one place this differs from it | 3 |
| D12 | **A cancel stage acts on open records only.** Finished records are evidence and keep their state | 3 |

**Open for the step 3 spec.** A request that leaves a cancel stage, or is un-archived —
core's `reset_equipment_request` (`maintenance/models/maintenance.py:293-297`) moves it back to the
first stage — has only cancelled records. Plain matching would recreate cycle 1 from
`reported_at`, overdue from the moment it exists.

## Folder structure

```
maintenance_sla/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── maintenance_sla.py                                # 1
│   ├── maintenance_stage.py                              # 1
│   ├── maintenance_request_sla.py                        # 2
│   └── maintenance_request.py                            # 2, 3, 4, 5
├── security/ir.model.access.csv                          # 1, 2
├── views/
│   ├── maintenance_sla_views.xml                         # 1
│   ├── maintenance_stage_views.xml                       # 1
│   ├── maintenance_request_sla_views.xml                 # 2, 4
│   ├── maintenance_request_views.xml                     # 2, 5
│   └── maintenance_sla_report_views.xml                  # 6
├── tests/__init__.py, test_maintenance_sla_rule.py       # 1
│         test_maintenance_request_sla.py                 # 2
└── readme/ DESCRIPTION.md, USAGE.md                      # 1 (DESCRIPTION), 5 (USAGE)
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Maintenance SLA` |
| `summary` | `Configured response and restore commitments on maintenance requests, with immutable evidence` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Maintenance` |
| `depends` | `maintenance`, `mail` |
| `data` | `security/ir.model.access.csv`, `views/maintenance_sla_views.xml`, `views/maintenance_stage_views.xml`, `views/maintenance_request_sla_views.xml` (step 2), `views/maintenance_request_views.xml` (step 2) |
| `installable` | `True` |

`mail` is declared although `maintenance` already brings it: this module posts to the request's
chatter itself (design §5.1), so the dependency is used directly rather than inherited by
accident.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import maintenance_sla`, `from . import maintenance_stage`, `from . import maintenance_request_sla` (step 2), `from . import maintenance_request` (step 2) |
| `tests/__init__.py` | `from . import test_maintenance_sla_rule`, `from . import test_maintenance_request_sla` (step 2) |

## Models

### `maintenance.sla` — `models/maintenance_sla.py`

`models.Model` · `_name = "maintenance.sla"` · `_description = "Maintenance SLA Rule"` · `_order = "sequence, id"`

One row is one commitment: *P3 · Response · reach In progress · 0:15*.

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `sequence` | Integer | `default=10`; lower wins when two matching rules share a target stage |
| `active` | Boolean | `default=True` |
| `company_id` | Many2one → `res.company` | optional, no default — a rule with no company applies to every company, as the priority grid does |
| `maintenance_type` | Selection | `_request_selection(self, "maintenance_type")`, `string="Maintenance Type"`, `required=True` |
| `priority` | Selection | `_request_selection(self, "priority")`, `string="Priority"`, optional — empty means any |
| `team_ids` | Many2many → `maintenance.team` | `string="Teams"`; empty means any |
| `equipment_category_ids` | Many2many → `maintenance.equipment.category` | `string="Equipment Categories"`; empty means any |
| `domain` | Char | `string="Extra Filter"`, optional |
| `target_stage_id` | Many2one → `maintenance.stage` | `string="Target Stage"`, `required=True`, `ondelete="restrict"` |
| `pause_stage_ids` | Many2many → `maintenance.stage` | `string="Pause Stages"`, `ondelete="restrict"`; time in these stages is not counted |
| `duration` | Float | `required=True`, `string="Target (hours)"` |
| `at_risk_pct` | Integer | `string="At Risk (%)"`, `default=75` |

`sequence`, `priority`, `team_ids`, `equipment_category_ids`, `domain`, `target_stage_id`,
`pause_stage_ids`, `duration` and `at_risk_pct` carry a `help` saying what an empty value means
or what the value does.

**Both selections are the request's own**, resolved through one module-level helper in
`models/maintenance_sla.py`, so a rule cannot key on a value a request could not hold:

```python
def _request_selection(model, field_name):
    field = model.env["maintenance.request"]._fields[field_name]
    return field._description_selection(model.env)
```

The fields declare `selection=lambda self: _request_selection(self, "priority")` and the same
for `"maintenance_type"`. `_description_selection` (`odoo/fields.py:3020`) handles a list, a
callable or a method name and picks up any `selection_add`. The helper is this module's own:
`maintenance_priority_matrix` has an equivalent, and importing it would make this module depend
on that one.

**`duration` is labelled *Target (hours)* everywhere**, per the design: core's
`maintenance.request.duration` already exists as a manual estimate for calendar and gantt
display, and the two will sit near each other in reports.

**`ondelete="restrict"` on `target_stage_id` and on `pause_stage_ids`.** On the Many2many it
lands on the relation table's stage column (`column2`, the only one `ondelete` governs). A stage
a commitment depends on cannot be deleted under it: stages are configuration a site rearranges,
and this is the guard that stops a rearrangement silently changing what a rule measures. Both are
enforced by the database, so a refused delete raises `IntegrityError`.

**No company check on teams and categories.** `check_company=True` would lock a company-less
rule — the common case — out of every team and category that carries a company: with no
company on the record, `_check_company` allows only company-less co-records
(`odoo/models.py:4334-4335`, `:4378-4392`), and the view's dropdown domain does the same
(`odoo/fields.py:3186-3187`). On this instance every team and category carries one. Without
the check, a rule naming another company's team simply never matches (D3) — inert, not harmful.

**Widgets live in the views.** A Python field accepts no `widget` parameter: `_valid_field_parameter`
allows only `related_sudo` (`odoo/models.py:662-664`), and anything else logs *unknown parameter*
on every load (`odoo/fields.py:524-532`).

**Constraints**

| Method | Decorator | Rule | Message |
|---|---|---|---|
| `_check_target_not_cancel` | `@api.constrains("target_stage_id")` | the target may not be a stage flagged `sla_cancel` | `"'%(stage)s' cancels SLA records, so it cannot also be a target stage."` |
| `_check_domain` | `@api.constrains("domain")` | the value, when set, parses through `ast.literal_eval` **and** passes `expression.expression(domain, self.env["maintenance.request"].sudo())` | `"This domain cannot be read: %(error)s"` |

**`_check_domain` has two halves, as core's own checks do.** `literal_eval` refuses what does not
parse and the dynamic forms — `uid`, `context_today()` — which this version does not support: a
domain that reads the environment would make a commitment depend on who created the request.
`expression.expression` then refuses a field the request does not have, which parses perfectly
and would otherwise raise at matching time. The second half is `ir.rule`'s check
(`base/models/ir_rule.py:63-72`); it builds the query without running it. The form's domain
editor runs with `allow_expressions` off, its default (`web/static/src/views/fields/domain/domain_field.js`), so it
offers literal domains only — the same line the check draws.

**`at_risk_pct` is not constrained to 0–100.** A value outside it produces a `risk_at` before the
start or after the deadline, which shows as *at risk* immediately or never — visible, harmless,
and not worth a guard.

| Method | Decorator | Behaviour |
|---|---|---|
| `_parsed_domain` | — | `ensure_one`; the domain as a list, or `[]` when unset. The single reader, so matching never calls `literal_eval` itself |
| `_matches` (step 2) | — | `ensure_one`; `(request)` → whether this rule applies to the request, by D3: `maintenance_type` equal; `priority` empty or equal; `team_ids` empty or containing `maintenance_team_id`; `equipment_category_ids` empty or containing `category_id`; `company_id` empty or equal; `domain` empty or `request.filtered_domain(self._parsed_domain())` non-empty. An empty request value fails every non-empty condition: a request with no team matches only rules with no teams, and a request with no priority only rules with no priority (D4). Called on `sudo()` records (D2) |

### `maintenance.stage` — `models/maintenance_stage.py`

| Field | Type | Attributes |
|---|---|---|
| `sla_cancel` | Boolean | `string="Cancels SLA"`, help naming what it does to open records |

Reaching a stage with this flag cancels a request's **open** records (step 3, D12). Core's stage
model carries only `name`, `sequence`, `fold` and `done` (`maintenance/models/maintenance.py:10-20`),
and `done` is not a substitute: *Repaired* is a done stage and must stop clocks by being reached,
while *Scrap* must cancel them.

**Constraints**

| Method | Decorator | Rule | Message |
|---|---|---|---|
| `_check_not_a_target` | `@api.constrains("sla_cancel")` | a flagged stage may not be the target of any rule, archived rules included (`active_test=False`) | `"'%(stage)s' is the target stage of the SLA rule '%(rule)s', so it cannot cancel SLA records."` |

**The rule's constraint cannot see this side.** `@api.constrains("target_stage_id")` fires only
when a rule's target is written, and dotted names are ignored (`odoo/api.py:180`), so flagging a
stage that is already a target needs its own check here. Archived rules are included so that
un-archiving one cannot bring the conflict back unnoticed — writing `active` triggers neither
constraint.

### `maintenance.request.sla` — `models/maintenance_request_sla.py` (step 2)

`models.Model` · `_name = "maintenance.request.sla"` · `_description = "Maintenance Request SLA"` · `_order = "id"`

One record is one commitment on one request, for one cycle. Every field is plain and written
imperatively by the engine — never a compute (design §9, the anti-pattern taken from
`helpdesk.ticket.sla`) — except `company_id` and `display_name`.

```python
STATES = [
    ("running", "Running"),
    ("paused", "Paused"),
    ("achieved", "Achieved"),
    ("achieved_late", "Achieved late"),
    ("cancelled", "Cancelled"),
]
```

| Field | Type | Attributes |
|---|---|---|
| `request_id` | Many2one → `maintenance.request` | `string="Request"`, `required=True`, `ondelete="cascade"`, `index=True` |
| `sla_id` | Many2one → `maintenance.sla` | `string="SLA Rule"`, `required=True`, `ondelete="restrict"` — a rule with records can be archived, not deleted |
| `target_stage_id` | Many2one → `maintenance.stage` | `string="Target Stage"`, `required=True`, `ondelete="restrict"`; snapshot |
| `target_sequence` | Integer | `string="Target Position"`; snapshot of the target's `sequence` — evidence of what *reached* meant, never compared against |
| `duration` | Float | `string="Target (hours)"`; snapshot |
| `at_risk_pct` | Integer | `string="At Risk (%)"`; snapshot |
| `start_at` | Datetime | `string="Clock Start"`, `required=True` |
| `state` | Selection `STATES` | `required=True`, `default="running"`, `index=True` |
| `consumed` | Float | `string="Counted (hours)"`; running time accumulated up to `last_change_at` |
| `paused_time` | Float | `string="Paused (hours)"` |
| `last_change_at` | Datetime | `string="Last Change"` |
| `deadline` | Datetime | set while running, empty otherwise |
| `risk_at` | Datetime | `string="At Risk From"`; set while running, empty otherwise |
| `reached_at` | Datetime | `string="Reached At"`; written from step 3 |
| `elapsed` | Float | `string="Elapsed (hours)"`; written from step 3 |
| `on_time` | Float | `string="On Time (%)"`, `aggregator="avg"`; written from step 3, **only** when a record finishes |
| `cycle` | Integer | `default=1` |
| `team_id` | Many2one → `maintenance.team` | dimension (divergence 6) |
| `equipment_id` | Many2one → `maintenance.equipment` | dimension |
| `category_id` | Many2one → `maintenance.equipment.category` | `string="Equipment Category"`; dimension |
| `priority` | Selection | `_request_selection(self, "priority")`; dimension |
| `maintenance_type` | Selection | `_request_selection(self, "maintenance_type")`; dimension |
| `company_id` | Many2one → `res.company` | `related="request_id.company_id"`, `store=True` (design §4.3) |

`_request_selection` is imported from `models/maintenance_sla.py`.

**`on_time` is never written until a record finishes.** A Float written `False` stores `0.0`
(`odoo/fields.py`, `Float.convert_to_column`), and an average counts zeros, so a running record
given an empty `on_time` would read as a breach in every compliance figure. Left out of the
create values, the column stays NULL, which `AVG` skips.

**The dimension Many2ones keep the default `ondelete="set null"`.** Teams and categories are
configuration a site may delete; refusing that over historical evidence would turn a report
column into a lock. The record keeps its rule, target and times either way.

**A stage that was ever a target cannot be deleted.** `target_stage_id` is `restrict` here as on
the rule, and stages have no `active` field to retire them with
(`maintenance/models/maintenance.py:10-20`), so once a record has targeted a stage it stays for as
long as that record does. Renaming or resequencing it remains possible; the record's
`target_sequence` keeps the position it had.

**The evidence is readable by every internal user** (divergence 7): no record rules, and no
delegation to the request.

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_display_name` | `@api.depends("sla_id", "request_id")` | `"<rule name> · <request display name>"`, the request's name read through `sudo()` — a reader of the evidence may not be able to read the request itself |
| `_set_deadline` | — | for each record: while `running`, `deadline = max(last_change_at, start_at) + (duration − consumed)` hours and `risk_at = deadline − (1 − at_risk_pct / 100) × duration` hours; otherwise both `False`. Step 3 calls it on every resume |

### `maintenance.request` — `models/maintenance_request.py` (step 2)

| Field | Type | Attributes |
|---|---|---|
| `reported_at` | Datetime | `string="Reported At"`, `default=fields.Datetime.now`, `tracking=True`, `copy=False`, help saying the corrective clocks start here |
| `sla_ids` | One2many → `maintenance.request.sla`, `request_id` | `string="SLA Records"`, `copy=False` (design §4.4) |

**Installing fills `reported_at` on existing requests with the install time.** Odoo initialises
a new column from the field's default (`odoo/fields.py:1145-1148`). Those requests get no SLA
records (D5), so the value is never read as a clock start; it is simply not their real report
time. On this instance that is the four test requests.

| Method | Decorator | Behaviour |
|---|---|---|
| `create` | `@api.model_create_multi` | `super()`, then `_sla_apply()` on the new requests |
| `_sla_start` | — | `ensure_one`; the clock start: `schedule_date or reported_at or create_date` for a preventive request, `reported_at or create_date` otherwise (divergence 4). `reported_at` is not required, and a caller may pass `False`; `start_at` is required, so without the last fallback the record's INSERT would fail and block the request's creation |
| `_sla_apply` | — | the one matching function (D1), below |

**`_sla_apply()` in step 2** — the creation case, on `self.sudo()` (D2):

1. Read the active rules once, in `_order`.
2. Skip a request that is archived or sits in a stage flagged `sla_cancel`: nothing is
   promised on a request that is already cancelled.
3. Per target stage, the winner is the first rule in that order whose `_matches(request)` holds.
4. For each target stage with a winner and **no record of the request on that target stage that
   is not cancelled**, create one: `sla_id` and the four snapshots from the rule; `start_at` from
   `_sla_start()`; `state` `paused` when the request's stage is among the rule's
   `pause_stage_ids`, `running` otherwise; `consumed` and `paused_time` `0.0`;
   `last_change_at = start_at`; `cycle` 1; the five dimensions from the request. Then
   `_set_deadline()` on the new records.

The guard in item 4 is what makes a second run change nothing (D8). `last_change_at = start_at` makes
a backdated `reported_at` count from the report rather than from the save, and puts a preventive
clock whose scheduled date lies ahead at rest until that date.

**The clamp, a contract for step 3.** Step 2 can create a record whose `last_change_at` and
`start_at` lie in the future. Both of step 3's time additions — to `consumed` when leaving
`running`, to `paused_time` when leaving `paused` — are therefore
`max(0, now − max(last_change_at, start_at))`. Paused time uses the same base as running time, so
a pause before the clock starts counts nothing.

What later steps add to the same function: a record reached at creation and the next cycle (step
3, D6, D11); cancelling and replacing an open record whose rule no longer wins, and refreshing
the dimensions of open records (step 4, D1, D10, divergence 6). Step 2 posts nothing to the
chatter; posts begin with the state changes of step 3.

**Step 3 narrows item 4's guard.** As written it serves creation only: it would block D11, since
a finished record already exists on the target stage and no next cycle could open. Step 3
replaces it with: the target stage has **no open record**, and its latest record is not finished
while the request sits at or past that stage. Neither form settles a request leaving a cancel
stage — its latest records are cancelled, so both would recreate cycle 1 from the original start
— which stays the open item under *Decisions for later steps*, for step 3 to answer alongside.

**On this instance `maintenance_priority_matrix` loads first**, so its `create()` runs inside
this one. Modules of equal depth load in name order (`odoo/modules/graph.py:109-117`), and
both sit one level above `maintenance`. The priority the matrix fills is therefore in place when
`_sla_apply()` runs at creation. The reverse order is answered by step 4's `write()`, where D8's
create-then-write test lives.

## Security — `security/ir.model.access.csv`

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_maintenance_sla_user` | `maintenance.sla.user` | `model_maintenance_sla` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_maintenance_sla_manager` | `maintenance.sla.manager` | `model_maintenance_sla` | `maintenance.group_equipment_manager` | 1 | 1 | 1 | 1 |
| `access_maintenance_request_sla_user` (step 2) | `maintenance.request.sla.user` | `model_maintenance_request_sla` | `base.group_user` | 1 | 0 | 0 | 0 |

**The evidence is read-only for everyone, managers included.** The engine writes it as `sudo()`,
and no row grants write, create or unlink: a record nobody can edit or delete is what R10 asks
for. Deleting a request still removes its records through `ondelete="cascade"`, as design §4.3
has it. Step 4's waiver is the one manager write, and decides its own path.

Read for every internal user for the same reason the priority grid needs it: core grants
`maintenance.request` create rights to `base.group_user`
(`maintenance/security/ir.model.access.csv:4`), and a rule table nobody can read would raise on
creation. Matching itself runs as `sudo()` (D2); the read right is for the forms and the
evidence that link to rules. `base_maintenance_group`'s *Full Access* group implies
`maintenance.group_equipment_manager`, so the manager row covers it.

## Views — `views/maintenance_sla_views.xml`

| XML id | Type | Content |
|---|---|---|
| `maintenance_sla_view_list` | list | `sequence` (`widget="handle"`), `name`, `maintenance_type`, `priority`, `target_stage_id`, `duration` (`widget="float_time"`), `at_risk_pct`, `company_id` (`groups="base.group_multi_company"`), `active` (`column_invisible="True"`) |
| `maintenance_sla_view_form` | form | archived ribbon; `name` in its own group; a *When* group (`name="conditions"`) holding `maintenance_type`, `priority`, `team_ids` and `equipment_category_ids` (both `widget="many2many_tags"`), `company_id` (`groups="base.group_multi_company"`), `domain` (`widget="domain"`, `options="{'model': 'maintenance.request'}"`); a *Then* group (`name="commitment"`) holding `target_stage_id`, `pause_stage_ids` (`widget="many2many_tags"`), `duration` (`widget="float_time"`), `at_risk_pct`; `sequence` and `active` invisible |
| `maintenance_sla_view_search` | search | fields `name`, `target_stage_id`, `priority`; filter `archived`; group by `maintenance_type`, `target_stage_id`, `priority` |
| `maintenance_sla_action` | action | name `SLA Rules`, `view_mode` `list,form`, `search_view_id`, and `help` saying that with no rules configured no commitments are created |

The two groups are labelled *When* and *Then*, as `qms.determination.rule`'s form is: a rule
reads as conditions and outputs, and the same shape in both engines means one thing to learn.

| Menu | Parent | Groups | Sequence |
|---|---|---|---|
| `menu_maintenance_sla` "SLA Rules" | `maintenance.menu_maintenance_configuration` | inherited — core's Configuration menu is `maintenance.group_equipment_manager`, to which `base_maintenance_group` adds its *Full Access* group | 30 |

## Views — `views/maintenance_stage_views.xml`

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `hr_equipment_stage_view_tree` | `maintenance.hr_equipment_stage_view_tree` | field `done` after | `sla_cancel` |

**One inheritance, because core ships no form view for a stage.** `maintenance.stage` has a
search view, an `editable="top"` list and a kanban, and nothing else
(`maintenance/views/maintenance_views.xml:696-730`) — the mirror image of the severity case in
`qms_nonconformity`, where OCA shipped a form and no list. The flag is therefore set inline in
the list, beside `fold` and `done`.

Core's *Maintenance Stages* menu is `base.group_no_one`
(`maintenance/views/maintenance_views.xml:1028-1034`, `groups` at `:1033`), so the stage list — and the flag with
it — is reached in debug mode only. Left as core has it: rearranging the stage flow is a
setup-time job.

No `optional="show"`: an optional column can be hidden, and a stage list of a handful of rows
has no crowding to relieve. A flag that silently cancels commitments should not be hideable.

## Views — `views/maintenance_request_sla_views.xml` (step 2)

| XML id | Type | Content |
|---|---|---|
| `maintenance_request_sla_view_list` | list | `create="0"`, `edit="0"`, `delete="0"`: `sla_id`, `target_stage_id`, `cycle`, `state` (`widget="badge"`, `decoration-info="state == 'running'"`, `decoration-warning="state == 'paused'"`, `decoration-success="state == 'achieved'"`, `decoration-danger="state == 'achieved_late'"`, `decoration-muted="state == 'cancelled'"`), `start_at`, `deadline`, `reached_at`, `elapsed` (`widget="float_time"`), `paused_time` (`widget="float_time"`) |
| `maintenance_request_sla_view_form` | form | `create="0"`, `edit="0"`, `delete="0"`: side by side, a *Commitment* group (`name="commitment"`) holding `request_id`, `sla_id`, `target_stage_id`, `cycle`, `duration` (`widget="float_time"`), `at_risk_pct`, and a *Clock* group (`name="clock"`) holding `state`, `start_at`, `deadline`, `risk_at`, `reached_at`, `consumed`, `paused_time`, `elapsed` (the three hour fields `widget="float_time"`); below them a *Recorded against* group (`name="dimensions"`) holding `team_id`, `equipment_id`, `category_id`, `priority`, `maintenance_type`, `company_id` (`groups="base.group_multi_company"`) |

No action and no menu in step 2: the records are reached from their request. Step 6 adds the
report action over the same list.

## Views — `views/maintenance_request_views.xml` (step 2)

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `hr_equipment_request_view_form` | `maintenance.hr_equipment_request_view_form` | field `request_date` after | `reported_at`, `readonly="id"` |
| | | `//notebook` inside | page `SLA` (`name="sla"`) holding `sla_ids` (`readonly="1"`, `nolabel="1"`), shown through `maintenance_request_sla_view_list` |

`request_date` sits in the form's first group (`maintenance/views/maintenance_views.xml:104`),
which is where the report time belongs. **`reported_at` is editable only before the first
save**, so a late entry can be backdated when it is raised and the clock starts from the real
report. Correcting it afterwards, and moving the running clocks with it, is step 4.

## Tests — `tests/test_maintenance_sla_rule.py`

**The fixtures build their own stages and rules and do not read the instance's.** The rule table
and the stage list are both configuration a site owns, and `maintenance_priority_matrix`'s tests
failed once because a real grid row occupied a fixture's pair. Stages cannot be cleared —
requests point at them — so the fixtures **create** their own and never assume which stages exist
or in what order.

Every `IntegrityError` test runs under `@mute_logger("odoo.sql_db")` with
`self.assertRaises(IntegrityError), self.cr.savepoint()`, as `maintenance_priority_matrix`'s do.
`assertRaises` already opens a savepoint (`odoo/tests/common.py:489`); the explicit one is kept
for consistency with those tests.

`TestSlaRule(TransactionCase)`, `at_install`: the fixtures create stages and rules only.

| Test | Asserts |
|---|---|
| `test_rule_requires_a_target` | a rule created without `target_stage_id` raises `IntegrityError` |
| `test_target_may_not_be_a_cancel_stage` | a rule whose target is flagged `sla_cancel` raises `ValidationError`, on create and on a write moving the target |
| `test_cancel_flag_refused_on_a_target` | flagging a stage no rule targets is accepted (the positive control); flagging a stage that is already a rule's target raises `ValidationError`, and so does flagging the target of an **archived** rule |
| `test_target_stage_delete_restricted` | deleting a stage used as a target raises `IntegrityError`; deleting a stage no rule uses succeeds |
| `test_pause_stage_delete_restricted` | deleting a stage used as a pause stage raises `IntegrityError` |
| `test_domain_refused_when_malformed` | `"[('priority', '=', '3'"` raises `ValidationError` at save |
| `test_domain_refused_when_dynamic` | `"[('user_id', '=', uid)]"` raises `ValidationError`, with the message naming the parse failure |
| `test_domain_refused_on_unknown_field` | `"[('no_such_field', '=', 1)]"` — which parses — raises `ValidationError` at save; a valid domain saves; writing the unknown field onto that saved rule raises too |
| `test_parsed_domain` | a valid domain reads back as a list, and an empty one as `[]` |
| `test_selections_are_the_requests` | the rule's `priority` and `maintenance_type` values equal `maintenance.request`'s |

## Tests — `tests/test_maintenance_request_sla.py` (step 2)

The fixtures and the helpers `_make_rule`, `_request`, `_records` and `_record` live in a shared
base class, `RequestSlaCase(TransactionCase)`, which has no tests of its own. The two test
classes inherit from it and are both `@tagged("post_install", "-at_install")`: the fixtures
create equipment, requests and users. `_records` searches for a request's records rather than
reading `sla_ids`, so no assertion depends on the one2many's cache.

**The fixtures archive every active SLA rule first**, so that the instance's configuration never
adds a record to a fixture request — the lesson of the priority grid's tests, applied here by
archiving rather than deleting, since a rule with records cannot be deleted. They create their own
stages (*new*, *in progress*, *waiting*, *restored*, and *scrap* flagged `sla_cancel`), two
teams, two categories and one machine, and two rules: *Response* targeting *in progress*, and
*Restore* targeting *restored* and pausing in *waiting*. Urgency and criticality are left unset,
so `maintenance_priority_matrix`, where installed, suggests nothing and leaves `priority` as the
fixture sets it.

`TestRequestSla(TransactionCase)`

| Test | Asserts |
|---|---|
| `test_records_created_per_target_stage` | a matching request gets one record per target stage, carrying its rule's target, target position, duration and at-risk %, `cycle` 1, `running`, nothing counted |
| `test_clock_starts_at_reported_at` | `start_at` equals `reported_at`; with `reported_at` backdated in the values, `start_at` and `deadline` follow it, `deadline = start_at + duration`, and `risk_at` sits `(1 − at_risk_pct / 100) × duration` before it |
| `test_clock_start_without_reported_at` | a request created with `reported_at=False` still gets its records, starting at its `create_date` |
| `test_lowest_sequence_wins` | of two matching rules on one target stage, only the lower sequence's creates a record |
| `test_rule_conditions` | one sub-test each for type, priority, team, category, company and domain: a request failing the condition gets no record from that rule, and one meeting it does. Each conditional rule has sequence 1 and is archived after its sub-test, so it never competes with the next. The category case creates a second machine in the second category; the company case uses two rules, one for this company and one for another company created in the test |
| `test_empty_priority_collects_only_priority_free_rules` | a request with no priority gets the record of a rule with no priority, and none from a rule naming one (D4) |
| `test_paused_at_creation` | a request created in a pause stage has its record `paused`, with no `deadline` and no `risk_at` |
| `test_preventive_clock_start` | a preventive request starts at `schedule_date`, and at `reported_at` when it has none (divergence 4) |
| `test_nothing_promised_when_cancelled` | a request created in the *scrap* stage, and one created archived, get no records |
| `test_no_rules_no_records` | with every rule archived, a request gets no records |
| `test_apply_twice_changes_nothing` | a second `_sla_apply()` on an unchanged request leaves the same records with the same values (D8) |
| `test_rule_edit_leaves_records` | changing a rule's duration and target afterwards leaves the snapshots on existing records as they were (R5) |
| `test_dimensions_copied` | team, machine, category, priority and type are copied from the request, and `company_id` follows it |
| `test_on_time_stays_null` | a new record's `on_time` column is NULL in the database, not `0.0` — read with SQL after `self.env.flush_all()`, since the ORM reads NULL as `0.0` |

`TestRequestSlaAccess(TransactionCase)` — users from `new_test_user`: a requester with
`base.group_user` only, and a manager with `maintenance.group_equipment_manager`.

| Test | Asserts |
|---|---|
| `test_requester_creates_records` | a request raised by the requester gets its records, although the requester has no create right on them — the engine runs as `sudo()` (D2). The request names no machine: core's *Users are allowed to access equipment they follow* rule applies to every internal user, and core's own computes read the machine as the requesting user (`maintenance/models/maintenance.py:305-310`, `:313-319`), so a machine the requester does not follow would fail there before this module runs. The requester is the request's responsible (`user_id`): `hr_maintenance` computes `owner_user_id` from an employee, and `create()` checks record rules before mail subscribes the creator, so without it a plain internal user fails the own-requests rule on create |
| `test_records_readable_by_any_internal_user` | on a request the requester neither owns, follows nor is assigned — and so cannot read — the requester reads its records' `state`, `deadline` and `display_name` (divergence 7; the display name through its `sudo()` read of the request) |
| `test_records_read_only_for_everyone` | the manager reads the records, and writing or deleting them raises `AccessError` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Gives maintenance requests configured response and restore commitments, measured on the stages technicians already use, and records each commitment as its own evidence: what was promised, when it was met, and whether it was on time |
