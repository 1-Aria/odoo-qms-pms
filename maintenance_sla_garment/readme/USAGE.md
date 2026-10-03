## Before installing

**The values are a starting point, not a standard.** They are placeholders for sewing lines —
many small, swappable machines and a line that loses output by the minute — meant to run for a
few weeks and then be agreed with production and changed in *Maintenance → Configuration*:
SLA Rules, Priority Rules, Waive Reasons and Maintenance Stages.

- **Installing rearranges core's stages** around three new ones, and renames *Repaired* to
  *Done*. Stage ids do not change, so existing requests keep their stages.
- **A priority pair already configured keeps its value**; only the missing pairs are filled.
- **Upgrading never overwrites tuned values**: the records belong to the site once installed.
- **English names only.** In another language, *Done* keeps core's translation of *Repaired*, and
  the new stages, rules and reasons show in English.
- **Meant to stay installed.** Uninstalling deletes the records it created that are not in use,
  keeps those that are, keeps the grid rows, and does not undo the stage changes.

## What it installs

| Sequence | Stage | Role |
|---|---|---|
| 1 | New Request | clocks running |
| 2 | In Progress | target of the Response rules |
| 3 | Waiting for Parts | pauses the Restore rules |
| 4 | Waiting for Production | pauses the Restore rules |
| 5 | Restored – to Confirm | target of the Restore rules |
| 6 | Done | confirmed by the requester |
| 7 | Scrap | cancels SLA |

| Priority | Response | Restore |
|---|---|---|
| High | 0:15 | 2:00 |
| Normal | 1:00 | 8:00 |
| Low | 4:00 | 24:00 |
| Very Low | 24:00 | 72:00 |
| none | 1:00 | 8:00 |

All corrective, at risk from 75 % of the target.

| Criticality | Safety risk | Line stopped | Producing defects | Degraded operation | No production impact |
|---|---|---|---|---|---|
| A — critical | High | High | High | Normal | Low |
| B — important | High | High | Normal | Normal | Low |
| C — minor | High | Normal | Normal | Low | Very Low |

Waive reasons: power or utility outage; production refused access to the machine; external
contractor or supplier delay; not a maintenance fault.

## Day to day

A technician leaves a machine in *Restored – to Confirm* once it runs again; that meets the
restore commitment. Moving it to *Done* is the requester's confirmation; sending it back to
*In Progress* opens a new restore cycle.
