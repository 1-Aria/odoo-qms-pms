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
`zalo_…` key per line. A `\n` inside a `.env` value is not turned into a newline here. Later steps
add `zalo_oa_secret` and `zalo_redirect_recipient`: one more line in the block, one more variable in
`.env`.

Without an app ID the module does nothing. Each instance has its own app; a token row for another
app, as a database restore leaves it, is ignored.
