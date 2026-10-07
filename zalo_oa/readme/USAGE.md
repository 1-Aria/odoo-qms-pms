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
