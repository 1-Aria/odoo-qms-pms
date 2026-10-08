**Nothing is sent until destinations are added.** In *Settings → Technical → Automation Rules*,
open each of this module's rules, then its *Send Zalo Message* action, and set its destinations —
a test chat on a test instance. The rules ship without any, since chat IDs belong to each site.

The rules and templates are a starting point, their text in Vietnamese: after install they belong
to the site, and an upgrade does not overwrite them. Stage and SLA rule names print as stored —
translate or rename them in Odoo to have them in Vietnamese too.

| Notification | When |
|---|---|
| New maintenance request | a corrective request is created |
| Maintenance request paused | a corrective request reaches *Waiting for Parts* or *Waiting for Production* |
| Maintenance request restored | a corrective request reaches *Restored – to Confirm* |
| Technician assigned | *Responsible* is set on a corrective request, also when reassigned |
| SLA at risk, SLA breached | about a minute after an SLA record turns at risk or overdue, while it runs |
| New inspection | an inspection is created — one message each, as their triggers create them |
| Inspection not passed | an inspection awaits approval, and again when it is failed |

**Technician assigned** also fires for a new request created with *Responsible* already set. Core
fills a new request's *Responsible* from the equipment's *Technician*, or its category's
*Responsible*: leave those empty if assignment should be a manager's explicit step.

**SLA alerts** are time-based rules: installing sets the cron *Automation Rules: check and
execute* to run every minute. Its first run after install — which can come up to four hours later —
notifies, once, every running SLA record already at risk or overdue.
