Sends Zalo Official Account messages from Odoo, through the instance's own Zalo app. Odoo holds the
app's tokens and refreshes them, queues every message and sends it within seconds, and renders
templates from automation rules, so any model can notify a Zalo group chat or user. A route lets an
external system — the Apps Script that receives the OA's chat events — send its replies through Odoo
as well.

This version only sends: it does not receive Zalo's webhook events.
