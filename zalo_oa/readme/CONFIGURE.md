Name the instance's Zalo app in `odoo.conf`:

```ini
zalo_app_id = ...
zalo_app_secret = ...
```

On this instance `odoo.conf` is generated at container start, and its template appends the
`ADDITIONAL_ODOO_RC` environment variable to it. Build that variable in the `odoo` service of
`compose.yml.template`, as a YAML block whose lines are indented further than its key, and keep the
values in `.env` as plain single-line variables:

```yaml
      ADDITIONAL_ODOO_RC: |-
        zalo_app_id = ${ZALO_APP_ID}
        zalo_app_secret = ${ZALO_APP_SECRET}
```

```ini
ZALO_APP_ID=...
ZALO_APP_SECRET=...
```

Render `compose.yml` from the template, recreate the container, and check that `odoo.conf` has one
`zalo_…` key per line. A `\n` inside a `.env` value is not turned into a newline here. On a test
instance, add `zalo_redirect_recipient` (see Usage) the same way: one more line in the block, one
more variable in `.env`.

Without an app ID the module does nothing. Each instance has its own app; a token row for another
app, as a database restore leaves it, is ignored.

**Authorization.** In the Zalo console, register `<base URL>/zalo/callback` as the app's Official
Account Callback URL — on this instance `https://odoo.quangphuong.net/zalo/callback`.

**The Apps Script's sender.** `/zalo/send` takes the API key of a technical user whose only group is
*Zalo sender*: no user type and no password, so the key reads and writes nothing else in Odoo. An
administrator creates the user and its one persistent key once, and revokes the key when needed. A key
created in a user's own preferences expires within 90 days, and the Apps Script would then stop
replying. Do not edit this user in the user form, which requires a user type.
