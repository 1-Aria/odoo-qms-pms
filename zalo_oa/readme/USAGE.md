Under *Settings → Technical → Zalo → Tokens* (developer mode), create the row for the configured
app and paste its refresh token — or, from a later step, authorize the app.

**Do not put a refresh token in Odoo while the Apps Script still refreshes it:** Odoo's cron will
rotate it, and the Apps Script's replies stop.

The refresh cron runs hourly and refreshes when fewer than six hours remain. *Refresh now* asks it
to refresh at its next run, within seconds. Set an alert user — a system administrator — to be told
when the token has not been refreshed for two days.

**Destinations** name the group chats and users messages go to. **Messages** is the queue and log:
every message is queued first and sent within seconds by the send cron, which also retries what
failed for a passing reason — a network error, an expired token — with a growing wait, up to five
attempts. Zalo's own refusals fail at once. A message can be queued by hand on the form, and a
failed one sent again with *Retry*. Sent and failed messages are removed after 30 days.

On a test instance, `zalo_redirect_recipient` in `odoo.conf` (`group:<id>` or `user:<id>`) sends every
message to that one chat instead, its text naming the intended recipient.

**Templates** hold the message text for one model, with placeholders such as
`{{ object.name }}` for the record's fields. To send from an automation rule, give it the action
*Send Zalo Message* with a template for the rule's model and one or more destinations. A template
that fails to render — a mistyped placeholder, a removed field — becomes a failed message in
*Messages*; the record that triggered the rule still saves.

**An *On save* rule needs *When updating* fields.** With none it sends on every save and every
recompute, duplicates within one save included. To send when a record is created, watch
**Created on**; to send on a stage change, watch **Stage**.
