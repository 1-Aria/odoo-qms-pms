# maintenance_sla_garment

A starting SLA configuration for garment manufacturing: the stage flow, response and restore
targets per priority, the priority grid and the waive reasons. Install it on top of
`maintenance_sla` and `maintenance_priority_matrix` to have commitments measured from day one,
then tune the values in *Configuration*.
Design: `docs/Maintenance SLA Engine — Technical Design.md` — §3.1 (the company configuration
module), §5.4 (the stage flow), §8 (targets to be agreed). Plan: §8.

The engines carry no business values (`maintenance_priority_matrix` divergence 2,
`maintenance_sla` divergence 13 and the project's no-guessed-seeds rule); this module is where
they live, as an opt-in preset. Nothing in it is code the engines depend on.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The whole module: stages, rules, grid, waive reasons, the install hook, tests, readme | done | 2026-10-03, one pass. `exit=0`, 6 tests, 0 failures; UI checked: the seven-stage board, ten rules, the 15-cell grid, four waive reasons, a High-priority request through pause, restore and a second cycle, and the Vietnamese name of *Done* kept from core |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §3.1: `<company>_maintenance_sla_config`, company-specific, data only | `maintenance_sla_garment`, a preset for an industry, no company in it | It lives in the public `addons/` repo, which carries no company data. Rules and grid rows have no company, so they apply to every company, as the engines' own unconfigured rows do. A site makes the values its own by editing them after install |
| 2 | §3.1: data only | data files for the records it owns, and a `post_init_hook` for everything touching records it does not own — core's stages, rules targeting core's *In Progress*, grid pairs a site may already have | The project's rule that seeding must be safe to fail: a data record naming a foreign XML id raises at install when that record is missing, and a grid row for a pair already configured violates the matrix's unique index. The hook skips both instead |
| 3 | §3.1 lists escalation Automated Actions | none, and no `base_automation` dependency | Escalation, preventive *Completion* rules and auto-confirming restores are configuration a site adds when it wants them (design §7); none is needed to start measuring |
| 4 | §5.4 renames *New Request* to *New* | *New Request* kept; only *Repaired* is renamed, to *Done* | *Repaired* directly after *Restored – to confirm* reads as the same thing. *New Request* is only cosmetic |

## The values — proposed, to confirm

Design §8 suggests running a few weeks on placeholder targets, then agreeing real ones with
production. These are those placeholders, chosen for sewing lines: many small, swappable
machines, a mechanic on the floor, and a line that loses output by the minute.

**Stage flow** (design §5.4)

| Sequence | Stage | Source | SLA role |
|---|---|---|---|
| 1 | New Request | core `maintenance.stage_0` | clocks running |
| 2 | In Progress | core `maintenance.stage_1` | target of the Response rules |
| 3 | Waiting for Parts | this module | pause stage of the Restore rules |
| 4 | Waiting for Production | this module | pause stage of the Restore rules |
| 5 | Restored – to Confirm | this module | target of the Restore rules; **not** `done` (design §5.4) |
| 6 | Done | core `maintenance.stage_3`, renamed from *Repaired* | `done` |
| 7 | Scrap | core `maintenance.stage_4` | `done`, flagged `sla_cancel` |

**Targets** (hours; at risk from 75 %)

| Priority | Response — reach *In Progress* | Restore — reach *Restored – to Confirm* |
|---|---|---|
| High (`3`) | 0:15 | 2:00 |
| Normal (`2`) | 1:00 | 8:00 |
| Low (`1`) | 4:00 | 24:00 |
| Very Low (`0`) | 24:00 | 72:00 |
| no priority | 1:00 | 8:00 |

The *no priority* pair is a fallback with a higher sequence (100 against 10), so it applies only
where no priority rule matches: a corrective request whose machine has no criticality gets no
suggested priority, and would otherwise carry no commitment at all. All rules are corrective.

**Priority grid** (`maintenance_priority_matrix`; criticality × urgency → priority)

| Criticality | Safety risk | Line stopped | Producing defects | Degraded operation | No production impact |
|---|---|---|---|---|---|
| A — critical | High | High | High | Normal | Low |
| B — important | High | High | Normal | Normal | Low |
| C — minor | High | Normal | Normal | Low | Very Low |

Safety is always *High*. A minor machine stopping a line is *Normal*: on a sewing line a minor
machine is one a spare replaces.

**Waive reasons**, in this order: *Power or utility outage*; *Production refused access to the
machine*; *External contractor or supplier delay*; *Not a maintenance fault*.

## Folder structure

```
maintenance_sla_garment/
├── __init__.py, __manifest__.py, hooks.py
├── data/
│   ├── maintenance_stage_data.xml
│   ├── maintenance_sla_data.xml
│   └── maintenance_sla_waive_reason_data.xml
├── tests/__init__.py, test_garment_preset.py
└── readme/ DESCRIPTION.md, USAGE.md
```

No `models/`, `security/` or `views/`: the module adds no model, field, access or view.

## Manifest

| Key | Value |
|---|---|
| `name` | `Maintenance SLA: Garment Manufacturing` |
| `summary` | `A starting SLA configuration for garment manufacturing: stage flow, targets, priority grid, waive reasons` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Maintenance` |
| `depends` | `maintenance_sla`, `maintenance_priority_matrix` |
| `data` | `data/maintenance_stage_data.xml`, `data/maintenance_sla_waive_reason_data.xml`, `data/maintenance_sla_data.xml` |
| `post_init_hook` | `post_init_hook` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from .hooks import post_init_hook` |
| `tests/__init__.py` | `from . import test_garment_preset` |

## Data — records this module owns

All three files are `noupdate="1"`: after install the records belong to the site, and an upgrade
of this module does not overwrite what was tuned.

| File | XML ids | Content |
|---|---|---|
| `data/maintenance_stage_data.xml` | `stage_waiting_parts`, `stage_waiting_production`, `stage_restored` | the three new stages at sequences 3, 4 and 5; none `done` or folded |
| `data/maintenance_sla_waive_reason_data.xml` | `waive_reason_power`, `waive_reason_access`, `waive_reason_contractor`, `waive_reason_not_a_fault` | the four reasons, sequences 10 to 40 |
| `data/maintenance_sla_data.xml` | `sla_restore_high`, `_normal`, `_low`, `_very_low`, `_any` | the five Restore rules: corrective, the priority (none for `_any`), target `stage_restored`, pause `stage_waiting_parts` and `stage_waiting_production`, the duration from the table; sequence 10, and 100 for `_any` |

Every reference in these files is to this module's own records, so none can be missing.

## The install hook — `hooks.py`

`post_init_hook(env)` runs three helpers, each safe to run again and each skipping what it cannot
find. The values sit in module-level constants, so the tables above and the code are one list.

| Helper | Behaviour |
|---|---|
| `_arrange_stages(env)` | through `env.ref(xml_id, raise_if_not_found=False)`, skipping a stage that is missing: core's *New Request* to sequence 1, *In Progress* to 2, *Repaired* to 6 renamed *Done*, *Scrap* to 7 with `sla_cancel = True`. Resequencing changes no ids, so existing requests keep their stages |
| `_create_response_rules(env)` | when `maintenance.stage_1` exists, creates the five Response rules targeting it — `sla_response_high`, `_normal`, `_low`, `_very_low`, `_any` — each registered under this module's XML id with `noupdate=True`, and skipped when that XML id already resolves |
| `_fill_priority_grid(env)` | creates each of the 15 company-less grid rows whose pair is not already taken, archived rows included (`active_test=False`) — the unique index counts them too. A pair a site has configured keeps its value |

**The Response rules are created by the hook, the Restore rules by data**: the first target
core's *In Progress*, a foreign record, the second only this module's own stages.

**Renaming *Repaired*** writes the stage's `name` with `lang="en_US"`: the module is English
only, so another installed language — Vietnamese on this instance — keeps core's translation of
*Repaired*, and the new stages, rules and reasons exist in English alone.

## Tests — `tests/test_garment_preset.py`

`TestGarmentPreset(TransactionCase)`, `@tagged("post_install", "-at_install")`. Each test calls
the hook or a helper inside its own transaction and asserts the result, rather than reading what
the install left: a site's later tuning would otherwise break the run.

| Test | Asserts |
|---|---|
| `test_stage_flow` | after `_arrange_stages`, the seven stages read in order by `(sequence, id)`: *New Request*, *In Progress*, *Waiting for Parts*, *Waiting for Production*, *Restored – to Confirm*, *Done*, *Scrap*; *Scrap* cancels SLA; *Restored – to Confirm* is not `done` and *Done* is |
| `test_restore_rules_pause_in_waiting_stages` | each Restore rule targets *Restored – to Confirm* and pauses in both waiting stages |
| `test_every_priority_covered` | the Response rules, and the Restore rules, carry each of the request's priorities once and a fallback with none |
| `test_hook_runs_again_without_duplicates` | a second `post_init_hook(env)` creates no rule and no grid row |
| `test_grid_keeps_a_configured_pair` | with the grid cleared and one pair set to a value of its own, `_fill_priority_grid` adds the other 14 and leaves that one as it was |
| `test_hook_survives_missing_core_stages` | with the XML ids of core's four stages and of the preset's Response rules removed — `ir.model.data.unlink()` clears the lookup cache (`base/models/ir_model.py:2349-2351`) — `post_init_hook(env)` completes without error, creates no Response rule and changes no stage: the safe-to-fail path |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | A starting SLA configuration for garment manufacturing — the stage flow with waiting and confirmation stages, response and restore targets for each priority, a priority grid and waive reasons — so that commitments are measured from the day `maintenance_sla` is installed |
| `readme/USAGE.md` | **Meant to stay installed**: uninstalling deletes the records it created that are not in use and keeps those that are (`base/models/ir_model.py:2538-2575` attempts each deletion in a savepoint), keeps the grid rows, which it never owned, and does not undo the stage changes. **Installing rearranges core's stages and renames *Repaired* to *Done*.** **English names only**: in another language *Done* keeps core's translation of *Repaired*, and the new stages, rules and reasons show in English. **The values are a starting point, not a standard**: placeholders to run for a few weeks, then to agree with production and change in *Configuration* — SLA Rules, Priority Rules, Waive Reasons, Maintenance Stages. Installing never overwrites a configured priority pair, and upgrading never overwrites tuned values. The tables of stages, targets and grid as installed. *Restored – to Confirm* is where a technician leaves a machine once it runs again; moving it to *Done* is the requester's confirmation |
