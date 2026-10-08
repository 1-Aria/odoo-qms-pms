# zalo_oa

Zalo Official Account integration: the instance's Zalo app and its tokens, a send queue, templates
and a "Send Zalo message" server action, the routes for authorization and the interim Apps Script,
and later the webhook.
Design: `docs/Zalo ↔ Odoo Integration Design Note.md`; the Zalo API: `docs/Zalo OA Integration
Reference.md`. Plan: §8.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The instance's app from `odoo.conf`; `zalo.token` per app; the token half of the Zalo client; the refresh under the row lock with its commit; the refresh cron and the health alert; the token list and form | done | 2026-10-07, two runs. First: 8 of 22 passed; the 14 token tests errored after each test, on a class-level `patch.dict` that `TransactionCase`'s attribute check cannot read (`odoo/odoo/tests/common.py:1117-1122`), now started per test in `setUp`. Second: `-u`, `exit=0`, 22 tests, 0 failures. The instance's app configured through a YAML block in `compose.yml.template` — a `\n` in `.env` stayed literal. UI checked: the configured app's row recognised, *Refresh now* waking the cron and `last_error` reporting the missing refresh token, the alert user offered among administrators only, another app's row muted without the button; no live refresh, the Apps Script still holding app A |
| 2 | The send queue: `zalo.destination`, `zalo.message`, the send half of the client with refresh-on-expiry — its refresh under step 1's savepoint, a serialization failure leaving the message queued — the send cron committing per message, the redirect, `_queue()` | done | 2026-10-07, two runs. First: 47 of 48 passed; `test_queue_flushes_the_callers_writes_first` patched `flush_all` outside `assertRaises`, whose own flushing savepoint (`odoo/odoo/tests/common.py:489`) met it first — now patched inside. Second: `-u`, `exit=0`, 48 tests, 0 failures. UI checked with a borrowed access token and no refresh token (design, phase 1): a message to a test group delivered and shown *Sent* with Zalo's response; one to a bogus ID failed with Zalo's error and re-queued by *Retry* |
| 3 | `zalo.template` and the "Send Zalo message" server action, with the isolation rule for queueing; the message's source template | done | 2026-10-07, two runs. First: the template tests failed after the first one created an automation rule, its patches on the model class surviving the rollback — now unregistered in `tearDown`, as core's tests do; and a test built on a mistaken review, that a savepoint's rollback discards the caller's tracking, was dropped with the plain savepoint it motivated — `cr.flush()` runs the precommit hooks first. Second: `-u`, `exit=0`, 56 tests, 0 failures. UI checked with a borrowed access token: a template on maintenance requests, an automation rule sending it, a new request delivered with its fields filled in, a mistyped placeholder failing as a message while the request saved. The rule first sent twice per save — an *On save* rule with no watched fields fires on every write and recompute in the save; fixed by configuration, watching *Created on*, no code changed |
| 4 | Routes: `/zalo/authorize`, `/zalo/callback`, `/zalo/send` with the *Zalo sender* group; the pending authorization on `zalo.token` | done | 2026-10-08, two runs. First: `-u` committed the step, but the post-install run aborted before any of its tests — the route tests were an `HttpCase`, before which Odoo pregenerates every asset bundle (`odoo/odoo/service/server.py:1437-1440`), and this image strips core's test assets (`images/odoo/Dockerfile:49`); only the 27 at-install tests ran, and passed. `/zalo/send`'s body moved into `zalo.message._queue_from_request`, tested as the technical user in a `TransactionCase`; its read-back as superuser had been found while writing the route — the technical user cannot read the log. Second: `-u`, `exit=0`, 73 tests, 0 failures. UI checked: *Authorize* redirecting to Zalo's permission page with the instance's callback URL, not approved — app A stays with the Apps Script until phase 2; `/zalo/callback` with an unknown state answering the plain-text refusal; the technical user created with its persistent key; `curl` to `/zalo/send` — no key 401, an administrator's key 403, a body that is not JSON 400, a valid one 200 and the message delivered to the group; a read of `res.partner` over XML-RPC with the technical user's key refused. The approval and the first pair wait for phase 2 |
| 5 | Receiving: `zalo.event`, `/zalo/webhook`, event processing | planned | target state |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | *Rules* 1: "the refresh cron and the send fallback both call the same `_refresh()`"; Phase 2 step 3: "trigger one refresh from Odoo" | the token form's *Refresh now* sets `refresh_requested` and wakes the refresh cron; it does not refresh in the request | *Rules* 2: Zalo is called from crons only. A refresh committed inside a user request would break that rule for the one place an administrator touches it |
| 2 | §"Models" lists the pending authorization's state and verifier on `zalo.token` | added in step 4, with the routes that use them | Nothing reads them before |
| 3 | §"Models" gives `zalo.message` a source template | added in step 3, with `zalo.template` | The model does not exist before |
| 7 | §"Server action type": a template field and destination fields, as SMS has; SMS translates its template body | the template's body is **not** translated (`translate=False`); its name is | A translated body is stored per language and rendered in the language of whoever runs the action — the automation's superuser. Edited in a Vietnamese session, the Vietnamese text changes while the English one, the one actually rendered, stays old, and the notification silently keeps the previous wording. The recipients are chats, with no language to render for. The name stays translatable, as every name field in this project does |
| 4 | §"Models" does not record where a redirected message went | `sent_to` on the message: the recipient Zalo was actually given, set on every sent message | The design keeps the intended recipient in the log; with a redirect, the log should also say where the message really went |
| 6 | *Sending path*: "network errors and failed refreshes are retried a few times by the cron" | each retry waits `attempts × RETRY_DELAY` (5 minutes), through `next_attempt_at`; only due messages are sent | Odoo's cron runner calls a job again, up to ten times in one run, while it reports work done and work remaining (`odoo/odoo/addons/base/models/ir_cron.py:419-454`). A retried message is still queued, so without a wait one run would spend all five attempts in seconds during a Zalo outage, failing every message before Zalo came back. Found reading the runner while writing the code |
| 5 | The design does not say what a malformed `zalo_redirect_recipient` does | the message fails, naming the setting; it is never sent to its intended recipient | The redirect exists to keep a test instance out of real chats. Falling back to the real recipient on a typo would defeat it |

## Decisions

| # | Decision |
|---|---|
| D1 | **The client is a plain Python module, `tools/zalo_client.py`,** with no ORM: endpoints, error codes, and functions taking the app's ID and secret and returning a result dictionary. The models persist and lock; the client only speaks HTTP. It is the port of `zalo_client.js` the design names, the token half in this step |
| D2 | **The configuration is read on every use,** through `get_zalo_config()`, from `odoo.tools.config` — every key of `odoo.conf`'s `[options]` is kept (`odoo/tools/config.py:703-709`). Nothing is cached, so a restart with a new `.env` takes effect without a database change |
| D3 | **The row lock is `SELECT … FOR UPDATE` on the token row, inside a savepoint.** The instance runs two workers and two cron threads, so the refresh cron and, from step 2, the send cron's fallback can meet. Odoo's cursors run in REPEATABLE READ (`odoo/odoo/sql_db.py:303`): a transaction waiting on the lock for a row another one then updates and commits does not get the new row — PostgreSQL fails it with *could not serialize access due to concurrent update* (`psycopg2.errors.SerializationFailure`). The lock, re-read, Zalo call and write therefore run inside `self.env.cr.savepoint()`, and that failure is caught outside it and read as *refreshed by another worker*: the waiter never calls Zalo, and the next transaction sees the new pair |
| D4 | **"Already refreshed" is decided by the access token, not the expiry.** `_refresh(stale_access_token)` refreshes only if the stored access token, re-read under the lock, is still the stale one. Inside one transaction a concurrent refresh surfaces as D3's serialization failure; the value check catches a refresh committed before the transaction began, after the caller read its stale token — the send fallback (step 2), which refreshes a token Zalo has just rejected whatever its expiry |
| D5 | **The commit after saving the pair is governed by `_zalo_auto_commit()`:** true unless the current thread is testing — core's mail queue's rule (`mail/models/mail_mail.py:263`). In a test the save stays in the test transaction; outside one it is committed before anything else can roll it back. The commit comes **after** the savepoint block closes, never inside it: committing within an open savepoint breaks its release |
| D6 | **The refresh cron never raises** (design §"Isolation from Odoo", rule 2), so Odoo never counts a failure towards deactivating it (`odoo/odoo/addons/base/models/ir_cron.py:24-25`, `457-494`). Its database work runs inside savepoints — `_refresh()`'s own, and one around the health check; not one around `_refresh()`, which commits, and a commit inside an open savepoint breaks its release (D5) — so a database error leaves the transaction usable: any other error is logged and written to `last_error` after the rollback. A serialization failure is not written — the row changed under the transaction, and the same write would fail the same way; the cron returns and the next run sees the new pair |
| D7 | **The health alert is an activity on the token row,** of type `mail.mail_activity_data_warning`, for `alert_user_id`, scheduled when the last successful refresh is older than two days and no such activity is open — so it is raised once, not every hour. The row inherits `mail.thread` and `mail.activity.mixin` for it; no token field is tracked |
| D8 | **Tokens are editable on the form, masked.** Phase 2 copies the Apps Script's refresh token into the row, and phase 1 tests sends with a borrowed access token, so both fields are typed by hand — by system administrators only (D9) — with `widget="password"` |
| D10 | **Every queued message wakes the send cron** (step 2): `zalo.message.create()` calls `_trigger()` on it for queued records, so a message created by `_queue()`, by a server action (step 3), by a route (step 4) or by hand on the form goes out within seconds by the same path |
| D11 | **`_queue()` never raises** (design §"Isolation from Odoo", rule 1). It creates inside a savepoint; on any error the savepoint is rolled back, the error logged, and a *failed* message written with what is known; if even that fails, it logs and returns an empty recordset. A missing recipient or text is not an exception but a failed message. For it to hold, `recipient_id`, `recipient_type` and `text` are not `required` on the model — a failed message records whatever it had. It creates as superuser, so a caller needs no access to the log. **It flushes first, outside the guard** (`self.env.flush_all()` before the `try`): `cr.savepoint()` flushes the caller's pending writes when it is created (`odoo/odoo/sql_db.py:123-126`), so a savepoint opened inside the `try` would catch a failure in the *caller's* own writes, in a transaction already aborted — the failed message could not be written either, and the caller would later see *current transaction is aborted* instead of their own error. Flushed first, the caller's error surfaces as it would without `_queue()`, and only the module's own work is guarded. Step 3's server action follows the same rule; the cron's savepoints are unaffected. |
| D12 | **The send cron never raises and commits per message** (design rules 2 and *Sending path*). Each message's result is written in its own savepoint and, outside tests, committed before the next (D5's flag) — core's mail and SMS queues do the same (`sms/models/sms_sms.py:147-149`) — so a crash mid-batch cannot resend a message Zalo accepted. An unexpected error on one message is logged and counted as a failed attempt on it; the cron goes on. The refresh-on-expiry runs **outside** any savepoint, since `_refresh()` commits (D5) |
| D13 | **Results fall into four kinds** (reference, *Error reference*): *sent* — HTTP 200 and `error` 0; *expired* — HTTP 401 or `error` −216, refreshed once and retried once; *retryable* — a network error, a body that is not JSON, an HTTP status of 500 or more, a failed refresh, or still *expired* after the refresh: the attempt is counted and the message stays queued until `MAX_ATTEMPTS` (5), then fails; *permanent* — any other Zalo error, such as −224: failed at once, Zalo's body kept |
| D14 | **The redirect is read from `odoo.conf` at send time** (design §"Models"): `zalo_redirect_recipient` as `group:<id>` or `user:<id>`. Set, every message goes there, its text prefixed `[→ <intended recipient>] `, where the intended recipient is the destination's name or `<type>:<id>`; the message keeps its intended recipient, and `sent_to` records the real one. Malformed, the message fails (divergence 5) |
| D15 | **Batches through Odoo 18's cron progress:** the send cron takes `BATCH_SIZE` (50) queued messages, oldest first, and reports `_notify_progress(done=…, remaining=…)` (`odoo/odoo/addons/base/models/ir_cron.py:734`); the cron runner calls the job again while work remains, committing between calls |
| D18 | **The template is SMS's** (step 3): `zalo.template` inherits `mail.render.mixin` with `_unrestricted_rendering = True`, as `sms.template` does (`sms/models/sms_template.py:10-13`), so a template uses the full inline-template syntax and the mixin restricts creating or editing a dynamic one to `mail.group_mail_template_editor` (`mail/models/mail_render_mixin.py:95-110`). It renders with `_render_field("body", res_ids)` (`:707`), one call for all the action's records |
| D19 | **Queueing from a template never raises, and flushes first** (design §"Isolation from Odoo", rule 1; D11): `zalo.message._queue_from_template()` flushes the caller's writes, then renders inside a savepoint. The caller's tracking is safe: `cr.flush()` runs the precommit hooks (`odoo/odoo/sql_db.py:156-167`) and a savepoint flushes before it opens, so the rollback of a failed render clears only hooks added inside it (a plain savepoint was specced for this on a review that missed the flush; the first run showed the hooks already run). The template is read and rendered **as superuser**, so an administrator's template renders the same whether an automation runs the action, through `sudo()` (`base_automation/models/base_automation.py:737`), or a user runs it from a record's *Action* menu. A rendering error — a typo in a placeholder, a field that no longer exists — becomes a *failed* message per record and destination, carrying the error and the source record; the save that triggered the rule goes through. An automation rule re-raises its actions' errors (`base_automation/models/base_automation.py:737-742`), and SMS's action has no such guard (`sms/models/ir_actions_server.py:72-89`) |
| D20 | **The action skips recomputes**, as SMS does: `_is_recompute()` (`mail/models/ir_actions_server.py:201`) is true when an on-update rule fires only because a computed field was recomputed, and the action then queues nothing |
| D21 | **The template's model must be the action's,** a constraint as SMS's `_check_sms_template_model` (`sms/models/ir_actions_server.py:62-66`): rendering a template against records of another model can only fail. The view filters the template by the action's model as well |
| D22 | **Authorization is two model methods behind thin routes** (step 4): `zalo.token._authorize_start(redirect_uri)` and `_authorize_finish(state, code)`. The routes only read the request and answer; the logic is tested without HTTP |
| D23 | **PKCE as the reference has it** (reference, *Initial authorization*): a `code_verifier` of 64 random URL-safe characters (`secrets.token_urlsafe(48)`), `code_challenge` = base64url of its SHA-256 without padding, a `state` of `secrets.token_urlsafe(32)`. Both are kept on the configured app's token row with the time; the row is created when missing. A pending authorization expires after **10 minutes**, and `state` is compared with `hmac.compare_digest` on the UTF-8 bytes: given two `str`, it raises `TypeError` when either holds a non-ASCII character, and the callback is public |
| D24 | **The callback URL is the instance's own:** `<web.base.url>/zalo/callback`, through `get_base_url()`, the URL registered in the Zalo console (design §"Routes"). `/zalo/authorize` passes it, and the code exchange is made on the same configured app |
| D25 | **The code exchange is the one Zalo call in a request** (design *Rules* 2): `/zalo/callback` is answered by Zalo's redirect of an administrator's browser, so it cannot wait for a cron. It writes the first pair on the row; the request's own commit saves it. A failure is shown on the page and written to `last_error`. **The row is locked before Zalo is called** (`_lock_row()`): a request runs inside Odoo's retry on serialization failures (`odoo/odoo/http.py:2167`, `odoo/odoo/service/model.py:141-198`), so a conflict found only when the pair is flushed would run the route again and reuse a code Zalo has already redeemed, losing the pair it issued. The lock meets any conflict first, before the call, and holds off any other writer until the commit — the reference exchanges under its refresh lock too (`docs/zalo_client.js:191`). The refresh cron does write the row meanwhile: a row created by `_authorize_start` has no `expires_at`, so the cron tries to refresh it and writes `last_error`. **A matching `state` is cleared whatever follows,** so it is used once; a state that does not match leaves the pending authorization alone, since the callback is public and anyone could otherwise cancel an administrator's authorization in progress |
| D26 | **`/zalo/send` is one model method behind a thin route** (step 4): `zalo.message._queue_from_request(payload)` returns the HTTP status and the JSON answer, so it is tested without HTTP — an `HttpCase` cannot run on this image (*Tests*). It answers 403 when the calling user lacks *Zalo sender*; 400 for a payload that is not a JSON object, a `recipient_type` other than `user` or `group`, or a `recipient` or `text` that is not a non-empty string — the caller gets its mistake, not a failed message; otherwise it calls `_queue()`, which creates as superuser (D11), and answers 200 with `ok` = whether the message is queued, since `_queue()` falls back to a failed message rather than raise. The message is **read back as superuser**: the technical user cannot read the log, and reading its state as that user raises `AccessError`. Bearer authentication is Odoo's (`odoo/odoo/addons/base/models/ir_http.py:204-243`): a missing or invalid key answers 401 before the route runs |
| D27 | **The *Zalo sender* group grants nothing else** (design §"Routes"): no access row names it. It is checked by the route alone; the message is created as superuser. **It is held by a technical user with no other group** — no user type, no password — whose one API key is persistent and created once by an administrator, through sudo, as that user; an administrator revokes it. So the key reads and writes nothing in Odoo, over RPC either: this instance has no read access row without a group. The alternatives fail: bearer authentication takes only a global key (`odoo/odoo/addons/base/models/ir_http.py:228-229`), which also authenticates RPC (`odoo/odoo/addons/base/models/res_users.py:2306-2320`), so an internal user's key reads what any employee reads; and a key created by a user who is not an administrator expires within the longest `api_key_duration` of its groups, 90 days for *Internal User* and 1 day without one (`res_users.py:2422-2432`, `base/security/base_groups.xml:27`), after which the autovacuum deletes it (`res_users.py:2462-2470`) and the Apps Script stops replying with nothing in Odoo saying why. Sudo lifts the limit (`res_users.py:2426-2427`). The user form requires a user type (`res_users.py:2119-2122`), so the user is not edited there |
| D17 | **A retry waits** (divergence 6): `next_attempt_at` = now + `attempts × RETRY_DELAY` — 5, 10, 15, 20 minutes — and the send cron and its `remaining` count read only messages that are due (`next_attempt_at` empty or past). An outage of about 50 minutes costs no message; a sent, failed or retried-by-hand message clears it |
| D16 | **Old messages are removed by `@api.autovacuum`** (design §"Scheduled actions and cleanup"): sent and failed messages older than `RETENTION_DAYS` (30). Queued ones are never removed |
| D9 | **Access is system administrators only:** `base.group_system` holds the model's only access row, and the token fields also carry `groups="base.group_system"` (design §"Models"). The menu is under *Settings → Technical* (`base.menu_custom`) |

## Folder structure

```
zalo_oa/
├── __init__.py, __manifest__.py
├── tools/
│   ├── __init__.py
│   └── zalo_client.py
├── models/
│   ├── __init__.py
│   ├── zalo_token.py
│   ├── zalo_destination.py                             # 2
│   ├── zalo_message.py                                 # 2
│   ├── zalo_template.py                                # 3
│   └── ir_actions_server.py                            # 3
├── controllers/
│   ├── __init__.py                                     # 4
│   └── main.py                                         # 4
├── data/ir_cron.xml
├── security/ir.model.access.csv, zalo_security.xml     # 1, 4
├── views/zalo_token_views.xml, zalo_destination_views.xml, zalo_message_views.xml   # 1, 2, 2
│         zalo_template_views.xml, ir_actions_server_views.xml                         # 3, 3
├── tests/__init__.py, test_zalo_client.py, test_zalo_token.py, test_zalo_message.py  # 1, 1, 2
│         test_zalo_template.py                                                        # 3
│         test_zalo_authorize.py, test_zalo_send.py                                    # 4, 4
└── readme/ DESCRIPTION.md, USAGE.md, CONFIGURE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Zalo Official Account` |
| `summary` | `Send Zalo Official Account messages from Odoo: tokens, a send queue, templates and automation` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Productivity` |
| `depends` | `mail`, `base_automation` — the second for step 3's server action, declared now so the dependency never changes under an installed module |
| `data` | `security/zalo_security.xml` (step 4, first), `security/ir.model.access.csv`, `data/ir_cron.xml`, `views/zalo_token_views.xml`, `views/zalo_destination_views.xml` (step 2), `views/zalo_message_views.xml` (step 2), `views/zalo_template_views.xml` (step 3), `views/ir_actions_server_views.xml` (step 3) |
| `installable` | `True` |

`requests` is in Odoo's own requirements; no external dependency is declared.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import tools`, `from . import models`, `from . import controllers` (step 4) |
| `controllers/__init__.py` | `from . import main` (step 4) |
| `tools/__init__.py` | `from . import zalo_client` |
| `models/__init__.py` | `from . import zalo_token`, `from . import zalo_destination`, `from . import zalo_message` (step 2), `from . import zalo_template`, `from . import ir_actions_server` (step 3) |
| `tests/__init__.py` | `from . import test_zalo_client`, `from . import test_zalo_token`, `from . import test_zalo_message` (step 2), `from . import test_zalo_template` (step 3), `from . import test_zalo_authorize`, `from . import test_zalo_send` (step 4) |

## Configuration — `get_zalo_config()` in `tools/zalo_client.py`

Returns a dictionary read from `odoo.tools.config` on every call (D2):

| Key | `odoo.conf` key |
|---|---|
| `app_id` | `zalo_app_id` |
| `app_secret` | `zalo_app_secret` |
| `oa_secret` | `zalo_oa_secret` (step 5) |
| `redirect` | `zalo_redirect_recipient` (step 2) |

Each value is stripped; a missing or empty key gives `False`. **No `app_id`, no Zalo** (design
§"Instances, apps and configuration").

## The client — `tools/zalo_client.py`

| Name | Content |
|---|---|
| `OA_TOKEN_URL` | `"https://oauth.zaloapp.com/v4/oa/access_token"` |
| `REFRESH_TOKEN_INVALID` | `-14020` |
| `DEFAULT_EXPIRES_IN` | `90000` — 25 hours, when a response has no `expires_in` (reference, *Caveats*) |
| `TIMEOUT` | `20` seconds |
| `request_tokens(app_id, app_secret, fields)` | `requests.post(OA_TOKEN_URL, data=dict(fields, app_id=app_id), headers={"secret_key": app_secret}, timeout=TIMEOUT)` — form-encoded by `data`. Returns `{"ok": True, "access_token", "refresh_token", "expires_in"}` when the status is 200 and the body has both tokens and no `error`; otherwise `{"ok": False, "error": <text>}` |
| `refresh_tokens(app_id, app_secret, refresh_token)` | `request_tokens(…, {"refresh_token": refresh_token, "grant_type": "refresh_token"})` |
| `OA_PERMISSION_URL` | step 4; `"https://oauth.zaloapp.com/v4/oa/permission"` |
| `exchange_code(app_id, app_secret, code, code_verifier)` | step 4; `request_tokens(…, {"code": code, "grant_type": "authorization_code", "code_verifier": code_verifier})` |
| `pkce_pair()` | step 4; `(code_verifier, code_challenge)` per D23 |
| `permission_url(app_id, redirect_uri, code_challenge, state)` | step 4; `OA_PERMISSION_URL` with those four as query parameters, URL-encoded |

**Failures it reports** (reference, *Refresh request*, *Error reference*): a network exception
(`requests.RequestException`) as `"network error: <exception class>"`; a body that is not JSON as
`"unexpected response (HTTP <status>)"`; a body with `error`, `error_name` or `error_description` as
`"Zalo error <error>: <error_name or error_description>"`, and for `-14020` the text `"refresh token
already used or expired; authorize the app again"`. **Never a token, a secret or the raw body** in the
returned text or a log line — the reference's logging rule.

`expires_in` is returned as an integer, `DEFAULT_EXPIRES_IN` when absent or unreadable.

**The send half** (step 2):

| Name | Content |
|---|---|
| `SEND_URLS` | `{"user": "https://openapi.zalo.me/v3.0/oa/message/cs", "group": "https://openapi.zalo.me/v3.0/oa/group/message"}` |
| `RECIPIENT_KEYS` | `{"user": "user_id", "group": "group_id"}` |
| `ACCESS_TOKEN_EXPIRED` | `-216` |
| `send_text(access_token, recipient_type, recipient_id, text)` | `requests.post(SEND_URLS[recipient_type], json={"recipient": {RECIPIENT_KEYS[recipient_type]: recipient_id}, "message": {"text": text}}, headers={"access_token": access_token}, timeout=TIMEOUT)`. Returns `{"status": <kind>, "error": <text or False>, "response": <body as JSON text, or False>}`, the kinds of D13: `"sent"`, `"expired"`, `"retry"`, `"failed"` |

The send response carries no token, so its body is returned for the log; the error text follows the
same rule as the token half — never the access token.

## Models

### `zalo.token` — `models/zalo_token.py`

`_name = "zalo.token"`, `_description = "Zalo App Token"`, `_inherit = ["mail.thread",
"mail.activity.mixin"]`, `_rec_name = "app_id"`.

| Field | Type | Attributes |
|---|---|---|
| `app_id` | Char | `string="App ID"`, `required=True`, `index=True` |
| `access_token` | Char | `groups="base.group_system"`, `copy=False` |
| `refresh_token` | Char | `groups="base.group_system"`, `copy=False` |
| `expires_at` | Datetime | `string="Access Token Expires"`, `copy=False` |
| `last_refresh_at` | Datetime | `string="Last Refresh"`, `readonly=True`, `copy=False` |
| `last_error` | Text | `readonly=True`, `copy=False` |
| `refresh_requested` | Boolean | `copy=False`, help: set by *Refresh now*; the next run of the refresh cron refreshes whatever the expiry |
| `alert_user_id` | Many2one → `res.users` | `string="Alert User"`, `domain` users in `base.group_system` (a lambda reading the group's id), help: a system administrator, told when the token has not been refreshed for two days — only they can open the token the alert points at (D9) |
| `is_configured_app` | Boolean | `compute="_compute_is_configured_app"`, not stored, `string="This Instance's App"` |
| `auth_state` | Char | step 4; `groups="base.group_system"`, `copy=False` (divergence 2) |
| `auth_code_verifier` | Char | step 4; `groups="base.group_system"`, `copy=False` |
| `auth_requested_at` | Datetime | step 4; `copy=False` |

| SQL constraint | Definition | Message |
|---|---|---|
| `app_id_unique` | `unique(app_id)` | `There is already a token for this Zalo app.` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_is_configured_app` | `@api.depends("app_id")` | `app_id` equals the configured `app_id` |
| `_get_current` | `@api.model` | the row whose `app_id` is the configured one, or an empty recordset — also when no app is configured. Never creates |
| `_zalo_auto_commit` | `@api.model` | `not getattr(threading.current_thread(), "testing", False)` (D5) |
| `_lock_row` | — | `SELECT id FROM zalo_token WHERE id = %s FOR UPDATE` — its own method, so a test can make it raise |
| `_refresh` | — | `ensure_one`; the refresh, below. Returns `True` when it saved a new pair or found one already saved, `False` otherwise |
| `action_refresh_now` | — | `ensure_one`; writes `refresh_requested=True` and calls `_trigger()` on the refresh cron (divergence 1) |
| `_cron_refresh` | `@api.model` | the cron's entry point, below; never raises (D6) |
| `_check_health` | — | `ensure_one`; the alert (D7), below |
| `_authorize_start` | `@api.model` | step 4; `_authorize_start(redirect_uri)`: with no configured app or app secret, `UserError`. Otherwise the configured app's row, created when missing; a new PKCE pair and `state` written on it with the time (D23); returns `permission_url(…)` |
| `_authorize_finish` | `@api.model` | step 4; `_authorize_finish(state, code)`, below. Returns `(ok, message)` |
| `action_authorize` | — | step 4; `ensure_one`; an `ir.actions.act_url` to `/zalo/authorize`, `target` `self` |

**`_refresh(stale_access_token)`** (D3, D4, D5):

Inside `with self.env.cr.savepoint():` —

1. `_lock_row()`; invalidate the row's cache and re-read it.
2. If its `access_token` differs from `stale_access_token`, another worker refreshed before this
   transaction began: clear `refresh_requested`, result `True`, no call to Zalo.
3. If the configured `app_secret` is missing or the row has no `refresh_token`, write `last_error`,
   result `False`.
4. `refresh_tokens(app_id, app_secret, refresh_token)`.
5. On success: write `access_token`, `refresh_token`, `expires_at` = now + `expires_in` seconds,
   `last_refresh_at` = now, `last_error` = `False`, `refresh_requested` = `False` — all in one
   `write()` — result `True`.
6. On failure: write `last_error` with the client's text; leave both tokens as they are. Result
   `False`.

— then, outside the block:

- `psycopg2.errors.SerializationFailure` raised by the block: another worker refreshed concurrently
  (D3). Invalidate the row's cache, log at INFO, return `True`, write nothing.
- Otherwise, when a new pair was saved and `_zalo_auto_commit()`, commit (D5); return the result.

Because it commits, `_refresh()` is never called inside an open savepoint of its caller's — the
cron's, or step 2's send fallback.

**`_cron_refresh()`** (D6): take `_get_current()`; if empty, return. Inside `try:` — when
`refresh_requested`, or `expires_at` is empty, or it falls within **6 hours** of now, call
`_refresh(stale_access_token=row.access_token)`; then `_check_health()` inside
`with self.env.cr.savepoint():`. `except SerializationFailure`: return, writing nothing. `except Exception`: log it
with `_logger.exception` and write `last_error` — never re-raise.

**The cron refreshes any refresh token it finds,** at once when `expires_at` is empty. A refresh token
put in the row while the Apps Script still refreshes the same app is therefore rotated within the
hour, and the Apps Script then fails with `-14020` (design, phase 1).

**`_check_health()`** (D7): when `alert_user_id` is set and `last_refresh_at` is empty or older than
**2 days**, and the row has no open activity of type `mail.mail_activity_data_warning` for that user,
`activity_schedule("mail.mail_activity_data_warning", user_id=alert_user_id, summary="Zalo token not
refreshed", note=…)` naming the last refresh and the last error.

**`_authorize_finish(state, code)`** (step 4; D23, D25) — each refusal returns `(False, <text saying
why>)` and calls nothing:

1. No configured app or app secret, or no row for it: refused.
2. `_lock_row()`; invalidate the row's cache and re-read it. A serialization failure here propagates,
   so the request is retried before Zalo is called (D25).
3. No pending authorization, or `state` empty or different (`hmac.compare_digest` on bytes): refused,
   **nothing written**.
4. The state matches: clear `auth_state`, `auth_code_verifier` and `auth_requested_at` — whatever
   follows.
5. Requested more than 10 minutes ago, or `code` empty — the administrator declined at Zalo: refused.
6. `exchange_code(app_id, app_secret, code, verifier)`. Success: write `access_token`,
   `refresh_token`, `expires_at` = now + `expires_in` seconds, `last_refresh_at` = now, `last_error` =
   `False` — `(True, …)`. Failure: write `last_error` with the client's text, the stored pair kept —
   `(False, <the client's text>)`.

**Only the configured app's row is ever refreshed.** A row of another app — copied by a restore —
is never read by `_get_current()`, so the cron leaves it alone (design §"A production database
restored onto test").

### `zalo.destination` — `models/zalo_destination.py` (step 2)

`_name = "zalo.destination"`, `_description = "Zalo Destination"`, `_order = "name"`.

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `recipient_type` | Selection | `[("group", "Group chat"), ("user", "User")]`, `string="Type"`, `required=True`, `default="group"` |
| `zalo_id` | Char | `string="Zalo ID"`, `required=True`, help: the group's ID, or the user's ID as the OA knows it — from the webhook's `recipient.id` of a group message or `sender.id` of a 1:1 message |
| `active` | Boolean | `default=True` |

### `zalo.message` — `models/zalo_message.py` (step 2)

`_name = "zalo.message"`, `_description = "Zalo Message"`, `_order = "id desc"`.

| Field | Type | Attributes |
|---|---|---|
| `recipient_type` | Selection | the destination's selection, `string="Type"` — not `required` (D11) |
| `recipient_id` | Char | `string="Zalo ID"` — not `required` (D11) |
| `destination_id` | Many2one → `zalo.destination` | `ondelete="set null"`, `index=True` |
| `text` | Text | — not `required` (D11) |
| `state` | Selection | `[("queued", "Queued"), ("sent", "Sent"), ("failed", "Failed")]`, `required=True`, `default="queued"`, `index=True` |
| `attempts` | Integer | `readonly=True` |
| `next_attempt_at` | Datetime | `string="Next Attempt"`, `readonly=True`, `index=True`, help: set after a retryable failure; the message is not sent before it (D17) |
| `last_error` | Text | `readonly=True` |
| `zalo_response` | Text | `string="Zalo Response"`, `readonly=True` |
| `sent_at` | Datetime | `readonly=True` |
| `sent_to` | Char | `readonly=True`, help: the recipient Zalo was given, as `<type>:<id>` — another than the intended one when a redirect is configured (divergence 4) |
| `res_model` | Char | `string="Source Model"`, `index=True` |
| `res_id` | Many2oneReference | `model_field="res_model"`, `string="Source Record"` |
| `template_id` | Many2one → `zalo.template` | step 3; `ondelete="set null"`, `readonly=True` (divergence 3) |

| Constant | Value |
|---|---|
| `MAX_ATTEMPTS` | 5 |
| `BATCH_SIZE` | 50 |
| `RETENTION_DAYS` | 30 |
| `RETRY_DELAY` | 5 minutes (D17) |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_display_name` | `@api.depends("destination_id", "recipient_type", "recipient_id")` | the destination's name, or `<type>:<id>` |
| `create` | `@api.model_create_multi` | `super()`, then `_trigger()` on the send cron when any created record is queued (D10) |
| `_queue` | `@api.model` | `_queue(text, recipient_type=None, recipient_id=None, destination=None, record=None)`: never raises (D11). The destination, when given, supplies type and ID; an archived destination, or no recipient or no text, gives a failed message saying so. Creates as superuser with `res_model`/`res_id` from `record`. Returns the message, or an empty recordset. Step 3 adds `template=None`, kept as `template_id`, and `error=None`: given, the message is created *failed* with that error, whatever else it has |
| `_queue_from_template` | `@api.model` | step 3; `_queue_from_template(template, records, destinations)`: never raises (D19). `self.env.flush_all()`, then in `try:` and a savepoint, `template.sudo()._render_field("body", records.ids)` (D19); on any exception, log it and keep its text as the error for every record. Then one `_queue()` per record and destination — the rendered text, or the error — with `template` and `record`. Nothing when there are no records or no destinations |
| `_queue_from_request` | `@api.model` | step 4; `_queue_from_request(payload)` → `(status, result)`, the body of `/zalo/send` (D26): the user without `zalo_oa.group_zalo_sender`, `(403, {"ok": false, "error": …})`; a payload refused by the module function `_payload_error(payload)` — its error text, or `False` — `(400, {"ok": false, "error": …})`; otherwise `_queue(text, recipient_type=…, recipient_id=recipient)`, the message read as superuser, `(200, {"ok": <queued>, "id": <id or false>})`, with `error` — the message's `last_error` — when not queued |
| `_redirect` | `@api.model` | parses `zalo_redirect_recipient`: `False` when unset; `(type, id)` when `group:<id>` or `user:<id>`; raises `ValueError` when malformed (D14) |
| `_due_domain` | `@api.model` | queued, and `next_attempt_at` empty or past (D17) |
| `_write_result` | — | `ensure_one`; writes one send's outcome in a savepoint of its own — step 4 of `_send` |
| `_send` | — | `ensure_one`; one message, below |
| `_cron_send` | `@api.model` | the send cron, below; never raises (D12) |
| `action_retry` | — | failed messages back to queued, `attempts` 0, `last_error` and `next_attempt_at` cleared; wakes the send cron |
| `_gc_old_messages` | `@api.autovacuum` | unlinks sent and failed messages whose `create_date` is older than `RETENTION_DAYS` (D16) |

**`_cron_send()`** (D12, D15): with no configured app, or no current token with an access token,
return — the messages stay queued. Otherwise take the oldest `BATCH_SIZE` due messages (`_due_domain`); for each,
`try: message._send(token)` and, on an unexpected exception, log it and count a failed attempt in a
savepoint; after each message, commit when `_zalo_auto_commit()`. Then
`self.env["ir.cron"]._notify_progress(done=<processed>, remaining=<due left>)`. The whole body is
inside `try`/`except Exception` that logs, so the cron always finishes.

**`_send(token)`**:

1. The recipient: `_redirect()`; on `ValueError`, fail the message — *zalo_redirect_recipient is
   malformed* — and stop. Redirected: send to it, the text prefixed `[→ <display_name>] `. Otherwise
   the message's own type and ID; none, fail it.
2. `send_text(token.access_token, …)`, the access token read before the call as `stale`.
3. *expired*: `token._refresh(stale_access_token=stale)` — outside any savepoint (D12). When it
   returns `True`, re-read the token and send once more; the second result is used as it is, an
   *expired* one counting as *retry*. When it returns `False`, the result is *retry* with the token's
   `last_error`.
4. Write the result in a savepoint: *sent* — `state` sent, `sent_at` now, `sent_to`, `zalo_response`,
   `last_error` cleared; *retry* — `attempts` + 1, `last_error`, and `state` failed once `attempts`
   reaches `MAX_ATTEMPTS`, otherwise `next_attempt_at` = now + `attempts × RETRY_DELAY`; *failed* —
   `state` failed, `attempts` + 1, `last_error`, `zalo_response`. Sent and failed clear
   `next_attempt_at`.

A serialization failure inside `_refresh()` returns `True` (step 1, D3) while this transaction still
reads the old token, so the retry is *expired* again and counts as *retry*: the message stays queued,
and the next run sends with the new pair (design §"Module design", step 2). It costs one of the five
attempts — accepted: the collision is rare, and a separate *refreshed elsewhere* result would add a
branch for it.

### `zalo.template` — `models/zalo_template.py` (step 3)

`_name = "zalo.template"`, `_description = "Zalo Template"`, `_inherit = ["mail.render.mixin"]`,
`_unrestricted_rendering = True` (D18), `_order = "name"`.

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | `required=True`, `translate=True` |
| `model_id` | Many2one → `ir.model` | `string="Applies to"`, `required=True`, `ondelete="cascade"`, `domain=[("transient", "=", False)]` |
| `model` | Char | `related="model_id.model"`, `store=True`, `index=True`, `string="Model"` |
| `body` | Text | `required=True`, **not** translated (divergence 7), help: the message, with placeholders such as `{{ object.name }}` for the record's fields; plain text, not HTML |

| Method | Decorator | Behaviour |
|---|---|---|
| `_compute_render_model` | `@api.depends("model")` | `render_model` = `model` — the mixin's hook, as SMS overrides it (`sms/models/sms_template.py:36-39`) |

### `ir.actions.server` — `models/ir_actions_server.py` (step 3)

`_inherit = "ir.actions.server"`.

| Field | Type | Attributes |
|---|---|---|
| `state` | Selection | `selection_add=[("zalo", "Send Zalo Message")]`, `ondelete={"zalo": "cascade"}` — SMS's shape (`sms/models/ir_actions_server.py:13-15`) |
| `zalo_template_id` | Many2one → `zalo.template` | `string="Zalo Template"`, `ondelete="set null"` |
| `zalo_destination_ids` | Many2many → `zalo.destination` | `relation="ir_act_server_zalo_destination_rel"`, `string="Zalo Destinations"` |

| Method | Decorator | Behaviour |
|---|---|---|
| `_check_zalo_template_model` | `@api.constrains("model_id", "zalo_template_id")` | `ValidationError` when the template's model is not the action's (D21) |
| `_run_action_zalo_multi` | — | `eval_context=None`: nothing when there is no template, no destination, or `_is_recompute()` (D20); otherwise the records of `eval_context["records"]` or `["record"]` to `zalo.message._queue_from_template(self.zalo_template_id, records, self.zalo_destination_ids)`. Returns `False`, as SMS's does |

The server action runs as whatever user the automation runs it with — `base_automation` runs its
actions through `sudo()` (`base_automation/models/base_automation.py:737`) — and queueing creates as
superuser in any case (D11), so no access to templates or messages is needed by the user whose save
triggered it.

### Group — `security/zalo_security.xml` (step 4)

| XML id | Content |
|---|---|
| `group_zalo_sender` | `res.groups`, *Zalo sender*, comment: may call `/zalo/send`; grants no access to any record. Held by a technical user with no other group, whose API key an administrator creates (D27) |

### Routes — `controllers/main.py` (step 4)

`ZaloController(http.Controller)`.

| Route | Decorator | Behaviour |
|---|---|---|
| `/zalo/authorize` | `type="http"`, `auth="user"`, `methods=["GET"]` | not a system administrator: 403. Otherwise `_authorize_start(<base URL>/zalo/callback)` and `request.redirect(<the returned URL>, local=False)` — the default `local=True` strips scheme and host and would redirect within Odoo (`odoo/odoo/http.py:1942-1947`); a `UserError` is answered as a `text/plain` page |
| `/zalo/callback` | `type="http"`, `auth="public"`, `methods=["GET"]`, `csrf=False`, `save_session=False` | `_authorize_finish(state, code)` as superuser with the query's `state` and `code`; a short `text/plain` page saying whether the app was authorized, and why not — plain, since the reason may carry Zalo's text. Never a token on the page |
| `/zalo/send` | `type="http"`, `auth="bearer"`, `methods=["POST"]`, `csrf=False`, `save_session=False` | the body by `request.get_json_data()`, `None` when it raises `ValueError` — not JSON; then `_queue_from_request(payload)` as the key's user, answered with `make_json_response(result, status=status)` (D26) |

The payload of `/zalo/send`: `{"recipient_type": "user" | "group", "recipient": "<Zalo ID>", "text": "…"}`
(design, phase 2 step 1).

## Data — `data/ir_cron.xml`

| XML id | Content |
|---|---|
| `ir_cron_zalo_token_refresh` | `name` *Zalo: refresh token*, `model_id` `model_zalo_token`, `state` `code`, `code` `model._cron_refresh()`, `interval_number` 1, `interval_type` `hours`, `active` `True`, `user_id` `base.user_root` |

| `ir_cron_zalo_send` | step 2; `name` *Zalo: send queued messages*, `model_id` `model_zalo_message`, `state` `code`, `code` `model._cron_send()`, `interval_number` 5, `interval_type` `minutes`, `active` `True`, `user_id` `base.user_root` — the catch-up; each queued message also wakes it (D10) |

Loaded with `noupdate="1"`, so an administrator's change to the cadence survives upgrades (design,
*Rules* 5).

## Access — `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_zalo_token_system` | `model_zalo_token` | `base.group_system` | 1 | 1 | 1 | 1 |
| `access_zalo_destination_system` | `model_zalo_destination` | `base.group_system` | 1 | 1 | 1 | 1 |
| `access_zalo_message_system` | `model_zalo_message` | `base.group_system` | 1 | 1 | 1 | 1 |
| `access_zalo_template_system` | `model_zalo_template` | `base.group_system` | 1 | 1 | 1 | 1 |

Destinations and the message log are configuration and audit, for administrators. Queueing needs no
access: `_queue()` creates as superuser (D11).

## Views — `views/zalo_token_views.xml`

| XML id | Type | Content |
|---|---|---|
| `zalo_token_view_list` | list | `app_id`, `is_configured_app`, `expires_at`, `last_refresh_at`, `alert_user_id`; `decoration-muted="not is_configured_app"` |
| `zalo_token_view_form` | form | header: button `action_refresh_now`, `string="Refresh now"`, `type="object"`, `invisible="not is_configured_app"`; from step 4 button `action_authorize`, `string="Authorize"`, same `invisible`; sheet: `app_id`, `is_configured_app`, `access_token` and `refresh_token` (`widget="password"`, D8), `expires_at`, `last_refresh_at`, `refresh_requested`, `alert_user_id`, `last_error`; chatter |
| `zalo_token_action` | `ir.actions.act_window` | *Zalo Tokens*, `zalo.token`, `list,form` |
| `menu_zalo_root` | menu | *Zalo*, parent `base.menu_custom`, sequence 90 |
| `menu_zalo_token` | menu | *Tokens*, parent `menu_zalo_root`, action `zalo_token_action`, sequence 10 |

*Refresh now* is shown on the configured app's row only: refreshing another app's row is what the
configuration exists to prevent.

## Views — `views/zalo_destination_views.xml` (step 2)

| XML id | Type | Content |
|---|---|---|
| `zalo_destination_view_list` | list | `editable="bottom"`: `name`, `recipient_type`, `zalo_id`, `active` (`widget="boolean_toggle"`) |
| `zalo_destination_view_search` | search | `name`, `zalo_id`; filter *Archived* (`active = False`) |
| `zalo_destination_action` | `ir.actions.act_window` | *Zalo Destinations*, `zalo.destination`, `list` |
| `menu_zalo_destination` | menu | *Destinations*, parent `menu_zalo_root`, sequence 20 |

## Views — `views/zalo_message_views.xml` (step 2)

| XML id | Type | Content |
|---|---|---|
| `zalo_message_view_list` | list | `create_date`, `display_name` (*Recipient*), `state` (`widget="badge"`, `decoration-success` sent, `decoration-danger` failed, `decoration-info` queued), `attempts`, `sent_at`, `last_error` (`optional="show"`) |
| `zalo_message_view_form` | form | header: button `action_retry`, `string="Retry"`, `invisible="state != 'failed'"`, and `state` (`widget="statusbar"`); sheet: `destination_id`, `recipient_type`, `recipient_id`, `text` — editable while queued (`readonly="state != 'queued'"`), so an administrator can queue a test message by hand — then `attempts`, `sent_at`, `sent_to`, `res_model`, `res_id`, `last_error`, `zalo_response` |
| `zalo_message_view_search` | search | `text`, `recipient_id`, `destination_id`; filters *Queued*, *Sent*, *Failed*; group-by state, destination |
| `zalo_message_action` | `ir.actions.act_window` | *Zalo Messages*, `zalo.message`, `list,form` |
| `menu_zalo_message` | menu | *Messages*, parent `menu_zalo_root`, sequence 30 |

## Views — `views/zalo_template_views.xml` (step 3)

| XML id | Type | Content |
|---|---|---|
| `zalo_template_view_list` | list | `name`, `model_id` |
| `zalo_template_view_form` | form | `name`, `model_id` (`options="{'no_create': True}"`), `body` (plain text, `placeholder` *New request {{ object.name }} on {{ object.equipment_id.name }}*) |
| `zalo_template_view_search` | search | `name`, `model_id`; group-by model |
| `zalo_template_action` | `ir.actions.act_window` | *Zalo Templates*, `zalo.template`, `list,form` |
| `menu_zalo_template` | menu | *Templates*, parent `menu_zalo_root`, sequence 25 |

## Views — `views/ir_actions_server_views.xml` (step 3)

| XML id | Inherits | Position | Content |
|---|---|---|---|
| `ir_actions_server_view_form` | `base.view_server_action_form` | field `link_field_id` after — SMS's anchor (`sms/views/ir_actions_server_views.xml:9`) | `zalo_template_id` (`domain="[('model_id', '=', model_id)]"`, `context="{'default_model_id': model_id}"`, `invisible="state != 'zalo'"`, `required="state == 'zalo'"`), `zalo_destination_ids` (`widget="many2many_tags"`, same `invisible` and `required`) |

The message form (step 2) gains `template_id`, read-only, beside the source record.

## Tests

The configuration is patched with `patch.dict(odoo.tools.config.options, {...})`, **per test** — in
`setUp` through `self.startPatcher`, or in a `with` block. Never as a class patcher: after every test
`TransactionCase` reads `.target` from each active patch (`odoo/odoo/tests/common.py:1117-1122`),
which `patch.dict` lacks, so a class-level one errors every test (first run, 2026-10-07). HTTP is patched at
`odoo.addons.zalo_oa.tools.zalo_client.requests.post`, returning a stub with `status_code` and
`json()`: Odoo's tests refuse outbound requests at `requests.Session.send`
(`odoo/odoo/tests/common.py:295-333`), and the client must never reach it.

### `tests/test_zalo_client.py`

`TestZaloClient(BaseCase)`, `at_install`: no records.

| Test | Asserts |
|---|---|
| `test_refresh_request_shape` | `refresh_tokens` posts to `OA_TOKEN_URL` with `secret_key` in the headers and `app_id`, `refresh_token`, `grant_type=refresh_token` as form data |
| `test_success` | a 200 with both tokens and `expires_in` gives `ok` and the three values, `expires_in` an integer |
| `test_missing_expires_in` | without `expires_in`, `DEFAULT_EXPIRES_IN` |
| `test_zalo_error_in_body` | a 200 with `error: -14020` is not `ok`, and its text asks to authorize again |
| `test_not_json` | a body that is not JSON is not `ok` |
| `test_network_error` | `requests.ConnectionError` raised by the post is not `ok`, and nothing propagates |
| `test_no_secret_in_error` | in every failure above, neither the secret nor either token appears in the returned text |
| `test_config_read` | with `zalo_app_id = " A1 "` patched, `get_zalo_config()["app_id"]` is `"A1"`; without it, `False` |
| `test_send_request_shape` | step 2; a group send posts to the group URL with `{"recipient": {"group_id": …}, "message": {"text": …}}` and the `access_token` header; a user send to the 1:1 URL with `user_id` |
| `test_send_sent` | step 2; HTTP 200 with `error` 0 is *sent*, the body returned |
| `test_send_expired` | step 2; HTTP 200 with `error` −216, and HTTP 401, are both *expired* |
| `test_send_permanent_error` | step 2; HTTP 200 with `error` −224 is *failed* |
| `test_send_retryable` | step 2; a network error, a body that is not JSON and an HTTP 503 are *retry* |
| `test_send_no_token_in_error` | step 2; in every failure above the access token is not in the error text |

### `tests/test_zalo_token.py`

`TestZaloToken(TransactionCase)`, `@tagged("post_install", "-at_install")`: the access test creates a user, a core
record later modules extend (`addons/CLAUDE.md`, *Tests that create core records*).
The configuration names app `T`. Rows: `T`, with an access and a refresh token expiring in 2 hours;
`P`, another app's, likewise.

| Test | Asserts |
|---|---|
| `test_current_is_the_configured_app` | `_get_current()` is the `T` row; with no app configured, empty |
| `test_refresh_saves_the_pair` | a successful refresh writes both new tokens, `expires_at` about now + `expires_in`, `last_refresh_at`, and clears `last_error` and `refresh_requested` |
| `test_refresh_failure_keeps_the_pair` | a failed refresh leaves both tokens unchanged and writes `last_error` |
| `test_refresh_skips_when_already_refreshed` | `_refresh(stale_access_token="old")` on a row whose access token is already another calls nothing and returns `True` (D4) |
| `test_cron_refreshes_when_expiring` | the cron refreshes `T`, expiring in 2 hours |
| `test_cron_skips_fresh_token` | with `T` expiring in 20 hours, the cron calls nothing |
| `test_cron_refresh_requested` | `action_refresh_now` on a fresh `T` sets `refresh_requested`; the cron then refreshes it |
| `test_cron_never_touches_other_apps` | after the cron, `P`'s tokens are unchanged and no request named app `P` |
| `test_cron_without_app` | with no app configured, the cron calls nothing and raises nothing |
| `test_cron_never_raises` | with the client raising an unexpected exception, the cron returns normally and `T`'s `last_error` is set (D6) |
| `test_cron_survives_serialization_failure` | with the row lock patched to raise `SerializationFailure`, the cron returns normally, Zalo is not called, and `T` is unchanged — `last_error` included (D3, D6) |
| `test_health_alert_once` | with `last_refresh_at` three days ago and an alert user, the cron schedules one warning activity for that user; a second run schedules no second one (D7) |
| `test_one_row_per_app` | a second row for app `T` raises `IntegrityError` |
| `test_tokens_for_administrators_only` | an internal user outside *Settings* reads a partner — the positive control — and reading a `zalo.token` raises `AccessError` |

`test_one_row_per_app` carries `@mute_logger("odoo.sql_db")` and a savepoint, as every constraint
test in the repository does.

**Checked in the UI:** *Settings → Technical → Zalo → Tokens* in developer mode for an administrator;
a row created for the configured app **with no refresh token**, *Refresh now* waking the cron and
`last_error` reporting the missing refresh token seconds later; the alert user offered only among
administrators; a row for another app muted and without the button. **No live refresh in step 1:**
the only refresh token is app A's, which the Apps Script still refreshes — a refresh from Odoo would
rotate it and stop the live chat's replies. The live refresh is checked at the design's phase 2,
step 3, after the Apps Script stops refreshing.

### `tests/test_zalo_message.py` (step 2)

`TestZaloMessage(TransactionCase)`, `@tagged("post_install", "-at_install")`: the access test creates a
user. The configuration — app `T` and its secret — is patched per test in `setUp`, as in
`test_zalo_token.py`. Fixtures: `T`'s token row with an access and a refresh token expiring in 20 hours;
a group destination. `send_text` is patched at `odoo.addons.zalo_oa.models.zalo_message.send_text`,
`refresh_tokens` as in step 1.

| Test | Asserts |
|---|---|
| `test_queue_wakes_the_cron` | `_queue()` creates a queued message and an `ir.cron.trigger` for the send cron |
| `test_queue_from_destination` | a destination supplies the type and ID; the source record is kept as `res_model`/`res_id` |
| `test_queue_never_raises` | no recipient, no text, or an archived destination each give a failed message saying why, and no exception; with `create` itself patched to raise, `_queue()` returns an empty recordset and raises nothing (D11) |
| `test_queue_flushes_the_callers_writes_first` | with `flush_all` patched to raise, `_queue()` lets that error propagate rather than catching it — the caller's own error is the caller's (D11) |
| `test_cron_sends` | a queued message is sent: `state` sent, `sent_at`, `sent_to` the destination, `zalo_response` kept, the call carrying `T`'s access token |
| `test_cron_without_app` | with no app configured, nothing is called and the message stays queued |
| `test_cron_ignores_other_apps_token` | with only another app's token row, nothing is called |
| `test_expired_refreshes_and_retries` | an *expired* answer, then a successful refresh, then *sent*: the message is sent with the new access token, and the refresh was asked with the old one |
| `test_expired_after_refresh_stays_queued` | *expired* twice around a successful refresh: queued, `attempts` 1 |
| `test_failed_refresh_stays_queued` | *expired*, then a failed refresh: queued, `attempts` 1, the token's error in `last_error` |
| `test_retry_waits_for_its_turn` | after a *retry* the message has a future `next_attempt_at`, and a second run at once sends nothing (D17) |
| `test_retry_until_max_attempts` | *retry* five times over five runs, the message made due before each: failed after the fifth, `attempts` 5 |
| `test_permanent_error_fails_at_once` | a *failed* answer fails the message on the first run, Zalo's body kept |
| `test_redirect` | with `zalo_redirect_recipient = group:G`, the message goes to group `G`, its text starting `[→ <destination name>] `, `sent_to` `group:G`, and the message still names its destination |
| `test_malformed_redirect_fails` | with `zalo_redirect_recipient = bogus`, the message fails naming the setting and nothing is called (divergence 5) |
| `test_cron_never_raises` | `send_text` raising `RuntimeError` counts a failed attempt on the message; the cron returns normally (D12) |
| `test_batch_progress` | with `BATCH_SIZE` patched to 2 and three queued messages, one run sends two and calls `_notify_progress(done=2, remaining=1)` — observed by patching it on the `ir.cron` class, since it returns at once without the runner's `ir_cron_progress_id` in the context (`odoo/odoo/addons/base/models/ir_cron.py:742-743`) (D15) |
| `test_retry_action` | `action_retry` on a failed message makes it queued with `attempts` 0 and no error |
| `test_old_messages_vacuumed` | a sent and a failed message created 31 days ago are removed by `_gc_old_messages`; a queued one of the same age, and a sent one of yesterday, are kept (D16) |
| `test_log_for_administrators_only` | an internal user outside *Settings* reads a partner — the positive control — and reading a message raises `AccessError`; `_queue()` called as that user still queues |

`create_date` is backdated with SQL for the vacuum test.

**Checked in the UI** (step 2): *Destinations* and *Messages* under *Settings → Technical → Zalo*; a
message queued by hand to a test group, with a **borrowed access token** pasted into the token row and
**no refresh token** (design, phase 1), arriving in the chat within seconds and shown *Sent*; a message to
a bad ID failing with Zalo's error and *Retry* re-queuing it; with `zalo_redirect_recipient` set, a
message to another destination arriving in the redirect chat, prefixed with its intended recipient.

### `tests/test_zalo_template.py` (step 3)

`TestZaloTemplate(TransactionCase)`, `@tagged("post_install", "-at_install")`: the fixtures create
partners. `tearDown` calls `self.env["base.automation"]._unregister_hook()`: creating an automation rule
patches `create`, `write` and `_compute_field_value` onto the model class, the rollback does not undo it,
and Odoo's after-test attribute check then fails every later test — core's own tests unregister the same
way (`base_automation/tests/test_automation.py:12-14`) (first run, 2026-10-07). Templates and actions are on `res.partner`: two destinations; a template *New partner
{{ object.name }}*; a broken template *{{ object.nmae }}*; a server action of state `zalo` with the first
template and both destinations.

| Test | Asserts |
|---|---|
| `test_render` | the template renders *New partner Ann* for a partner named Ann |
| `test_action_queues_per_record_and_destination` | the action run on two partners queues four messages, each with the rendered text, its destination, the partner as source record and the template |
| `test_action_without_destinations` | with no destination the action queues nothing and raises nothing |
| `test_template_model_must_match` | a template on `zalo.destination` set on a `res.partner` action raises `ValidationError` (D21) |
| `test_broken_template_does_not_block_save` | with an automation rule on partner creation running an action with the broken template, creating a partner **succeeds**, and a failed message per destination carries the rendering error and the partner as source (D19) — the isolation rule's own test |
| `test_manual_run_by_a_user` | the action run by an internal user outside *Settings* renders and queues as when run by the automation (D19) |
| `test_automation_queues_on_save` | with the same rule on the working template, creating a partner named Bob queues *New partner Bob* to both destinations |
| `test_queue_from_template_flushes_first` | with `flush_all` patched to raise, inside `assertRaises`, the error propagates — the caller's own error is the caller's (D19) |

`zalo.message`'s logger is muted where a rendering error is logged.

**Checked in the UI** (step 3): *Templates* under *Settings → Technical → Zalo*; a template on
*Maintenance Request*; an automation rule on request creation with the action *Send Zalo Message*, the
template offered only for the rule's model, destinations as tags; a new request delivered to the test
group with its fields filled in; a template with a mistyped placeholder failing as a message, the
request saving normally.

### `tests/test_zalo_authorize.py` (step 4)

`TestZaloAuthorize(TransactionCase)`, `at_install`: no core records. Configuration patched per test in
`setUp` (app `T`, its secret); `exchange_code` patched at `odoo.addons.zalo_oa.models.zalo_token.exchange_code`.

| Test | Asserts |
|---|---|
| `test_pkce_pair` | the verifier is 64 URL-safe characters and the challenge is base64url of its SHA-256, without padding |
| `test_permission_url` | the URL carries `app_id`, `redirect_uri`, `code_challenge` and `state` |
| `test_start_creates_the_row` | with no row for `T`, `_authorize_start` creates it and stores a state, a verifier and the time; the URL's challenge matches the stored verifier |
| `test_start_without_app` | with no app configured, `UserError` |
| `test_finish_saves_the_pair` | a matching state within ten minutes exchanges the code with the stored verifier and writes the pair; the pending authorization is cleared |
| `test_finish_wrong_state` | a different state calls nothing, writes no token, and leaves the pending authorization in place (D25) |
| `test_finish_non_ascii_state` | a state of `é` is refused like any other wrong one, without raising (D23) |
| `test_finish_expired` | a state eleven minutes old is refused, nothing called, and the pending authorization cleared |
| `test_finish_without_code` | a matching state with an empty code is refused, nothing called, and the pending authorization cleared |
| `test_finish_without_app` | with no app configured, refused and nothing called |
| `test_finish_locks_before_exchange` | with `_lock_row` patched to raise `SerializationFailure`, the error propagates and nothing is called (D25) |
| `test_finish_failed_exchange` | a failed exchange writes `last_error`, keeps any existing pair, and clears the pending authorization |
| `test_state_used_once` | a second `_authorize_finish` with the same state is refused |

### `tests/test_zalo_send.py` (step 4)

`TestZaloSend(TransactionCase)`, `@tagged("post_install", "-at_install")`: the fixtures create users —
the technical user, with `group_zalo_sender` as its only group (D27), and an internal user without it.
`_queue_from_request` is called **as the technical user** (`with_user`), as the route calls it.

| Test | Asserts |
|---|---|
| `test_send_queues` | a valid payload answers 200 with `ok` true and an id, and that message is queued with the recipient and text — the positive control |
| `test_send_without_group` | as the internal user, 403, and nothing is queued |
| `test_send_bad_payload` | no body (`None`), a list, a `recipient_type` of `channel`, a numeric `recipient`, an empty `text` and a missing `text` each answer 400, and nothing is queued (D26) |
| `test_send_reports_a_failed_queue` | with `_queue_values` patched to raise, 200 with `ok` false, an id and the error: the failed message is read back for a user who cannot read the log |

**No `HttpCase`:** on this image the post-install run pregenerates every asset bundle before a suite
holding one (`odoo/odoo/service/server.py:1437-1440`), and core's test assets are stripped at build
(`images/odoo/Dockerfile:49`), so the run aborts. The routes stay thin, and their HTTP wiring is checked
in the UI.

**Checked in the UI** (step 4): *Authorize* on the configured app's row redirecting to Zalo's permission
page, its `redirect_uri` the instance's `/zalo/callback`; `/zalo/callback?state=x&code=y` answering a
plain-text refusal; the technical user, created with its key by an administrator, and `curl` to
`/zalo/send` — no key 401, the key of an internal user without *Zalo sender* 403, a malformed payload
400, a valid one 200 and the message arriving; a read of `res.partner` over XML-RPC with the technical
user's key refused. For app B once it exists — or for app A at the design's phase 2 instead of copying
the Apps Script's refresh token — the admin's approval returning to `/zalo/callback` and the row
holding a pair. **Not before phase 2:** authorizing app A while the Apps Script still refreshes it may
invalidate the script's pair (design, open questions).

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Connects the instance to a Zalo Official Account through its own Zalo app: Odoo holds the app's tokens and refreshes them, and — from later steps — sends notifications from automation rules and templates |
| `readme/CONFIGURE.md` | Name the instance's Zalo app in `odoo.conf` — `zalo_app_id`, `zalo_app_secret` (and later `zalo_oa_secret`, `zalo_redirect_recipient`). On this instance through `ADDITIONAL_ODOO_RC`, built in `compose.yml.template` as a YAML `|-` block of `key = ${VARIABLE}` lines indented further than the key, the values in `.env` as plain single-line variables — a `\n` inside a `.env` value is not turned into a newline here. Without an app ID the module does nothing. Each instance has its own app; a token row for another app, as left by a database restore, is ignored. Step 4 adds: register `<base URL>/zalo/callback` as the app's callback URL in the Zalo console; for `/zalo/send`, a technical user with *Zalo sender* as its only group — no user type, no password — whose one persistent API key an administrator creates once and revokes when needed. The user is not edited in the user form, which requires a user type |
| `readme/USAGE.md` | Under *Settings → Technical → Zalo → Tokens* (developer mode), create the row for the configured app and paste its refresh token, or authorize it (step 4). The refresh cron runs hourly and refreshes when fewer than six hours remain; *Refresh now* asks it to refresh at its next run, within seconds. Set an alert user — a system administrator — to be told when the token has not been refreshed for two days. **Do not put a refresh token in Odoo while the Apps Script still refreshes it:** Odoo's cron will rotate it, and the Apps Script's replies stop. Step 2 adds: *Destinations*, named group chats and users; *Messages*, the queue and log — a message can be queued by hand, failed ones retried; messages go out within seconds, and a test instance's `zalo_redirect_recipient` sends every one to its test chat instead Step 3 adds: *Templates*, message text with `{{ object.field }}` placeholders for one model; an automation rule sends with the server action *Send Zalo Message*, a template and destinations. A template that fails to render becomes a failed message; the record still saves An *On save* rule needs *When updating* fields — with none it sends on every save and every recompute, duplicates included; watch *Created on* to send on creation, *Stage* for a stage change Step 4 adds: *Authorize* on the token row, which sends an administrator to Zalo and back to get the app's first token pair, within ten minutes; and `/zalo/send`, for the Apps Script: `POST` `{recipient_type, recipient, text}` as JSON with `Authorization: Bearer <the technical user's key>` (CONFIGURE), answered `{ok, id}` — a 400 names a malformed payload, a 401 a missing or revoked key |
