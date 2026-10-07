Under *Settings → Technical → Zalo → Tokens* (developer mode), create the row for the configured
app and paste its refresh token — or, from a later step, authorize the app.

**Do not put a refresh token in Odoo while the Apps Script still refreshes it:** Odoo's cron will
rotate it, and the Apps Script's replies stop.

The refresh cron runs hourly and refreshes when fewer than six hours remain. *Refresh now* asks it
to refresh at its next run, within seconds. Set an alert user — a system administrator — to be told
when the token has not been refreshed for two days.
