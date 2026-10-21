# IE Design Note — Single-Scan Capture

**Version:** v0.1 · 2026-10-21
**Status:** Direction agreed in discussion between Peter and Claude on 2026-10-21. Peter is confident in it; final confirmation and folding into the technical design are for the next session.
**Relates to:**
- `IE_Technical_Design_v0.2.md` (chunks 1–2): §5 lists every section this changes;
- `IE_Fit_Gap_v0.3.md` (the prototype findings it relies on);
- `IE_Business_Logic_Spec_v0.6.md` and `IE_Acceptance_Test_Cases_v0.3.md`: §6 lists the proposals for them.

**Purpose:** Record the single-scan capture direction in full, so the next session can review it and fold it into technical design v0.3 without relying on the conversation.

---

## 1. The direction
Shop-floor scanning must be as simple as possible:
- **A worker scans each bundle once.** That scan says "I am now on this bundle". It also ends their previous bundle.
- **Nothing to do at breaks, at shift end or the next morning.** No pause, no finish, no rescan.
- **A worker who scans a bundle and never scans another still earns it.** Their name and scan time are on the work order.
- **No clock runs in Odoo.** Only the scan times are captured, and durations are derived from them.

---

## 2. Rules

| # | Rule |
|---|------|
| R-1 | **One scan type.** A scan of bundle × operation by worker W makes W the credited operator of that work order. It also ends W's previous interval at the scan time. |
| R-2 | **Credit at the scan.** The bundle quantity × the SAM version in force on the scan's local date is credited to W, **dated by the scan's local date**. MO close is **not** a condition for the incentive: planners close MOs for stock, costing and scheduling, not for pay. Nothing is ever "in progress" for IE, so nothing needs checking at month close, and no credit can be lost when a period locks. |
| R-3 | **Duration.** W's interval on a bundle runs from that scan to **whichever comes first: W's next accepted scan, or the bundle's MO being marked done**. Its **counted time** is the interval ∩ W's attendance intervals (option B, TD-21), minus W's approved off-standard time. The interval may span any number of days and attendance sessions; only the attended parts count, each day's attendance net of lunch. So days off and leave add nothing. |
| R-4 | **Abnormal durations are accepted.** If W attends for long stretches without scanning, and the bundle's MO stays open, the interval keeps counting. That affects only the family time split (spec §10.2), never pay quantities. No job, check or exception is added for it. |
| R-5 | **Refused scans.** A scan is refused, with the reason shown at the station, when its MO is **done** ("this bundle's MO is already completed") or cancelled, or when the work order is credited to another worker (supervisor reassignment is the only way to change that). A refused scan changes nothing. Scanning your own current bundle again changes nothing either. |
| R-6 | **Combined stations** are scanned one operation after another. Each operation is its own work order, so scanning the second ends the first's interval. |
| R-7 | **Reassignment and clearing** are supervisor actions in the journal. Reassignment moves the credit and the interval to the new worker (spec §8 rule 3, unchanged). A clear removes a wrong scan, its credit and its interval. |
| R-8 | **Off-standard time** comes from leader entry (channel 2) and repairs (channel 3). It is **subtracted** from bundle time rather than requiring a pause. There is no pause channel. |
| R-10 | **Optional "done" scan.** A worker who has finished a bundle and will not scan another for a while (end of their work, moved to unscanned tasks) can end their interval. Workers are instructed in it, and line leaders remind them. It is never required. The proposed form is that **scanning your current bundle's ticket again means "done"**: it ends the interval and, if §3's option is kept, marks the work order done in Odoo. Repeats within a short debounce `[P 30 s]` are ignored as accidental double scans. This replaces R-5's "scanning your own current bundle again changes nothing". Credit is unchanged, because it was given at the first scan. |
| R-11 | **Running-long list (real-time).** The journal knows each worker's current bundle and when they scanned it, so "time on the current bundle" is computed live: now − scan time, minus the calendar's breaks, since attendance is not available live. A worker whose current bundle has run past `[P 3]` × qty × SAM appears on the leader's list and raises RT-2's "bundle open too long" alert. This is the prompt for the leader's reminder to scan "done" (R-10). It is detected directly, not inferred. |
| R-9 | **Optional breakdown button.** A station button "breakdown" starts a pending OS-01 off-standard record and, through the maintenance bridge, the breakdown call (RT-3). It does not touch any bundle. The record ends at W's next scan or when the leader sets its end. |

---

## 3. Implementation on Odoo

| Element | How |
|---------|-----|
| Scan | Capture writes a journal event (`mes.scan.event`, type `scan`) and sets the work order's credited operator. It does **not** call `button_start`, so Odoo starts no timer. |
| Previous bundle in Odoo (optional) | At W's next scan, capture marks W's previous work order done with `button_finish`. That method works on a work order that was never started (`odoo/addons/mrp/models/mrp_workorder.py:664-695`). It keeps Odoo's view of finished operations roughly current. Without it, the MO's close finishes every work order (`odoo/addons/mrp/models/mrp_production.py:2129`). **Recommended:** keep it. |
| Production record | `ie.production.record` is created **at the scan** from the journal and the work order, not when the work order is done. Its interval minutes come from the journal, not from Odoo time rows. |
| Odoo's time rows | Unused by IE. At MO close Odoo fills every work order that has zero duration with its expected duration (`mrp_production.py:1836-1842`). Those rows are ignored. |
| MO close | Unchanged for Odoo: it finishes the remaining work orders and posts stock and valuation. A work order nobody scanned still produces the `unscanned_workorder` exception, because someone did that work without being credited. |

---

## 4. What it removes and what it costs

**It removes** three prototype findings (fit-gap v0.3 §13.2), all of which came from Odoo's running timer:
- the collision on the line's `working_state` record when a line flips between idle and busy, which was the only concurrency issue the burst test found;
- the 20 calendar leaves per bundle, since leaves are created only by `button_start` (`mrp_workorder.py:644-655`);
- the "Reduced Speed" time rows.

**It also removes from the design:**
- system pauses;
- the pause channel and its approval;
- the rule that rejects off-standard time overlapping bundle time, and the automatic pause when off-standard time starts;
- the "unapproved pause" exception.

**It costs:**
- **Odoo's work-order durations are no longer real.** They become the expected-duration fill-ins, and the journal is IE's only record of time. Nothing else uses them: costing goes through the Extra Unit Cost (FG-06), and work centres carry no hourly cost.
- **Pace (M6) and coverage (M7) are rougher.** The time between finishing a bundle and scanning the next counts as the previous bundle's time, so coverage sits near 100% by construction. Waiting for work stays separate, because the leader enters it as off-standard time. Pay is unaffected, and the family split barely moves.
- **A switch counts as finished.** If a worker leaves a bundle half-done, scans another, and comes back, the return is "scanning your own bundle", which is allowed. But their interval on the other bundle has already ended. Only interval attribution changes; credit is unaffected. This is rare in a one-operator-per-bundle flow.

---

## 5. Changes to technical design v0.2

| TD v0.2 | Change |
|---------|--------|
| TD-05, §5 production records | Created at the scan, from the journal and the work order. `date` is the scan's local date. `sam` is the version in force on that date. `qty` is the work order's quantity. `active_minutes` is the journal interval (R-3). The builder's triggers become journal events and reassignments or clears, not finished work orders. |
| TD-06, §4.3 journal | Event types become `scan`, `reassign` and `clear`, plus `breakdown` if R-9 is kept. `pause`, `resume`, `start` and `finish` go. |
| TD-08 event time | Unchanged: prompt events take server time, queued ones the corrected device time. |
| TD-09, §4.4 checks | Reduced to R-5. The off-standard hook is no longer needed. |
| TD-11, §4.1 local date | `mes_date_local` (from `date_finished`) is replaced by the scan's local date on the journal and the production record. |
| §4.4 apply, §4.5 reassignment, system pauses | Rewritten for R-1 and R-7. System pauses are removed. |
| FG-29 (IE reads only scan rows) | Obsolete: IE never reads time rows. |
| TD-15–TD-18, §6 off-standard | The pause channel is removed (R-8), and channel 1 becomes the optional breakdown record (R-9). The overlap rule with bundle time and TD-17 are removed. Off-standard records still must not overlap each other. |
| §7.3 counted minutes | `counted_minutes` = journal interval ∩ attendance − approved off-standard time (R-3). |
| §8.2 exceptions | `unapproved_pause` is dropped. The rest stay: `open_offstandard`, `unscanned_workorder`, `late_event`, `rejected_queued_event`, `scan_outside_attendance`. |
| §9.1 defects | Unchanged: DD uses the production record's SAM. |

---

## 6. Proposals for the business documents (not applied)
- **Spec §8 rules 4–5.** Replace start and finish scans with one scan per bundle. The credit date becomes the scan's local date instead of the finish date. The time category, if ever needed, comes from the scan time.
- **Spec §3.3 and DEC-17.** Channel 1 changes from a work-order pause with a reason to the optional breakdown button (R-9). Off-standard time is subtracted from bundle time.
- **Spec §3.4 items 3–5.** No pausing at breaks or shift end, no nightly job; the remaining exception list.
- **Spec §4 (M6, M7) and §13.1.** Note that pace and coverage include handling time between scans.
- **Test cases:**
  - TC-TA-01: channel 1 by breakdown button;
  - TC-TA-03: obsolete;
  - TC-TA-04: off-standard time subtracted instead of pausing (the expected numbers are the same: bundle 40, off-standard 20);
  - TC-TA-07: obsolete;
  - TC-EM-08: scan date;
  - TC-RT-03: "bundle open > 72 min" becomes "current bundle running > 72 min since its scan", from the journal (R-11);
  - TC-RT-04: breakdown button.

---

## 7. For the next session to settle
1. Confirm the direction (R-1 to R-8, R-10, R-11), and whether the breakdown button (R-9) is wanted. Confirm the form of the "done" scan: re-scanning your current ticket (proposed), or a separate station button.
2. Confirm marking the previous work order done at the next scan (§3, recommended).
3. Fold this into technical design v0.3, then continue with chunk 3.
