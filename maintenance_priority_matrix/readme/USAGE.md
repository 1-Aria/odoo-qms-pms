## Configuring

1. Give each **equipment category** a criticality under *Maintenance → Configuration →
   Equipment Categories*. New machines in that category start from it; machines that already
   exist are not changed, so fill criticality in on them directly or by import.
2. Fill the grid under *Maintenance → Configuration → Priority Rules*: one row per criticality
   and urgency, saying what that combination is worth. The list is editable, so the whole grid
   goes in without opening a form.

A row with no company is the grid every company uses. A row naming a company overrides it for
that company only.

**Until the grid is filled, nothing is suggested and priority behaves exactly as it does in
core.** That is deliberate: which priority a combination deserves is a decision for the plant,
not a default worth guessing.

## Reporting a request

Set **Urgency** on the request; it is required for corrective work. The **Suggested Priority**
field shows what the rules make of it together with the machine's criticality — shown read-only
beside it, since criticality belongs to the machine — and **Priority** follows the suggestion.

You do not set priority yourself in the normal case: save the request and it arrives carrying
the suggestion. Preventive requests, which the maintenance plan generates without a reporter,
carry no urgency either.

Priority is yours to override: set it to anything, and give a reason — the form asks for one as
soon as your value differs from the suggestion, whether you change it while raising the request
or afterwards. Both the priority and the reason are recorded in
the chatter.

Change urgency on a request you have not overridden and the priority follows at once, in the
form — you do not have to save to see it.

An overridden priority stays put. Once you have moved it by hand, a later change of urgency
updates the suggestion and leaves your value alone, until someone sets it back to match the
suggestion. Clearing the priority counts as an override too, so it stays cleared.

## Two things the module does not do

- **The rule grid does not restate existing requests.** Editing a row changes what is suggested
  next; requests already raised keep the priority they carry, so history stays stable.
- **A request's criticality is a snapshot.** Re-rating a machine does not rewrite the requests
  already raised against it.
