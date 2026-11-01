# base_time_parameter_strict

A strict reader for OCA's time-dependent parameters: one method that returns a parameter's value in
force on a date, treats every stored value, 0 and False included, as a value, and raises when there is
none. Used by the payroll modules; offered to IE in place of its own reader (Payroll Technical
Design PTD-02, PTD-OPEN-01). Design: `docs/HR-Contract-Payroll/Payroll Technical Design v0.3.md` §4.1.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | `base.time.parameter._strict_get`; tests | done | 2026-11-01, one run: `base_time_parameter` installed (`-i`, `exit=0`), then `-i base_time_parameter_strict` with tests: `exit=0`, 13 tests, 0 failures |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §4.1: finds the parameter in the given company, else with no company | the same, read as superuser (D1) | OCA's global record rule on parameters is `[('company_id', 'in', company_ids)]` (`oca/server-tools/base_time_parameter/security/security.xml:6-13`): a parameter with no company matches no user, so only a superuser read finds it. The rule also hides such parameters from every screen; §1's "statutory values ship with no company" is therefore corrected in the payroll design (see Decisions D7) |
| 2 | §4.1: "converts its value by the parameter's type" | the module converts itself and raises on a value that does not convert (D3, D4) | OCA's `_get` has no branch for its own `record` type, testing `reference` and `reference_id` instead (`models/base_time_parameter.py:105-108`), and its value validators run only on the form's onchange (`models/base_time_parameter_version.py:77-92`), so data files and imports can store any text |

## Decisions

| # | Decision |
|---|---|
| D1 | **Read as superuser.** Parameters are configuration that calculations need whatever the user's groups: managing them needs OCA's hidden group `base_time_parameter.group_time_parameter` (`security/ir.model.access.csv`), and its company rule hides parameters without a company (divergence 1). The method searches and reads with `sudo()`; it is private, so it cannot be called over RPC |
| D2 | **Lookup:** parameters with the `code` in the given company (default: the environment's company); if none, parameters with the `code` and no company. More than one at the level found raises: OCA's `unique (code, company_id)` (`models/base_time_parameter.py:114-120`) does not stop two parameters with no company, since PostgreSQL treats NULLs as distinct. `model_id` is ignored: the code is the key |
| D3 | **Version:** the version with the latest `date_from` on or before `date`. No such version raises. A version is never skipped for its value |
| D4 | **Conversion by the parameter's `type`,** done by this module: `boolean` accepts `True`/`False`/`1`/`0` in any case; `date` reads `YYYY-MM-DD`; `float` reads any float text; `integer` reads an integer text or a float text with no fraction; `json` is `json.loads`; `string` is the text; `record` is `value_reference`. A value that does not convert raises, naming the parameter, the version's date, the value and the type |
| D5 | **An empty value raises:** a version whose `value` is empty (or, for `record`, whose `value_reference` is empty) is a missing value, not a 0 or an empty text. A stored `0`, `0.0` or `False` is a value |
| D6 | **`date` is required.** No default to today: a calculation names the date it calculates for |
| D7 | **Not part of this module, recorded for the payroll design:** because of divergence 1, statutory parameters are created per company — for every company whose country is Vietnam — by `l10n_vn_payroll`, not with an empty company. Policy parameters were already per company. To be folded into the technical design with the `l10n_vn_payroll` doc |
| D8 | **No cache.** The payroll pay context reads each parameter once per run (design §4.1); a cache would add invalidation for no gain |
| D9 | **A `record` value cannot be stored through the ORM as OCA ships it:** `value_reference` is a `Reference` with an empty selection (`models/base_time_parameter_version.py:67`), and core refuses a reference to a model outside the selection (`odoo/odoo/fields.py`, `Reference.convert_to_cache`). A module that adds its model to the selection can store one; the reader returns it. The test writes the value through SQL, which the ORM reads back without that check |

## Folder structure

```
base_time_parameter_strict/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   └── base_time_parameter.py
├── tests/
│   ├── __init__.py
│   └── test_strict_get.py
└── readme/
    ├── DESCRIPTION.md
    └── USAGE.md
```

## Manifest

| Key | Value |
|---|---|
| `name` | `Time Parameter Strict Reader` |
| `summary` | `Read a time parameter's value on a date; zero and False are values, a missing value raises` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Technical` |
| `depends` | `base_time_parameter` |
| `data` | — |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import base_time_parameter` |
| `tests/__init__.py` | `from . import test_strict_get` |

## Access

No new model, no access file. Reading goes through D1.

## Models

### `base.time.parameter` — `models/base_time_parameter.py`

`_inherit = "base.time.parameter"`. No new fields.

**`_strict_get(code, date, company=None)`** — `@api.model`

| Argument | Type | Notes |
|---|---|---|
| `code` | str | the parameter's `code` |
| `date` | `datetime.date` or `datetime.datetime` | a datetime is reduced to its date; anything else raises `TypeError` |
| `company` | `res.company` record, or `None` | `None` → `self.env.company` |

Returns the converted value (D4). Steps:

0. `date`: a `datetime.datetime` becomes its date; anything not a `datetime.date` raises `TypeError`.
1. `Param = self.sudo()`; `company = company or self.env.company`.
2. `found = Param.search([("code", "=", code), ("company_id", "=", company.id)])`; if empty, `found = Param.search([("code", "=", code), ("company_id", "=", False)])`.
3. `len(found) > 1` → `UserError`: *Several time parameters have the code %(code)s (company %(company)s).*
4. `found` empty → `UserError`: *No time parameter with the code %(code)s (company %(company)s).*
5. `version` = the first of `found.version_ids.filtered(lambda v: v.date_from <= date).sorted("date_from", reverse=True)`; none → `UserError`: *Time parameter %(code)s has no value on %(date)s.*
6. Return `self._strict_convert(found, version)`.

**`_strict_convert(parameter, version)`** — `@api.model`. For `string`, the text is returned as stored. Every other text type is converted inside one `try`, a `ValueError` becoming the *invalid* error below.

| `parameter.type` | Returns | Empty (D5) | Invalid |
|---|---|---|---|
| `boolean` | `True` for `true`/`1`, `False` for `false`/`0`, case-insensitive | `value` empty | any other text |
| `date` | `datetime.date` from `YYYY-MM-DD` | `value` empty | not that format |
| `float` | `float(value)` | `value` empty | `ValueError` from `float` |
| `integer` | `int(f)` where `f = float(value)` and `f.is_integer()` | `value` empty | not a number, or a fraction |
| `json` | `json.loads(value)` | `value` empty | `ValueError` from `json.loads` |
| `string` | `value` | `value` empty | — |
| `record` | `version.value_reference` (a record) | `value_reference` empty | — |
| any other | — | — | `UserError`: *Time parameter %(code)s has a type this reader does not know: %(type)s.* |

Empty raises the `UserError` built by **`_strict_empty(parameter, version)`**: *Time parameter %(code)s has no value on %(date)s*, with the version's `date_from`. Invalid raises `UserError`: *Time parameter %(code)s, version of %(date_from)s: %(value)r is not a valid %(type)s.*

All messages are translatable (`self.env._(...)`).

## Tests

`TestStrictGet(TransactionCase)` in `tests/test_strict_get.py`, `@tagged("post_install", "-at_install")`: the fixtures create a company and a user, core records later modules extend.

**Fixtures:** `setUpClass` keeps `company_a` = `env.company`, creates `company_b` (`res.company`), and a user `plain_user` (login `test.strict.plain.user`) in `base.group_user` with companies `company_a` and `company_b`. Codes are prefixed `test.strict.` so they never meet the instance's parameters. **Helpers:** `_param(code, kind, versions, company=False)` creates a `base.time.parameter` named and coded `test.strict.<code>`, of type `kind`, with `version_ids` from `versions`, a list of `(date_from, value)` pairs, and `company_id` = `company` (a record or `False`); `_get(code, date, company=None)` calls `_strict_get` on `test.strict.<code>`.

| Test | Asserts |
|---|---|
| `test_zero_float_is_value` | a float parameter with `0.0` from 2026-01-01 returns `0.0` on 2026-06-01 (OCA's reader treats it as missing) |
| `test_false_boolean_is_value` | a boolean with `False` returns `False` |
| `test_latest_version_before_date` | versions 2026-01-01 → `2340000`, 2026-07-01 → `2530000`: 2026-06-30 returns 2,340,000; 2026-07-01 and 2026-12-31 return 2,530,000 |
| `test_before_first_version_raises` | 2025-12-31 on the parameter above raises `UserError` |
| `test_missing_code_raises` | an unknown code raises `UserError` whose message holds the code |
| `test_company_overrides_no_company` | `company_b` holds `1.0`, no-company holds `2.0`: with `company=company_b` returns `1.0`; with `env.company` returns `2.0` |
| `test_ambiguous_no_company_raises` | two no-company parameters with one code raise `UserError` |
| `test_types` | `integer` `"26"` → 26 (an `int`) and `"26.0"` → 26; `date` `"2026-10-24"` → `date(2026, 10, 24)`; `json` `'{"IV": 3700000}'` → the dict; `string` `"IV"` → `"IV"` |
| `test_record_type` | a `record` parameter with no reference raises `UserError`; after `value_reference` is set to `res.company,<company_b id>` through SQL and the field invalidated, it returns `company_b` (D9) |
| `test_invalid_values_raise` | `float` `"abc"`, `integer` `"26.5"`, `boolean` `"yes"`, `date` `"24/10/2026"`, `json` `"{IV: 1}"` each raise `UserError` (one `subTest` each) |
| `test_empty_value_raises` | a `float` version with no `value` raises `UserError` |
| `test_datetime_date` | a `datetime` argument returns the same as its date; a string argument raises `TypeError` |
| `test_plain_user_reads` | as `plain_user`: reading `base.time.parameter` directly raises `AccessError` (positive control of the restriction), and `_strict_get` on the same code returns the value (D1) |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | A strict reader for `base_time_parameter`: zero and False are values, a missing value, version, code or a value that does not convert raises; reads as superuser; company parameters before parameters with no company |
| `readme/USAGE.md` | Calling `self.env["base.time.parameter"]._strict_get("vn.si.reference_level", date)` from server code, with an optional `company`; the types and their text formats (D4); that parameters are managed by users in *Manage Time Parameters* |
