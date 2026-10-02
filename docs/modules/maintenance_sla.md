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
| 3 | The clock: stage transitions, pause and resume, reached on time and late, cancel stages and archiving, final cancellation, next cycles, chatter notes, multi-company rules | done | 2026-10-02, one pass. `exit=0`, 47 tests, 0 failures; UI checked: a commitment met on time with its note, *Scrap* cancelling with its note and refusing the way back, archiving cancelling with *Reopen Request* hidden. The UI check also showed that an archived request can still be dragged between stages in the kanban — core's behaviour, harmless to the evidence, left as it is (D13) |
| 4 | Re-matching on request changes: replacing, resuming, refreshing; waivers; `reported_at` correction | done | 2026-10-02, three runs. First `exit=0`, 66 tests; UI checked: `reported_at` corrected and then locked, a waiver from the record list, a replacement on a priority change. Reviewed afterwards: the free-text waiver reason became a configured list with an optional note (divergence 13). The next run failed `test_waiver_requires_a_reason`: a wizard row left by the UI check kept `reason_id` nullable, since `-u` cannot add `NOT NULL` over existing NULLs and only logs it at INFO. Rows deleted, upgraded again: `exit=0`, 68 tests, 0 failures, the column `NOT NULL`; UI checked: the reasons list, the wizard with a reason and a note, an archived reason not offered |
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
| 7 | §4.3 delegates access to the request with `return result or self.request_id._check_access(operation)`, as `helpdesk.ticket.sla` does | no delegation: the evidence is readable by every internal user | Settled in review on 2026-10-01: the restriction accomplishes nothing. Record access is enforced in `_search`, which `search`, `read_group` and the reading of stored fields all go through: `fetch()` reads stored fields through `_search([('id', 'in', ids)])` (`odoo/models.py:4141-4142`), and its refusal is raised from `ir.rule`, not from `_check_access` (`:4160-4164`). A `_check_access` override would therefore restrict almost nothing, not even most reads; restricting the evidence would take a `_search` override, as `mail.activity` has. What it would hide is a rule name and some times. The snippet is also defective as written: it returns the request's records as the forbidden ones, while `_filtered_access` subtracts them from this model's (`odoo/models.py:4460-4461`), which raises `TypeError` (`:6963-6964`) |
| 8 | §5.1: "Every state change is posted to the request's chatter" | outcomes only: a commitment met on time or late, a commitment cancelled, and a next cycle opened — one note per request per change, not one per record. Pausing and resuming post nothing, nor does a first record | A pause or resume is a stage change, which the request's stage tracking already writes to the chatter; a note beside it repeats it. A first record exists on every request from its creation and is on the SLA page. What the chatter cannot otherwise show is the outcome |
| 9 | §5.1 cancels open records on a cancel stage or on archiving, and does not forbid the way back | cancellation is final for a request under SLA: `write()` refuses to move it out of a cancel stage, or to un-archive it, and the form hides *Reopen Request* | A cancelled work order is final in CMMS practice; reopening is raising a new request. Odoo treats its own manufacturing orders the same way: `mrp.production` has `action_cancel` (`mrp/models/mrp_production.py:1748`) and no way back from `cancel`. And it keeps the cycle simple: a request coming back from a cancellation would need a rule for what the gap means — a new cycle from the move, or the old clock resumed — and neither is evidence of anything. Requests without SLA records keep core's behaviour |
| 10 | R10: "A manager may waive a record with a reason" | a waiver applies to a **finished** record only, through a wizard, and is permanent | A waiver is a judgement on an outcome — this breach was not the team's — so it needs an outcome to judge. An open record that should not count is a request raised by mistake, which is cancelled, and cancelled records are outside compliance already. Permanent because the waiver is itself evidence: undoing one would be rewriting it, the thing R10 forbids for the records themselves |
| 11 | §4.3 has no link between a record and the one it replaces | `replaced_id` on the record that takes over | Without it, a record cancelled by re-matching is indistinguishable from one cancelled with its request, and the chatter can only say "cancelled" where the truth is "replaced". One Many2one makes both explain themselves |
| 12 | §2: `reported_at` "may be corrected for late entry until the first clock of the request stops" | correctable until any record of the request **changes state** — pauses, finishes or is cancelled — and the correction moves only records that have not | A correction moves a record's start. Once a record has paused or resumed, its counters were booked against the old start, and moving the start under them would make the books disagree; a record that has not changed state has booked nothing yet. The lock is in the view only: a value written past it by import or code moves nothing that has changed state, so the evidence cannot be bent through it |
| 13 | R10: waive "with a reason" | the reason is picked from a configured list, `maintenance.sla.waive.reason`, with an optional free-text note beside it — the shape of core's `crm.lost.reason` and its lost wizard (`crm/models/crm_lost_reason.py`, `crm/wizard/crm_lead_lost.py:14-15`) | A list makes waivers a policy rather than a sentence each manager phrases differently, and makes them reportable: compliance can be read by waiver reason. The note keeps the specifics. Unlike CRM's, the reason is required — a waiver without a classified reason defeats the point. The module ships no reasons (the project's no-guessed-seeds rule), so nobody can waive until a manager has configured one |

## Decisions for later steps

Settled before the code exists, so that the later steps are specced against them.

| # | Decision | Step |
|---|---|---|
| D1 | **One matching function.** `_sla_apply()` on `maintenance.request`, run as `sudo()`, safe to run twice. Per target stage it computes the winner — the matching rule with the lowest `(sequence, id)` — creates the missing record, and cancels an open record whose rule is no longer the winner. `create()` and `write()` both call it; nothing else creates records | 2, 4 |
| D2 | **`sudo()` is required, not a convenience.** A Many2many read applies the comodel's record rules (`odoo/fields.py`, `Many2many.read`, `_apply_ir_rules`), and `base_maintenance_group`'s `only_subscribe_maintenance_team` would show a non-member an empty `team_ids` — which reads as *any team*. `sudo()` keeps `env.uid`, so the records still carry the real creator | 2 |
| D3 | **What a rule matches.** `maintenance_type` equal; `priority` equal or empty on the rule; `team_ids` containing the request's team or empty; `equipment_category_ids` containing the request's category or empty (exact, divergence 5); `company_id` equal or empty on the rule; `domain` satisfied | 2 |
| D4 | **An empty priority collects only the rules with no priority set.** `maintenance_priority_matrix` allows an empty priority when no grid row matches; such a request gets the site's priority-agnostic commitments and no others. Tested | 2 |
| D5 | **No backfill.** Records are created by `create()` and `write()` only. Requests that exist when the module is installed get none, and nothing re-matches when a *rule* changes. A rule created after a request never gives it a first record, at creation or at a re-match (step 4): a first record starts at `reported_at`, so a later rule would attach to an old request already overdue. The test is `rule.create_date <= request.create_date`; a rule *edited* later to match more requests keeps its old `create_date` and is not caught. Archiving a rule leaves its open records running until their request's next re-match, which replaces or cancels them; a stage change does not touch them | 2, 4 |
| D6 | **The current stage is evaluated at creation.** Step 2 creates a record `paused` when the request starts in one of its rule's pause stages. Step 3 adds the reached case: a request created at or past a target — a kanban quick-create in a later column — has that record finished straight away | 2, 3 |
| D7 | **When `write()` re-matches.** `priority`, `maintenance_team_id`, `category_id`, `maintenance_type` and `company_id` are read per record before `super()`, and `_sla_apply()` runs for the records where any of them changed. Captured, not read from `vals`: `category_id` is a stored related on `equipment_id`, so a reassigned machine changes it while `vals` names neither — the lesson `maintenance_priority_matrix` learnt for its own suggestion. A rule's `domain` is evaluated only at those moments: a change to a field only the domain reads triggers nothing. Correcting `reported_at` moves only cycle-1 records whose start came from it: a next cycle starts at its move, and a preventive record at `schedule_date` | 4 |
| D8 | **Load order does not matter.** `maintenance_priority_matrix` writes `priority` from inside its `create()`. Whichever module loads last, either our `write()` runs inside `super().create()` before our own matching, or after it. Two tests cover both: create-then-write-priority leaves exactly one record per target stage, held by the winner; and a second `_sla_apply()` on an unchanged request changes nothing | 2, 4 |
| D9 | **Reached target stages are left alone.** A target stage whose latest record is finished and which the request still sits at or past gets no new record from re-matching | 3, 4 |
| D10 | **A replacement carries the clock.** A record replacing a cancelled open one takes its `start_at`, `consumed`, `paused_time` and `cycle`; the new rule's target, duration and at-risk % apply from then on. A record with no predecessor — a rule newly matching — has no pause history, so its clock counts from `start_at` | 4 |
| D11 | **The next cycle is opened by `_sla_apply()` too.** For a target stage with no open record, whose latest record is finished, while the request now sits below that stage: a new record from the *current* winner, with `cycle + 1` and `start_at` the moment of the move. Only the latest record counts, and only when no open record exists for that stage, so a finished record cannot open a cycle twice. If priority changed in between, the next cycle follows the current rule — where design §5.2's `_open_next_cycles` reopens from the same rule, the one place this differs from it. A rejection back below several targets opens a cycle for each: back to *New*, below both, opens a *Response* cycle 2 as well as a *Restore* one | 3 |
| D12 | **A cancel stage acts on open records only.** Finished records are evidence and keep their state | 3 |
| D13 | **Cancellation is final for a request under SLA** (divergence 9). For a request with SLA records, `write()` refuses a move from a stage flagged `sla_cancel` to one that is not, and `archive=False` on an archived request — which also covers core's `reset_equipment_request` (`maintenance/models/maintenance.py:293-297`), writing both. The form hides *Reopen Request* for such a request. Requests without records keep core's behaviour. A cancelled latest record on a request that is neither archived nor in a cancel stage can therefore only have been cancelled by re-matching, which D15 answers. An archived request can still be dragged between stages in the kanban: core hides the stage bar on the form (`maintenance/views/maintenance_views.xml:86`) but enforces nothing on the server. Left as it is — no record is open to evaluate, `_sla_apply()` skips archived requests, and only the move out of a cancel stage is refused | 3 |
| D14 | **A stage change opens next cycles only.** On a stage change `_sla_apply()` runs with `next_cycles_only=True`: it may open D11's next cycle, never a first record. Otherwise a rule added after the request was raised would attach to it at its next move, counting from `reported_at` — the backfill D5 rules out, by a side door | 3 |
| D15 | **A commitment whose rule stopped matching resumes when a rule matches again.** When re-matching finds a winner for a target stage whose latest record is cancelled, and the request sits below that stage, a replacement takes over its clock as D10 does: same start, its counted and paused time, its cycle. The time in between counts nowhere — no rule applied, so nothing was promised. Telling this case from a final cancellation needs no field: a request that is archived or in a cancel stage is skipped before the table is read (D13), so any other cancelled latest record was cancelled by re-matching. At or past the target, nothing: the request reached it while uncovered, and there is no honest reached time to record | 4 |
| D16 | **Waivers.** A manager waives a finished record through a wizard asking for a configured reason and an optional note (divergences 10, 13): `waived`, `waive_reason_id`, `waive_note`, `waived_by_id`, `waived_at` are set as `sudo()`, and the request gets a note. No unwaive | 4 |
| D17 | **Correcting `reported_at`.** When a write changes the request's clock start (`_sla_start()` before and after differ), its open cycle-1 records that started there and have not changed state since — `last_change_at == start_at` — move to the new start, and their deadline follows. Every other record keeps its start. The form locks `reported_at` once any record has changed state (divergence 12). Only `reported_at` triggers a correction: changing `schedule_date` moves no preventive clock, which also keeps a late preventive job from being rescheduled out of its breach. To be revisited when preventive rules are configured | 4 |
| D18 | **Reporting.** Compliance % and average time count finished records with `waived = False` (design §6). Open commitments are counted through the Overdue and At-risk filters: `live_state` is not stored, and `_read_group_groupby` refuses a field that is not (`odoo/models.py:2096-2099`), so it cannot be a pivot row — the reason OCA `helpdesk_mgmt_sla` builds a SQL-view report, which this module does not need | 6 |

## Folder structure

```
maintenance_sla/
├── __init__.py, __manifest__.py                          # 1
├── models/
│   ├── __init__.py                                       # 1
│   ├── maintenance_sla.py                                # 1
│   ├── maintenance_stage.py                              # 1
│   ├── maintenance_sla_waive_reason.py                   # 4
│   ├── maintenance_request_sla.py                        # 2
│   └── maintenance_request.py                            # 2, 3, 4, 5
├── security/ir.model.access.csv                          # 1, 2
│           maintenance_sla_security.xml                  # 3
├── views/
│   ├── maintenance_sla_views.xml                         # 1
│   ├── maintenance_stage_views.xml                       # 1
│   ├── maintenance_request_sla_views.xml                 # 2, 4
│   ├── maintenance_request_views.xml                     # 2, 3, 4, 5
│   ├── maintenance_sla_waive_reason_views.xml            # 4
│   └── maintenance_sla_report_views.xml                  # 6
├── tests/__init__.py, test_maintenance_sla_rule.py       # 1
│         test_maintenance_request_sla.py                 # 2
│         test_maintenance_sla_clock.py                   # 3
│         test_maintenance_sla_rematch.py                 # 4
├── wizards/
│   ├── __init__.py                                       # 4
│   ├── maintenance_request_sla_waive.py                  # 4
│   └── maintenance_request_sla_waive_views.xml           # 4
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
| `data` | `security/ir.model.access.csv`, `security/maintenance_sla_security.xml` (step 3), `views/maintenance_sla_views.xml`, `views/maintenance_stage_views.xml`, `views/maintenance_request_sla_views.xml` (step 2), `views/maintenance_request_views.xml` (step 2), `views/maintenance_sla_waive_reason_views.xml` (step 4), `wizards/maintenance_request_sla_waive_views.xml` (step 4) |
| `installable` | `True` |

`mail` is declared although `maintenance` already brings it: this module posts to the request's
chatter itself (design §5.1), so the dependency is used directly rather than inherited by
accident.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models`, `from . import wizards` (step 4) |
| `wizards/__init__.py` (step 4) | `from . import maintenance_request_sla_waive` |
| `models/__init__.py` | `from . import maintenance_sla`, `from . import maintenance_stage`, `from . import maintenance_sla_waive_reason` (step 4), `from . import maintenance_request_sla` (step 2), `from . import maintenance_request` (step 2) |
| `tests/__init__.py` | `from . import test_maintenance_sla_rule`, `from . import test_maintenance_request_sla` (step 2), `from . import test_maintenance_sla_clock` (step 3), `from . import test_maintenance_sla_rematch` (step 4) |

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
| `_check_not_a_target` | `@api.constrains("sla_cancel")` | a flagged stage may not be the target of any rule, archived rules included (`active_test=False`), searched as `sudo()` so that step 3's multi-company rule cannot hide another company's rule from the check — stages carry no company | `"'%(stage)s' is the target stage of the SLA rule '%(rule)s', so it cannot cancel SLA records."` |

**The rule's constraint cannot see this side.** `@api.constrains("target_stage_id")` fires only
when a rule's target is written, and dotted names are ignored (`odoo/api.py:180`), so flagging a
stage that is already a target needs its own check here. Archived rules are included so that
un-archiving one cannot bring the conflict back unnoticed — writing `active` triggers neither
constraint.

### `maintenance.sla.waive.reason` — `models/maintenance_sla_waive_reason.py` (step 4)

`models.Model` · `_name = "maintenance.sla.waive.reason"` · `_description = "SLA Waiver Reason"` · `_order = "sequence, id"`

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `sequence` | Integer | `default=10`; orders the wizard's dropdown |
| `active` | Boolean | `default=True` |

No company: a reason is vocabulary, as `crm.lost.reason` is. A reason that has been used cannot
be deleted (`waive_reason_id` is `restrict`), so retiring one is archiving it, which also takes it
out of the wizard's dropdown.

### `maintenance.request.sla` — `models/maintenance_request_sla.py` (steps 2, 3, 4)

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
OPEN_STATES = ("running", "paused")
FINISHED_STATES = ("achieved", "achieved_late")


def _format_hours(hours):
    """Hours as H:MM, rounded to the minute."""
    minutes = round(hours * 60)
    return f"{minutes // 60}:{minutes % 60:02d}"
```

`FINISHED_STATES` is imported by `models/maintenance_request.py` for `_sla_apply()`'s guard.

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
| `replaced_id` (step 4) | Many2one → `maintenance.request.sla` | `string="Replaces"`, `ondelete="set null"`; the cancelled record this one took over from (D10, D15, divergence 11) |
| `waived` (step 4) | Boolean | `readonly=True`, `index=True` |
| `waive_reason_id` (step 4) | Many2one → `maintenance.sla.waive.reason` | `string="Waiver Reason"`, `readonly=True`, `ondelete="restrict"` |
| `waive_note` (step 4) | Char | `string="Waiver Note"`, `readonly=True` |
| `waived_by_id` (step 4) | Many2one → `res.users` | `string="Waived By"`, `readonly=True` |
| `waived_at` (step 4) | Datetime | `string="Waived At"`, `readonly=True` |
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

**The evidence is readable by every internal user** (divergence 7), within the companies they
work in: one multi-company record rule (step 3, *Security*), and no delegation to the request.

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_display_name` | `@api.depends("sla_id", "request_id")` | `"<rule name> · <request display name>"`, the request's name read through `sudo()` — a reader of the evidence may not be able to read the request itself |
| `_sla_dimensions` (step 4) | — | `ensure_one`; the dimensions as written, the same dict shape as the request's `_sla_dimensions()`, so `_sla_apply()` writes them only when something differs |
| `_set_deadline` | — | for each record: while `running`, `deadline = max(last_change_at, start_at) + (duration − consumed)` hours and `risk_at = deadline − (1 − at_risk_pct / 100) × duration` hours; otherwise both `False` |
| `_sla_close` (step 3) | — | `(now)`: for each record, adds `max(0, now − max(last_change_at, start_at))` hours to `consumed` when `running`, to `paused_time` when `paused`; then `last_change_at = now`. The clamp and the shared base are what keep a clock that starts in the future at rest: neither running nor paused time counts before `start_at` |
| `_sla_cancel` (step 3) | — | `(now)`: on the open records only — `_sla_close(now)`, `state` `cancelled`, `_set_deadline()`. Returns them |
| `_sla_note_line` (step 3) | — | `ensure_one`; the chatter line for this record's outcome, from the table under `_sla_post`, or `None` |
| `action_waive` (step 4) | — | `ensure_one`; opens the waiver wizard on this record |
| `_sla_evaluate` (step 3) | — | `(now)`: brings each **open** record in line with its request's current stage, below. Returns the records that finished or were cancelled |

**`_sla_evaluate(now)`** — per open record, against the request's stage as it is now, comparing
positions as `(sequence, id)` pairs read live (design §5.2), never `target_sequence`:

| Request's stage | Record | Effect |
|---|---|---|
| flagged `sla_cancel` | open | `_sla_cancel(now)` (D12) |
| at or past `target_stage_id` | open | `_sla_close(now)`; `reached_at = now`; `elapsed = consumed`; `state` `achieved` when `float_compare(consumed, duration, precision_digits=6) <= 0`, else `achieved_late` — `consumed` is a sum of second counts divided by 3600, so a target reached exactly at its deadline can come out a hair over and be judged late without it; `on_time` 100 or 0; `_set_deadline()` clears the deadline |
| below the target, among the rule's `pause_stage_ids` | `running` | `_sla_close(now)`; `state` `paused`; `_set_deadline()` clears it |
| below the target, not a pause stage | `paused` | `_sla_close(now)`; `state` `running`; `_set_deadline()` from the remaining time |
| below the target | already in the matching state | nothing |

**A record is written only when its state changes.** A move between two counting stages leaves a
running record exactly as it was: closing and reopening it would add nothing to the clock and
move `last_change_at`, which records the last *state* change, and re-derive a deadline that
cannot differ. It is also why a record created in step 2's initial state passes through
`_sla_evaluate` untouched unless the stage reaches or cancels it.

**Pause stages are read from the rule, live.** The snapshots are the target, the duration and
the at-risk share (design R5, §4.3); a rule's pause stages are not among them, so editing them
changes how open records treat their next stage change. Finished records are unaffected.

### `maintenance.request` — `models/maintenance_request.py` (steps 2, 3, 4)

| Field | Type | Attributes |
|---|---|---|
| `reported_at` | Datetime | `string="Reported At"`, `default=fields.Datetime.now`, `tracking=True`, `copy=False`, help saying the corrective clocks start here |
| `sla_ids` | One2many → `maintenance.request.sla`, `request_id` | `string="SLA Records"`, `copy=False` (design §4.4) |
| `reported_at_locked` (step 4) | Boolean | non-stored compute, `@api.depends("sla_ids.state", "sla_ids.start_at", "sla_ids.last_change_at")`: true when any record has changed state — not open, or `last_change_at != start_at` (D17) |

**Installing fills `reported_at` on existing requests with the install time.** Odoo initialises
a new column from the field's default (`odoo/fields.py:1145-1148`). Those requests get no SLA
records (D5), so the value is never read as a clock start; it is simply not their real report
time. On this instance that is the four test requests.

| Method | Decorator | Behaviour |
|---|---|---|
| `create` | `@api.model_create_multi` | `super()`, then `_sla_apply()` on the new requests, then `_sla_post()` with what it returns |
| `write` (step 3) | — | below |
| `_sla_start` | — | `ensure_one`; the clock start: `schedule_date or reported_at or create_date` for a preventive request, `reported_at or create_date` otherwise (divergence 4). `reported_at` is not required, and a caller may pass `False`; `start_at` is required, so without the last fallback the record's INSERT would fail and block the request's creation |
| `_sla_apply` | — | `(next_cycles_only=False, now=None)`: the one matching function (D1), below. `now` defaults to the current time; `write()` passes its own, so a stage change and the next cycle it opens share one timestamp. Returns the records it created, in their evaluated state — those finished at creation included — and those it cancelled, so `_sla_post()` sees both |
| `_sla_inputs` (step 4) | — | `ensure_one`; the re-matching inputs as a tuple: `priority`, `maintenance_type`, and the ids of `maintenance_team_id`, `category_id`, `company_id`, `equipment_id` |
| `_sla_dimensions` (step 4) | — | `ensure_one`; the dimensions a record copies, as a dict keyed by the record's field names |
| `_sla_carried_clock` (step 4) | `@api.model` | `(latest, now)`: the clock values of a replacement or a resumed record — the latest's `start_at`, `cycle`, `consumed`, `paused_time`; `last_change_at = now`; `replaced_id` the latest |
| `_sla_shift_start` (step 4) | — | `(old_starts)`: per request, the open cycle-1 records with `start_at` equal to the request's old start and `last_change_at == start_at` get `start_at` and `last_change_at` set to `_sla_start()`, then `_set_deadline()` (D17) |
| `_sla_post` (step 3) | — | `(records)`: one note per request, below; the lines come from each record's `_sla_note_line()`, and this method only groups them per request and posts |

**`_sla_apply(next_cycles_only=False, now=None)`** — on `self.sudo()` (D2):

1. Read the active rules once, in `_order`.
2. Skip a request that is archived or sits in a stage flagged `sla_cancel`: nothing is
   promised on a request that is already cancelled.
3. Per target stage, the winner is the first rule in that order whose `_matches(request)` holds.
4. For each target stage that has a winner **or** an open record, look at the request's
   **latest** record on that stage (highest `id`) and the request's position against the stage.
   With `next_cycles_only` (a stage change, D14) only the next-cycle row applies:

   | Latest record | Request's stage | Winner | Result |
   |---|---|---|---|
   | none | any | yes, created no later than the request (D5) | a first record |
   | open | below the target | its own rule | kept; its five dimensions refreshed from the request (divergence 6) |
   | open | below the target | another rule | replaced (D10): `_sla_cancel(now)`, then a replacement |
   | open | below the target | none | `_sla_cancel(now)` |
   | cancelled | below the target | yes | resumed (D15): a replacement |
   | cancelled | at or past the target | any | nothing |
   | finished | at or past the target | any | nothing (D9) |
   | finished | below the target | yes | the next cycle (D11) |

   An open record is always below its target here: `write()` evaluates open records against a
   stage change before it re-matches, and a new record is evaluated as it is created.

5. A new record takes: `sla_id` and the four snapshots from the winner; `state` `paused` when the
   request's stage is among the winner's `pause_stage_ids`, `running` otherwise; the five
   dimensions from the request; and by kind —

   | Kind | `start_at` | `last_change_at` | `cycle` | `consumed`, `paused_time` | `replaced_id` |
   |---|---|---|---|---|---|
   | first record | `_sla_start()` | `start_at` | 1 | `0.0` | — |
   | next cycle | `now` | `now` | the latest's + 1 | `0.0` | — |
   | replacement (replaced or resumed) | the latest's | `now` | the latest's | the latest's, after its `_sla_cancel(now)` | the latest |

   A replacement takes the winner's snapshots and pause stages: the new rule's target, duration
   and at-risk share apply from the moment it takes over, against the time already counted.

6. `_set_deadline()`, then `_sla_evaluate(now)` on the new records: a request created at or past a
   target has that record finished at once (D6).

The table is what makes a second run change nothing (D8): after one run, every target stage with
a winner holds an open record of that winner, a finished record at or past it, or nothing it may
act on — and the rows that act only fire where that is not yet so.
`last_change_at = start_at` makes a backdated `reported_at` count from the report rather than from
the save, and puts a preventive clock whose scheduled date lies ahead at rest until that date.


**`write(vals)` (steps 3, 4)**

| Moment | Behaviour |
|---|---|
| before `super()` | for a request with SLA records, raise `UserError` (D13) when `vals` moves it from a stage flagged `sla_cancel` to one that is not, or when `vals` has `archive` falsy while the request is archived: `"%(request)s was cancelled with SLA commitments recorded against it, so it cannot be reopened. Raise a new request instead."` |
| | per record, by `id`: the stage when `vals` has `stage_id`; the clock start `_sla_start()` when `vals` has `reported_at` (step 4); and on every write the six re-matching inputs — `priority`, `maintenance_team_id`, `category_id`, `maintenance_type`, `company_id`, and `equipment_id`, a dimension that can change while the category does not (step 4, D7) |
| after `super()`, on `self.sudo()` with `now` read once | when `vals.get("archive")`, `_sla_cancel(now)` on the requests' open records (design §5.1: archiving hides a request without changing its stage, so nothing else would stop its clocks) |
| | where the clock start changed, `_sla_shift_start(old_start)` (step 4, D17) |
| | the requests whose stage actually changed get `_sla_evaluate(now)` on their open records |
| | the requests whose re-matching inputs changed get `_sla_apply(now=now)`; the others whose stage changed get `_sla_apply(next_cycles_only=True, now=now)` (step 4) |
| | `_sla_post()` with every record cancelled, finished or created above |

**The inputs are captured, not read from `vals`** (D7): `category_id` is a stored related on
`equipment_id`, and `maintenance_priority_matrix` writes `priority` from inside its own `write()`
and `create()`. Comparing before and after catches both, and the matrix's nested write re-enters
this one — which is what makes load order irrelevant (D8): whichever runs first, the second
`_sla_apply()` finds the winner already holding each stage.

Comparing the stage before and after, rather than testing for the key, keeps a write that sets the
stage a request already has — a form saved unchanged, an import — from doing anything. Core's
own nested writes after a stage change (`close_date`, `kanban_state`,
`maintenance/models/maintenance.py:343-365`) do not carry `stage_id`, so they pass through without
effect.

**`_sla_post(records)`** — on the sudo requests, through `_message_log` (`mail/models/mail_thread.py:2826`):
an internal note, no notification. One note per request, one line per record, in `id` order:

| Record | Line |
|---|---|
| `achieved` | `"%(rule)s met on time: %(elapsed)s of %(target)s"` |
| `achieved_late` | `"%(rule)s met late: %(elapsed)s of %(target)s"` |
| `cancelled` | `"%(rule)s cancelled"` |
| open, with `replaced_id` of the same rule (step 4) | `"%(rule)s resumed"` |
| open, with `replaced_id` of another rule (step 4) | `"%(old)s replaced by %(rule)s"` |
| open, `cycle` > 1 | `"%(rule)s: cycle %(cycle)s started"` |
| open, `cycle` 1 | no line |
| `cancelled`, with its replacement among the same records (step 4) | no line — the replacement's line says it |

A waiver posts its own note from the wizard: `"%(rule)s waived: %(reason)s"`.

Hours are shown as `H:MM`, rounded to the minute. A request with no line gets no note. The lines
are passed through `self.env._` and joined as escaped HTML, so a rule name cannot inject markup.

**On this instance `maintenance_priority_matrix` loads first**, so its `create()` runs inside
this one. Modules of equal depth load in name order (`odoo/modules/graph.py:109-117`), and
both sit one level above `maintenance`. The priority the matrix fills is therefore in place when
`_sla_apply()` runs at creation. The reverse order is answered by step 4's `write()`, where D8's
create-then-write test lives.

### `maintenance.request.sla.waive` — `wizards/maintenance_request_sla_waive.py` (step 4)

`models.TransientModel` · `_name = "maintenance.request.sla.waive"` · `_description = "Waive an SLA Record"`

| Field | Type | Attributes |
|---|---|---|
| `sla_record_id` | Many2one → `maintenance.request.sla` | `required=True`, `readonly=True` |
| `reason_id` | Many2one → `maintenance.sla.waive.reason` | `string="Reason"`, `required=True`; archived reasons are not offered, a Many2one dropdown searching active records only |
| `note` | Char | optional |

| Method | Behaviour |
|---|---|
| `action_confirm` | `ensure_one`. Raise `UserError` unless the record is finished and not yet waived. Then, as `sudo()`: `waived = True`, `waive_reason_id`, `waive_note`, `waived_by_id` the user, `waived_at` now; and a note on the request, `"%(rule)s waived: %(reason)s"`, or, when a note is given, the second translatable message `"%(rule)s waived: %(reason)s — %(note)s"` — not text appended outside the translation |

**The access row is the guard.** The wizard writes the evidence as `sudo()`, so what stops a
non-manager is that only `maintenance.group_equipment_manager` has an access row on the wizard
model: without it a user can neither create the wizard nor call its methods over RPC, since
access rights apply to transient models too. The button's `groups` only hides it.

## Security — `security/ir.model.access.csv`

| id | name | model_id:id | group_id:id | r | w | c | u |
|---|---|---|---|---|---|---|---|
| `access_maintenance_sla_user` | `maintenance.sla.user` | `model_maintenance_sla` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_maintenance_sla_manager` | `maintenance.sla.manager` | `model_maintenance_sla` | `maintenance.group_equipment_manager` | 1 | 1 | 1 | 1 |
| `access_maintenance_request_sla_user` (step 2) | `maintenance.request.sla.user` | `model_maintenance_request_sla` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_maintenance_request_sla_waive_manager` (step 4) | `maintenance.request.sla.waive.manager` | `model_maintenance_request_sla_waive` | `maintenance.group_equipment_manager` | 1 | 1 | 1 | 0 |
| `access_maintenance_sla_waive_reason_user` (step 4) | `maintenance.sla.waive.reason.user` | `model_maintenance_sla_waive_reason` | `base.group_user` | 1 | 0 | 0 | 0 |
| `access_maintenance_sla_waive_reason_manager` (step 4) | `maintenance.sla.waive.reason.manager` | `model_maintenance_sla_waive_reason` | `maintenance.group_equipment_manager` | 1 | 1 | 1 | 1 |

**The evidence is read-only for everyone, managers included.** The engine writes it as `sudo()`,
and no row grants write, create or unlink: a record nobody can edit or delete is what R10 asks
for. Deleting a request still removes its records through `ondelete="cascade"`, as design §4.3
has it. The waiver is the one manager write, and goes through its wizard (D16).

Read for every internal user for the same reason the priority grid needs it: core grants
`maintenance.request` create rights to `base.group_user`
(`maintenance/security/ir.model.access.csv:4`), and a rule table nobody can read would raise on
creation. Matching itself runs as `sudo()` (D2); the read right is for the forms and the
evidence that link to rules. `base_maintenance_group`'s *Full Access* group implies
`maintenance.group_equipment_manager`, so the manager row covers it.

## Security — `security/maintenance_sla_security.xml` (step 3)

| XML id | Model | Groups | Domain |
|---|---|---|---|
| `maintenance_sla_comp_rule` | `model_maintenance_sla` | none (global) | `[('company_id', 'in', company_ids + [False])]` |
| `maintenance_request_sla_comp_rule` | `model_maintenance_request_sla` | none (global) | `[('company_id', 'in', company_ids + [False])]` |

Named *Maintenance SLA Rule Multi-company rule* and *Maintenance Request SLA Multi-company rule*,
and declared the way core declares `maintenance_request_comp_rule`
(`maintenance/security/maintenance.xml:43-47`): no groups and no `global` field, which
`ir.rule` computes from the absence of groups (`base/models/ir_rule.py:53`).

**A company boundary, not the request-level restriction divergence 7 declines.** The instance
runs two companies; without these, each company's managers would see the other's rules in
configuration, and step 6's pivot would mix both companies' evidence. A rule with no company
stays visible to all, as the priority grid's rows do. Matching runs as `sudo()` (D2), so neither
rule affects which records a request gets — and `_check_not_a_target` searches as `sudo()` for the
same reason.

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

## Views — `views/maintenance_sla_waive_reason_views.xml` (step 4)

| XML id | Type | Content |
|---|---|---|
| `maintenance_sla_waive_reason_view_list` | list | `editable="bottom"`: `sequence` (`widget="handle"`), `name`, `active` (`column_invisible="True"`) |
| `maintenance_sla_waive_reason_view_search` | search | field `name`; filter `archived` |
| `maintenance_sla_waive_reason_action` | action | name `Waive Reasons`, `view_mode` `list`, `search_view_id`, and `help` saying that SLA records can be waived only once a reason exists |

| Menu | Parent | Groups | Sequence |
|---|---|---|---|
| `menu_maintenance_sla_waive_reason` "Waive Reasons" | `maintenance.menu_maintenance_configuration` | inherited | 40 |

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

## Views — `views/maintenance_request_sla_views.xml` (steps 2, 4)

| XML id | Type | Content |
|---|---|---|
| `maintenance_request_sla_view_list` | list | `create="0"`, `edit="0"`, `delete="0"`: `sla_id`, `target_stage_id`, `cycle`, `state` (`widget="badge"`, `decoration-info="state == 'running'"`, `decoration-warning="state == 'paused'"`, `decoration-success="state == 'achieved'"`, `decoration-danger="state == 'achieved_late'"`, `decoration-muted="state == 'cancelled'"`), `start_at`, `deadline`, `reached_at`, `elapsed` (`widget="float_time"`), `paused_time` (`widget="float_time"`) |
| `maintenance_request_sla_view_form` | form | `create="0"`, `edit="0"`, `delete="0"`: side by side, a *Commitment* group (`name="commitment"`) holding `request_id`, `sla_id`, `target_stage_id`, `cycle`, `duration` (`widget="float_time"`), `at_risk_pct`, and a *Clock* group (`name="clock"`) holding `state`, `start_at`, `deadline`, `risk_at`, `reached_at`, `consumed`, `paused_time`, `elapsed` (the three hour fields `widget="float_time"`); below them a *Recorded against* group (`name="dimensions"`) holding `team_id`, `equipment_id`, `category_id`, `priority`, `maintenance_type`, `company_id` (`groups="base.group_multi_company"`) |

Step 4 adds:

| View | Change |
|---|---|
| list | `waived` (`optional="show"`); a `action_waive` button (`type="object"`, `string="Waive"`, `icon="fa-gavel"`, `groups="maintenance.group_equipment_manager"`, `invisible="waived or state not in ('achieved', 'achieved_late')"`) |
| form | a header with the same button; `replaced_id` in the *Clock* group (`invisible="not replaced_id"`); a *Waiver* group (`name="waiver"`, `invisible="not waived"`) holding `waive_reason_id`, `waive_note`, `waived_by_id`, `waived_at` |

No action and no menu in step 2: the records are reached from their request. Step 6 adds the
report action over the same list.

## Views — `views/maintenance_request_views.xml` (steps 2, 3, 4)

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `hr_equipment_request_view_form` | `maintenance.hr_equipment_request_view_form` | field `request_date` after | `reported_at`, `readonly="reported_at_locked"` (step 4; `readonly="id"` in step 2); `reported_at_locked`, `invisible="1"` |
| | | `//notebook` inside | page `SLA` (`name="sla"`) holding `sla_ids` (`readonly="1"`, `nolabel="1"`), shown through `maintenance_request_sla_view_list` |
| | | button `reset_equipment_request`, `position="attributes"` (step 3) | `invisible` becomes `not archive or sla_ids` — core has `not archive` (`maintenance/views/maintenance_views.xml:85`); D13 |

`request_date` sits in the form's first group (`maintenance/views/maintenance_views.xml:104`),
which is where the report time belongs. **`reported_at` is editable only before the first
save** in step 2; from step 4 it stays editable until a record of the request changes state
(D17, divergence 12), and a correction moves the records that have not.

## Views — `wizards/maintenance_request_sla_waive_views.xml` (step 4)

| XML id | Type | Content |
|---|---|---|
| `maintenance_request_sla_waive_view_form` | form | `sla_record_id` (`force_save="1"`), `reason_id` (`options="{'no_create': True}"`), `note`; a footer with `action_confirm` (`string="Waive"`, `class="btn-primary"`) and a cancel button (`special="cancel"`) |
| `maintenance_request_sla_waive_action` | action | `res_model` `maintenance.request.sla.waive`, `view_mode` `form`, `target` `new`; opened by `action_waive` with `default_sla_record_id` in the context |

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
| `test_company_boundary` (step 3) | a user of the main company alone does not find a rule of a second company, nor the records of a request raised in it, and does find a company-less rule and the records of a main-company request. The second company's request names its own team and no machine, so the request's company checks pass |
| `test_cancel_flag_sees_other_company_rules` (step 3) | a manager of the main company alone flagging a stage that a rule of a second company targets raises `ValidationError`: `_check_not_a_target` searches as `sudo()`, so the multi-company rule does not hide that rule from the check |

## Tests — `tests/test_maintenance_sla_clock.py` (step 3)

`TestSlaClock(RequestSlaCase)`, `@tagged("post_install", "-at_install")`, importing the base
class from `test_maintenance_request_sla`. Time is fixed with `freezegun.freeze_time`, which the
container provides and OCA's `maintenance_plan` tests already use: each request is created at a
fixed `T0` and moved at `T0` plus a number of hours, so every duration is exact. With the
fixture rules, *Response* is 1 hour at 75 % and *Restore* 8 hours at 50 %, pausing in *waiting*.

| Test | Asserts |
|---|---|
| `test_target_reached_on_time` | moved to *in progress* at +0:30, *Response* is `achieved`, `reached_at` +0:30, `elapsed` 0.5, `on_time` 100, no deadline; *Restore*, still below its target, is untouched — `last_change_at` `T0`, deadline `T0` + 8 |
| `test_target_reached_late` | moved at +2, *Response* is `achieved_late`, `elapsed` 2.0, `on_time` 0 |
| `test_reached_exactly_at_the_deadline` | *Restore* paused from +0:20 to +0:40, then the request moved to *restored* at the record's own deadline: `achieved`, `on_time` 100 — the `float_compare` boundary |
| `test_later_stage_counts_as_reached` | moved from *new* straight to *restored* at +3, both are finished: *Response* late, *Restore* on time |
| `test_pause_and_resume` | +1 *in progress*; +2 *waiting*: *Restore* `paused`, `consumed` 2.0, no deadline; +5 *in progress*: `running`, `paused_time` 3.0, deadline `T0` + 11, `risk_at` `T0` + 7; +6 *restored*: `achieved`, `elapsed` 3.0, `paused_time` 3.0 |
| `test_cancel_stage_cancels_open_records_only` | +1 *in progress*, +2 *scrap*: *Restore* `cancelled` with `consumed` 2.0; *Response* stays `achieved` with its `reached_at` (D12) |
| `test_archiving_cancels_open_records` | `archive_equipment_request()` at +1 cancels both |
| `test_cancelled_request_cannot_come_back` | for a request with records: moved to *scrap*, a move back to *new* raises `UserError`; archived, `reset_equipment_request()` raises `UserError` (D13) |
| `test_request_without_records_reopens_freely` | with every rule archived, a request moved to *scrap* moves back, and an archived one is reopened by `reset_equipment_request()` — core's behaviour |
| `test_reopen_hidden_under_sla` | in the request form's arch from `get_view`, the `reset_equipment_request` button carries `invisible="not archive or sla_ids"` |
| `test_rejection_opens_the_next_cycle` | +1 *in progress*, +3 *restored*, +4 back to *in progress*: a second *Restore* record, `cycle` 2, `start_at` +4, `running`, deadline +12; the first is untouched; *Response*, still reached, gets nothing (D9). A second request rejected from *restored* back to *new* gets a cycle 2 of both *Response* and *Restore* |
| `test_next_cycle_opens_once` | after the rejection, +5 *waiting* and +6 *in progress* still leave exactly two *Restore* records |
| `test_next_cycle_follows_the_current_rule` | a lower-sequence rule on *restored*, added after the first cycle finished, holds the second cycle (D11) |
| `test_reached_at_creation` | a request created in *in progress* with `reported_at` two hours back has *Response* `achieved_late` at once, `elapsed` 2.0, `reached_at` `T0` (D6) |
| `test_clock_at_rest_before_its_start` | a preventive rule pausing in *waiting*, on a request scheduled for +48: moved to *waiting* at +1, then to *new* at +50 — `consumed` 0.0, `paused_time` 2.0, deadline +50 plus the target (the clamp) |
| `test_unchanged_stage_does_nothing` | writing the stage the request already has changes no record and posts no note |
| `test_new_rule_not_picked_up_on_stage_change` | a rule created after the request, on a stage it has no record for, gives it no record when it moves (D14) |
| `test_outcomes_posted` | +2 *in progress*, +3 *waiting*, +4 *scrap*: one note naming *Response* met late with `2:00 of 1:00`, one naming *Restore* cancelled, and no note for the pause |
| `test_next_cycle_posted` | the rejection of `test_rejection_opens_the_next_cycle` posts a note naming *Restore* and cycle 2 |

## Tests — `tests/test_maintenance_sla_rematch.py` (step 4)

Both classes `@tagged("post_install", "-at_install")`, on a shared base class `RematchCase(RequestSlaCase)` that holds
the fixed-time helpers and has no tests of its own; `T0` and `at()` are imported from the step 3
tests, and time is fixed by `freeze_time` as there (requests created at `T0`).

`TestSlaRematch(RequestSlaCase)`

| Test | Asserts |
|---|---|
| `test_priority_change_replaces_the_record` | with a priority-3 rule of sequence 1 on *in progress*, a priority-2 request raised at `T0` and raised to priority 3 at +1: the old record `cancelled` with `consumed` 1.0; the new one held by the priority-3 rule, `replaced_id` the old one, `start_at` `T0`, `consumed` 1.0, `cycle` 1, `last_change_at` +1, deadline +1 plus its duration less 1 (D10) |
| `test_one_open_record_per_target_stage` | created, then priority written straight away: exactly one open record per target stage, each held by the winner, and a further `_sla_apply()` changes nothing (D8) |
| `test_rule_no_longer_matching_cancels` | with only a team-A rule on *in progress*, moving the request to team B at +1 cancels its record and posts *cancelled* |
| `test_matching_again_resumes_the_clock` | moved back to team A at +3: a replacement of the same rule, `replaced_id` the cancelled record, `start_at` `T0`, `consumed` 1.0, `last_change_at` +3 — the two hours uncovered count nowhere — and a *resumed* note (D15) |
| `test_reassigned_machine_rematches` | with a category-Y rule of sequence 1, moving the request to a machine in category Y — `vals` carrying only `equipment_id` — replaces its record (D7) |
| `test_newly_matching_rule_creates_a_first_record` | a priority-1 rule on a stage the request has no record for gives it a first record, starting at `reported_at`, when its priority becomes 1 |
| `test_rule_created_later_gives_no_first_record` | a priority-1 rule on a stage the request has no record for, its `create_date` set an hour after the request's with SQL — within a test every record shares the transaction's timestamp (`odoo/sql_db.py:527-532`) — gives no record when the request's priority becomes 1 (D5) |
| `test_finished_records_untouched` | after *Response* is reached, a priority change that makes another rule win on *in progress* leaves the finished record as it was and adds none (D9) |
| `test_dimensions_refreshed_while_open` | after *Response* is reached, moving the request to team B updates `team_id` on the open *Restore* record and not on the finished *Response* one (divergence 6) |
| `test_domain_read_only_when_rematching` | a rule whose domain matches on the request's name gives it nothing when only the name changes, and wins once the priority changes (D7) |
| `test_reported_at_correction_moves_unchanged_clocks` | `reported_at` set an hour earlier at +0:30: both records' `start_at` and `last_change_at` follow it, and *Restore*'s deadline moves an hour earlier (D17) |
| `test_reported_at_correction_leaves_changed_clocks` | after *Response* is reached at +1, the same correction leaves *Response* as it was and moves *Restore*, which has not changed state |
| `test_reported_at_locked_once_a_record_changes_state` | `reported_at_locked` is false on a new request and true once *Response* is reached |

`TestSlaWaiver(RequestSlaCase)` — a reason fixture, and users from `new_test_user`: a manager with
`maintenance.group_equipment_manager`, and a requester with `base.group_user` only.

| Test | Asserts |
|---|---|
| `test_manager_waives_a_finished_record` | the manager waives a late *Response* through the wizard with a reason and a note: `waived`, `waive_reason_id`, `waive_note`, `waived_by_id` the manager, `waived_at` set, and a note on the request naming the reason and the note |
| `test_waiver_requires_a_reason` | creating the wizard without `reason_id` raises `IntegrityError` under `mute_logger("odoo.sql_db")`: the ORM has no Python required check, so a required field fails at the column's `NOT NULL` |
| `test_archived_reason_not_offered` | an archived reason is absent from `name_search` on the reason model, which is what the wizard's dropdown runs |
| `test_waiver_refused_for_an_open_record` | the wizard on a running record raises `UserError` |
| `test_waiver_refused_twice` | a second waiver of the same record raises `UserError` |
| `test_waiver_refused_for_a_non_manager` | the requester creating the wizard raises `AccessError` — the access row is the guard |
| `test_waive_hidden_from_non_managers` | in the record list's arch from `get_view`, as each user sees it: the `action_waive` button is present for the manager and absent for the requester. View processing strips `groups` attributes, so the attribute itself cannot be asserted |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Gives maintenance requests configured response and restore commitments, measured on the stages technicians already use, and records each commitment as its own evidence: what was promised, when it was met, and whether it was on time |
