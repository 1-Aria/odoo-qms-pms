## Configuring

1. Flag the stage that cancels a request, such as *Scrap*, with **Cancels SLA** in the stage list
   (*Maintenance → Configuration → Maintenance Stages*, in debug mode).
2. Define the commitments under *Maintenance → Configuration → SLA Rules*. A rule says which
   requests it applies to — by type, priority, team, equipment category, company, or an extra
   filter — which stage meets it, which stages pause it, how many hours are allowed, and from what
   share of that time it counts as at risk. When several rules match a request on the same target
   stage, the one with the lowest sequence applies.
3. Add the reasons a commitment may be waived under *Maintenance → Configuration → Waive
   Reasons*. Until at least one exists, nothing can be waived.

With no rules configured, no commitments are created and requests behave as they do without
this module.

## Day to day

Each request lists its commitments on its **SLA** page, and shows its state and next deadline
under *Priority*. The maintenance board is ordered by the next deadline, and each card shows a
badge: *On track*, *At risk*, *Overdue*, or *Paused* while the request waits in a pause stage.
The **SLA Overdue** and **SLA At Risk** filters list what needs attention.

*Reported At* defaults to the moment the request is raised. It can be corrected for a late entry
until a commitment of the request pauses, is met or is cancelled; the commitments move with it.

## What happens on its own

- A commitment is **met** when the request reaches its target stage or a later one: on time, or
  late, with the time it took.
- It **pauses** while the request sits in one of its pause stages; that time is recorded but not
  counted.
- It is **cancelled** with its request, by a cancelling stage or by the *Cancel* button.
  **Cancellation is final**: a cancelled request with commitments cannot be reopened; raise a new
  one.
- Sending a request **back** below a target it had reached opens a **new cycle** of that
  commitment, starting at the moment it was sent back. The first one keeps its result.
- A change of **priority, team, machine or type** applies the rules again: a commitment whose rule
  no longer applies is replaced by the one that now does, keeping the time already counted.

Every outcome is noted in the request's chatter.

## Waivers

An equipment manager can waive a finished commitment — one that was met — with a reason from the
list and an optional note, for instance when a breach was caused by something outside the team's
control. The commitment keeps its result but no longer counts in compliance. A waiver cannot be
undone.
