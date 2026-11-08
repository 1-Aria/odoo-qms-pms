# l10n_vn_payroll_garment

The garment company's current pay scheme (Pay Policy v0.5 §3–§11) as configuration for
`l10n_vn_payroll`: policy parameters, check levels, the productivity and grade scales, the pay
components, the salary rule categories, and one structure with a rule per component. A payroll
manager loads it into a company from *Settings → Payroll*; nothing is created at install.
Design: `docs/HR-Contract-Payroll/Payroll Technical Design v0.4.md` §28 (PTD-xx), on
`Pay Policy v0.5.md`. Engine: `docs/modules/l10n_vn_payroll.md`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | The loader: policy parameters and check levels, scales `PROD` and `GRADE`, the current scheme's components with the night components, `ATT`, `DUTY` and `PHONE` as inactive options, categories, the structure and its rules; the *Settings* button; tests on the loaded configuration, group G of the acceptance cases included; a test-only change in `l10n_vn_payroll` so its fixtures can take this configuration | done | 2026-11-08, one run each: `-u l10n_vn_payroll`, 224 tests, 0 failures (the refactor kept every engine test); `-i l10n_vn_payroll_garment`, 25 tests, 0 failures. Loaded in the UI into the garment company of the test copy, beside the trial's records: 35 components (3 inactive), scales `PROD` (the trial's, 5 cells) and `GRADE` (15), the 9 policy parameters, structure `VN_GARMENT` (id 125) with 35 rules, each on the component of its code; created records carry their Vietnamese names |
| 2 | `auditlog` rules (design §27), skipping models that already have a rule | planned | |
| 3 | Pay lines proposed on the contract from the pay group and the level or grade and step (design §7); the go-live helper, outside `addons/` (design §29 step 4) | planned | |
| 4 | Account mapping, after `l10n_vn_payroll_account` (design §28.2) | planned | |
| 5 | Following `l10n_vn_payroll` step 10: `vn.check.long_days` = *note* (quilting's double shifts); `OT_NIGHT` PIT treatment `exempt` (a premium on normal hours, outside the OT hour limits); `vn.policy.ot_min_hours_day` no longer created | planned | |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §1: depends on `l10n_vn_payroll_account` and `auditlog` | step 1 depends on `l10n_vn_payroll` only; `auditlog` comes with step 2, `l10n_vn_payroll_account` with step 4 | The garment configuration is built before the account module (Peter, 2026-11-07); the account mapping is the only part that needs it |
| 2 | §28: the configuration shipped as module data, accounts set by a `post_init_hook` | created per company by a loader that a payroll manager starts from *Settings* (D1) | Components, scales, parameters, categories, rules and structures belong to one company, and the trading company is Vietnamese too, so an install cannot know which company to configure; the public repo cannot name one (`maintenance_sla_garment` divergence 1). The loader is also how tests configure their own company |
| 3 | §28.1: eight OT components, and `ATT`, `KPI`, `SUPP`, `DUTY`, `PHONE` inactive | the three day OT components and the five night components active; `ATT`, `DUTY`, `PHONE` inactive; no `KPI`, no `SUPP` (D9) | Night pay is statutory, so its components stay active and pay as soon as night hours are recorded. `ATT`, `DUTY` and `PHONE` are options of the module, kept apart from the target policy. `KPI` behaves as `ONE`; `SUPP` is not part of any pay in use (Peter, 2026-11-07) |
| 4 | §4.3: `vn.policy.std_days.mode`, `ot_supplement`, `unit_rate`, `attendance_late_max`, `advance_max_share` | not created (D10) | `std_days.mode` was not built (engine divergence 12); `SUPP` is not shipped; the unit rate is set once IE is live (Pay Policy OPEN-04); the attendance limit and the attendance bonus amount are decided when `ATT` is switched on; the advance limit comes with the advances |
| 5 | §28.1: `ATT` takes its amount from the pay line | from the parameter `vn.policy.attendance_bonus`, not created (D12) | One amount for every worker, changed in one place |
| 6 | §28.2: scale versions from the go-live month | parameters and scale versions from 2026-01-01 (D10) | The go-live month is open (Pay Policy OPEN-16); a version from January covers every month calculated in 2026, the trial months included |
| 7 | §28.2: contract line templates, cost groups and accounts, contribution registers | later steps (3, 4) | Step 1 is the configuration a payslip needs |

## Decisions

| # | Decision |
|---|---|
| D1 | **A loader per company:** `res.company._l10n_vn_garment_load()` configures one company. It refuses a company whose country is not Vietnam (`UserError`, *The garment pay scheme is for Vietnamese companies; %(company)s is not one.*). It first runs the engine's `_l10n_vn_payroll_ensure_parameters()` for the company, so a company created after the last upgrade gets its statutory parameters too |
| D2 | **Existing records are kept as they are:** every record is matched by code (D3) and, when found, left untouched — no field written, no version or cell added. Archived records count as found. The loader only creates |
| D3 | **Matching:** parameter — `code` and `company_id`; scale — `code` and `company_id`; component — `code` and `company_id`; category — `code` and `company_id`, else `code` with no company; structure — `code` and `company_id`; rule — a rule of that structure with the component's code. All searches with `active_test=False` |
| D4 | **Rules:** the structure gets one `l10n_vn_component` rule per shipped component, pointing to the company's component of that code, whether found or created. A rule is created when the structure has none with that code; a rule found is kept, whatever component it points to |
| D5 | **Names in two languages:** names are written in English; when `vi_VN` is active, the Vietnamese name is written through `with_context(lang="vi_VN")` on the records the loader created. Parameter and structure names are English only: `base.time.parameter.name` and `hr.payroll.structure.name` are not translatable, and writing them in `vi_VN` would replace the English |
| D6 | **Who loads:** payroll managers (`payroll.group_payroll_manager`) and the superuser; anyone else gets an `AccessError` (*Only payroll managers can load the garment pay scheme.*). After the check the loader works as superuser |
| D7 | **The result:** `_l10n_vn_garment_load()` returns `{"created": [...], "kept": [...]}`, labels such as `component BASE`, `scale PROD`, `parameter vn.policy.std_days`, `category DED`, `structure VN_GARMENT`, `rule BASE`, in load order. The *Settings* button shows them in a sticky notification |
| D8 | **All or nothing:** the loader runs in the button's transaction; an error rolls back everything it created. It never runs at install, so the install-time rule that seeding is safe to fail does not apply |
| D9 | **Options are inactive components:** `ATT`, `DUTY` and `PHONE` are created with `active = False` and their rules active. Switching one on is unarchiving the component and filling in its values: pay lines, and for `ATT` its parameters. An archived component cannot be chosen on a pay line, so it pays nothing until then |
| D10 | **Dates:** every parameter version and scale version from 2026-01-01 |
| D11 | **Grade amounts** are Pay Policy v0.5 §4.1's placeholders; each person's amount is set at go-live (OPEN-20). G6 has no cell: its amount is on the pay line, overriding the cell (engine D2) |
| D12 | **`ATT`** takes `vn.policy.attendance_bonus` (amount source `parameter`), not prorated, with the attendance condition (engine D38). Neither `vn.policy.attendance_bonus` nor `vn.policy.attendance_late_max` is created: switched on without them, a payslip stops with a `calculation` result naming the parameter |
| D13 | **Probation** applies to every component paid as salary for the job: `BASE`, `PROD`, `PERF`, `DAILY` and `DUTY` (Labor Code Art. 26 on the salary of Art. 90, which includes allowances) |

## Folder structure

```
l10n_vn_payroll_garment/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── garment_scheme.py              # the scheme as constants
│   ├── res_company.py
│   └── res_config_settings.py
├── views/
│   └── res_config_settings_views.xml
├── readme/
│   ├── DESCRIPTION.md
│   └── USAGE.md
└── tests/
    ├── __init__.py
    ├── test_load.py
    └── test_acceptance.py
```

No `security/` folder: the module adds no model.

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Payroll, Garment Scheme` |
| `summary` | `The garment company's current pay scheme as configuration for l10n_vn_payroll` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Human Resources/Payroll` |
| `countries` | `["vn"]` |
| `depends` | `l10n_vn_payroll` |
| `data` | `views/res_config_settings_views.xml` |
| `installable` | `True` |

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import res_company`, `from . import res_config_settings`. `garment_scheme.py` holds no model and is imported by `res_company.py` |
| `tests/__init__.py` | `from . import test_load`, `from . import test_acceptance` |

## The scheme — `models/garment_scheme.py`

Module-level constants, read by the loader in this order: `PARAMETERS`, `SCALES`, `CATEGORIES`,
`COMPONENTS`, `STRUCTURE`. Each record carries its English and Vietnamese name.

### `PARAMETERS`

In the company, `country_id` the company's country, one version from 2026-01-01 (D10).

| Code | Name | Type | Value |
|---|---|---|---|
| `vn.policy.region` | Minimum wage region | string | `IV` |
| `vn.policy.std_days` | Standard days per month | integer | `26` |
| `vn.policy.base_salary` | Base salary | float | `3700000` |
| `vn.policy.probation_rate` | Probation pay rate | float | `0.85` |
| `vn.policy.attainment_cap` | Attainment and score cap | float | `1` |
| `vn.policy.ot_min_hours_day` | Minimum OT hours counted per day | float | `0.8` |
| `vn.policy.constant_months` | Months of unchanged variable pay before a check | integer | `6` |
| `vn.policy.net_change` | Net pay change from last month before a check | float | `0.30` |
| `vn.check.variable_constant.PERF` | Check level: performance pay unchanged | string | `note` |

### `SCALES`

One version from 2026-01-01.

| Code | Name (en / vi) | Kind | Cells: key (grade, step) amount |
|---|---|---|---|
| `PROD` | Productivity levels / Bậc năng suất | `level` | `Entry` 800,000; `S1` 1,300,000; `S2` 1,800,000; `S3` 2,300,000; `S4` 2,800,000 |
| `GRADE` | Grades and steps / Ngạch, bậc lương | `grade_step` | `G1-1` (G1, 1) 5,500,000; `G1-2` 6,000,000; `G1-3` 6,500,000; `G2-1` 7,500,000; `G2-2` 8,000,000; `G2-3` 8,500,000; `G3-1` 9,000,000; `G3-2` 10,000,000; `G3-3` 11,000,000; `G4-1` 13,000,000; `G4-2` 14,000,000; `G4-3` 15,000,000; `G5-1` 16,000,000; `G5-2` 17,000,000; `G5-3` 18,000,000 (D11) |

Each `GRADE` cell's `grade` is the key's part before the dash and `step` the number after it.

### `CATEGORIES`

| Code | Name (en / vi) | For components of kind |
|---|---|---|
| `EARN` | Earnings / Thu nhập | `earning` |
| `DED` | Deductions / Khấu trừ | `deduction` |
| `ER` | Employer contributions / Công ty đóng | `employer` |
| `TOTAL` | Totals / Tổng cộng | `total`, `info` |

### `COMPONENTS`

`sequence` in table order, by 10 (`BASE` 10 … `UNION_FEE` 350). Columns: **SI** `in_si_base`,
**OT** `in_ot_base`, **Prob.** `probation_applies`, **Var.** `variable` with its
`attainment_source`. Fields not shown are empty or False. `company_id` is the loaded company.

**Earnings**

| Code | Name (en / vi) | Nature | Source | SI | OT | PIT | Proration | Prob. | Var. | Section | Other |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `BASE` | Base salary / Lương cơ bản | `job_salary` | `parameter` `vn.policy.base_salary` | ✓ | ✓ | `taxable` | `paid_days` | ✓ | | `salary` | `sets_wage` |
| `PROD` | Productivity pay / Lương năng suất | `variable_salary` | `scale` `PROD` | | ✓ | `taxable` | `paid_days` | ✓ | `supervisor` | `salary` | |
| `PERF` | Performance pay / Lương hiệu quả công việc | `variable_salary` | `scale_remainder` `GRADE` | | ✓ | `taxable` | `paid_days` | ✓ | `manager` | `salary` | |
| `DAILY` | Daily wage / Lương ngày | `job_salary` | `line` | ✓ | ✓ | `taxable` | `per_day` | ✓ | | `salary` | |
| `DUTY` | Responsibility allowance / Phụ cấp trách nhiệm | `fixed_allowance` | `line` | ✓ | ✓ | `taxable` | `paid_days` | ✓ | | `salary` | inactive |
| `OT_WD` | Overtime, workday / Làm thêm giờ ngày thường | `overtime` | `ot` | | | `ot` | | | | `ot` | `ot_category` `WD` |
| `OT_RD` | Overtime, weekly rest day / Làm thêm giờ ngày nghỉ hằng tuần | `overtime` | `ot` | | | `ot` | | | | `ot` | `RD` |
| `OT_HOL` | Overtime, public holiday / Làm thêm giờ ngày lễ, Tết | `overtime` | `ot` | | | `ot` | | | | `ot` | `HOL` |
| `OT_NIGHT` | Night work premium / Phụ cấp làm việc ban đêm | `night` | `ot` | | | `ot` | | | | `ot` | `NIGHT` |
| `OT_NWD` | Night overtime, workday / Làm thêm giờ ban đêm ngày thường | `overtime` | `ot` | | | `ot` | | | | `ot` | `NWD` |
| `OT_NWD_AFTER` | Night overtime, workday after daytime overtime / Làm thêm giờ ban đêm ngày thường sau làm thêm ban ngày | `overtime` | `ot` | | | `ot` | | | | `ot` | `NWD_AFTER` |
| `OT_NRD` | Night overtime, weekly rest day / Làm thêm giờ ban đêm ngày nghỉ hằng tuần | `overtime` | `ot` | | | `ot` | | | | `ot` | `NRD` |
| `OT_NHOL` | Night overtime, public holiday / Làm thêm giờ ban đêm ngày lễ, Tết | `overtime` | `ot` | | | `ot` | | | | `ot` | `NHOL` |
| `ATT` | Attendance bonus / Thưởng chuyên cần | `bonus` | `parameter` `vn.policy.attendance_bonus` | | | `taxable` | `none` | | | `bonus` | `condition` `attendance`; inactive (D12) |
| `EFF` | Efficiency bonus / Thưởng hiệu suất | `bonus` | `entered` | | | `taxable` | | | | `bonus` | |
| `ONE` | One-time bonus / Thưởng đột xuất | `bonus` | `entered` | | | `taxable` | | | | `bonus` | |
| `ANNUAL` | Annual bonus / Thưởng tháng 13 | `bonus` | `entered` | | | `taxable` | | | | `bonus` | |
| `LEAVE` | Untaken leave pay / Tiền lương ngày phép chưa nghỉ | `leave_pay` | `entered` | | | `exempt` | | | | `other` | |
| `PHONE` | Phone allowance / Phụ cấp điện thoại | `welfare` | `line` | | | `exempt` | `none` | | | `other` | inactive |

All earnings have `kind` `earning` and `condition` `none` unless stated.

**Engine components:** `amount_source` `engine`, `engine_code` = the code, no PIT treatment, no proration.

| Code | Name (en / vi) | Kind | Nature | Section |
|---|---|---|---|---|
| `GROSS` | Gross pay / Tổng thu nhập | `total` | `total` | `total` |
| `EE_SI` | Social insurance (employee) / BHXH (người lao động) | `deduction` | `statutory` | `deduction` |
| `EE_HI` | Health insurance (employee) / BHYT (người lao động) | `deduction` | `statutory` | `deduction` |
| `EE_UI` | Unemployment insurance (employee) / BHTN (người lao động) | `deduction` | `statutory` | `deduction` |
| `DUES` | Union dues / Đoàn phí công đoàn | `deduction` | `union` | `deduction` |
| `PIT` | Personal income tax / Thuế TNCN | `deduction` | `statutory` | `deduction` |
| `DAMAGE` | Damage compensation / Bồi thường thiệt hại | `deduction` | `damage` | `deduction` |
| `NET` | Net pay / Thực lĩnh | `total` | `total` | `total` |
| `ADVANCE` | Advance settled / Đã tạm ứng | `info` | `advance` | `total` |
| `TO_PAY` | Amount to pay / Còn được lĩnh | `total` | `total` | `total` |
| `ER_PENSION` | Pension and survivorship (employer) / BHXH hưu trí, tử tuất (công ty) | `employer` | `statutory` | `employer` |
| `ER_SICKNESS` | Sickness and maternity (employer) / BHXH ốm đau, thai sản (công ty) | `employer` | `statutory` | `employer` |
| `ER_ACCIDENT` | Occupational accident (employer) / BHXH tai nạn lao động (công ty) | `employer` | `statutory` | `employer` |
| `ER_HI` | Health insurance (employer) / BHYT (công ty) | `employer` | `statutory` | `employer` |
| `ER_UI` | Unemployment insurance (employer) / BHTN (công ty) | `employer` | `statutory` | `employer` |
| `UNION_FEE` | Union fee / Kinh phí công đoàn | `employer` | `statutory` | `employer` |

35 components: 32 active, 3 inactive.

### `STRUCTURE`

`hr.payroll.structure`: `code` `VN_GARMENT`, name *Vietnamese pay — current scheme* (English only,
D5), `l10n_vn_payroll` True, `parent_id` empty, the loaded company.

Each rule (D4): `name` the component's name (both languages), `code` and `sequence` the
component's, `category_id` the company's category for the component's kind (`CATEGORIES`),
`company_id`, `amount_select` and `condition_select` `l10n_vn_component`,
`l10n_vn_component_id` the component; linked to the structure's `rule_ids`.

## Models

### `res.company` — `models/res_company.py`

`_inherit = "res.company"`.

| Method | Behaviour |
|---|---|
| `_l10n_vn_garment_load()` | `ensure_one`. D6 check (`self.env.su` or the user has `payroll.group_payroll_manager`), then as superuser: D1 country check and `_l10n_vn_payroll_ensure_parameters()`; then each constant in order, matched by D3 and created when missing (D2), Vietnamese names per D5; returns D7's dict |

For each kind the loader creates:

| Kind | Created with |
|---|---|
| parameter | `name`, `code`, `type`, `company_id`, `country_id`, `version_ids` with its one version (`date_from`, `value` as text) |
| scale | `code`, `name`, `kind`, `company_id`, `version_ids` with its one version and its cells (`key`, `grade`, `step`, `amount`) |
| category | `code`, `name`, `company_id` |
| component | the fields of `COMPONENTS`; `scale_id` the company's scale of that code, found or created |
| structure | the fields of `STRUCTURE` |
| rule | the fields of `STRUCTURE`'s rule paragraph; `category_id` found or created |

### `res.config.settings` — `models/res_config_settings.py`

`_inherit = "res.config.settings"`.

| Method | Behaviour |
|---|---|
| `action_l10n_vn_garment_load()` | `result = self.company_id._l10n_vn_garment_load()`; returns an `ir.actions.client` `display_notification`, `type` `success`, `sticky` True, title *Garment pay scheme loaded*, message *%(company)s: created %(created_count)s (%(created)s); kept as they were %(kept_count)s (%(kept)s).* with the labels comma-separated, *none* for an empty list |

## Views — `views/res_config_settings_views.xml`

| XML id | Inherits | Change |
|---|---|---|
| `res_config_settings_view_form` | `payroll.res_config_settings_view_form` | inside `//app[@name='payroll']`, a `block` titled *Vietnamese Payroll* (`id` `l10n_vn_payroll_garment`) with a `setting` *Garment pay scheme*, help *Creates the current scheme's parameters, scales, components, structure and rules in this company. Records whose code already exists are kept as they are.*, holding a `button` `action_l10n_vn_garment_load`, `type="object"`, string *Load Garment Pay Scheme*, `class="btn-link"`, `icon="oi-arrow-right"` |

OCA's *Payroll* app block is already limited to `payroll.group_payroll_manager`.

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | What the scheme holds: workers on base salary + productivity pay by level × attainment; other roles on base salary + performance pay (grade and step amount − base) × score; daily wage; OT and night components; entered bonuses and untaken-leave pay; the options `ATT`, `DUTY`, `PHONE`, inactive; the parameters and the `PERF` check level |
| `readme/USAGE.md` | *Settings → Payroll → Load Garment Pay Scheme* in the company to configure; what *kept* means; grade amounts are placeholders to set per person; switching an option on: unarchive the component, then its pay lines, and for `ATT` the parameters `vn.policy.attendance_bonus` and `vn.policy.attendance_late_max`; contracts move to the structure *VN_GARMENT* at go-live |

## Change to `l10n_vn_payroll` tests

Test files only; no version change. Engine test count stays 224.

| File | Change |
|---|---|
| `tests/payslip_common.py` | `PayslipCase.setUpClass` keeps `super()`, `_l10n_vn_payroll_ensure_parameters()`, `cls.contract.struct_id = cls.structure` and the period. Everything between — the policy parameters, scales, components, categories, structure and rules — moves unchanged into a new classmethod `_l10n_vn_configure()`, which `setUpClass` calls. It sets the attributes the tests read: `base`, `prod`, `perf`, `sal`, `skill`, `daily`, `att`, `travel`, `inc`, `eff`, `one`, `ot_wd`, `ot_rd`, `ot_hol`, `supp`, `gross`, `kpi`, `annual`, `leave`, `phone`, `meal`, `engine`, `structure` and the categories |
| `tests/group_g.py` (new) | `GroupGCases`, a plain class (not a `TestCase`): the constants `WORKER` and `STAFF`, the helpers `_worker`, `_staff`, `_run`, `_supervised`, `_managed`, and `test_g01` … `test_g15` (no `test_g09`), moved unchanged from `test_acceptance.py` |
| `tests/test_acceptance.py` | `class TestAcceptance(GroupGCases, PayslipCase)` with `allow_inherited_tests_method = True` (`odoo/odoo/tests/loader.py:31`); keeps groups A–E and the helpers only they use (`_skilled_lines`, `_office`, `_row`); imports `WORKER`, `STAFF` from `group_g` where the groups A–E use them |

## Tests

Both classes are `@tagged("post_install", "-at_install")`: their fixtures create a company,
employees and users. They import the engine's fixtures:
`odoo.addons.l10n_vn_payroll.tests.common.PayrollCase` and `.payslip_common.PayslipCase`, and
`.group_g.GroupGCases`. No import from a core `tests` package.

### `tests/test_load.py` — `TestLoad(PayrollCase)`

The engine fixture's company (Vietnam, VND) is loaded in each test that needs it.

| Test | Asserts |
|---|---|
| `test_load_creates` | after one load: the 9 parameters read through `_strict_get` on 2026-10-31 give `IV`, 26, 3,700,000, 0.85, 1, 0.8, 6, 0.30, `note`; scale `PROD` has 5 cells and `GRADE` 15, `G2-2` = 8,000,000 with grade `G2`, step 2; 35 components, the inactive ones exactly `ATT`, `DUTY`, `PHONE`; the structure `VN_GARMENT` has `l10n_vn_payroll` and 35 rules, each with the code and component of one component and the category of its kind; `created` lists every record, `kept` is empty |
| `test_component_settings` | `BASE`: source `parameter` `vn.policy.base_salary`, in SI and OT base, `sets_wage`; `PROD`: scale `PROD`, variable, `supervisor`, OT base only; `PERF`: `scale_remainder` on `GRADE`, `manager`; `LEAVE`: `exempt`; `ATT`: inactive, `parameter` `vn.policy.attendance_bonus`, condition `attendance`; `OT_NWD_AFTER`: category `NWD_AFTER`, PIT `ot` |
| `test_vietnamese_names` | with `vi_VN` activated before the load: `BASE` reads *Lương cơ bản* in `vi_VN` and *Base salary* in `en_US`; the structure's rule `BASE` the same |
| `test_load_again` | a second load creates nothing, `kept` lists all 9 + 2 + 4 + 35 + 1 + 35 records, counts unchanged |
| `test_existing_kept` | before the load: a component `BASE` named *Trial base* in section `other`, a parameter `vn.policy.std_days` with one version 2026-05-01 = 24, a scale `PROD` with one version holding `Entry` only. After: all three unchanged (name, section, versions, cells), each listed in `kept`; the structure's rule `BASE` points to the existing `BASE` |
| `test_category_shared` | a category `DED` with no company exists: the loader reuses it for the deduction rules and creates no `DED` in the company |
| `test_not_vietnamese` | a company with country France: `UserError`, and no component exists in it |
| `test_access` | a payroll officer (`payroll.group_payroll_user`) gets `AccessError`; a payroll manager in the same company loads it (positive control). Both through `_as(user)` |
| `test_settings_button` | `res.config.settings` of the company: `action_l10n_vn_garment_load()` returns a `display_notification` whose message names the company and *created 86* (9 parameters, 2 scales, 4 categories, 35 components, 1 structure, 35 rules) |

### `tests/test_acceptance.py` — `TestGarmentAcceptance(GroupGCases, PayslipCase)`

`allow_inherited_tests_method = True`. `_l10n_vn_configure()` is overridden: it calls
`cls.company._l10n_vn_garment_load()` and sets `base`, `prod`, `perf`, `eff`, `one`, `ot_wd`,
`ot_rd`, `ot_hol`, `gross` and `engine` (the 15 engine components by code) to the loaded
components, and `structure` to `VN_GARMENT`. `_code(code)` returns `code` unprefixed. The
expected figures come from the engine's `tests/data/acceptance_cases.json`.

| Test | Asserts |
|---|---|
| `test_g01` … `test_g15` (14, from `GroupGCases`) | group G of the acceptance cases on the loaded configuration: every earning line, gross, insurance, PIT, damage, net, employer funds and to pay, as in the engine |
| `test_night_components` | an Entry worker at attainment 1, input `ot_hours_json` `{"NIGHT": 8, "NWD": 2}`: `OT_NIGHT` = round(4,500,000 ÷ 208 × 0.3 × 8) = 51,923, `OT_NWD` = round(4,500,000 ÷ 208 × 2.0 × 2) = 86,538 |
| `test_option_switched_on` | `DUTY` unarchived, a worker's contract with a `DUTY` line of 500,000 for the whole month: a `DUTY` line of 500,000, and the SI base in the snapshot is 4,200,000 |

**Expected count:** 9 + 16 = 25 tests.
