## Configuring

1. Define the statuses under *Maintenance → Configuration → Equipment Statuses*.
2. In the stage list (*Maintenance → Configuration → Maintenance Stages*, in debug mode), set
   **Equipment Status** on the stages that should change a machine's status.

- **Map *Down* at the stage where work starts, not where requests arrive.** A reported request
  does not mean the machine is down: it may be degraded, or not affecting production at all.
- **Two restore options.** Map *Operational* at *Restored – to Confirm* when the technician's word
  counts, or at *Done* when the requester's confirmation does.
- **Scrap retires the machine** once *Scrap* is mapped to a retired status. A request raised by
  mistake is cancelled with the **Cancel** button, never scrapped.

## What happens

- Only **corrective** requests move a machine's status.
- Only a **real stage change** does, or creating a request directly in a mapped stage. Saving a
  request without moving it never touches the machine, so a status set by hand stands until the
  next mapped move.
- With two open requests on one machine, **the last mapped move wins**; correct it by hand if
  needed.
- A status limited to some equipment categories is **skipped** for machines outside them.
- The change is tracked on the machine under the user who moved the request, even one who may not
  edit equipment.
