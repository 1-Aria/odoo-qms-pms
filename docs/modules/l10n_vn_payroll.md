# l10n_vn_payroll

Vietnamese payroll on OCA `payroll`: pay components with their SI, OT and PIT treatment, salary and
productivity scales, dated pay lines on contracts, contribution profiles, monthly inputs, the pay
context that calculates every payslip, checks, the run workflow and lock, the payslip and the
statutory statements. Design: `docs/HR-Contract-Payroll/Payroll Technical Design v0.3.md` (PTD-xx),
on `Payroll Requirements Specification v0.5.md` (FR-xx) and `Pay Policy v0.5.md`. Base module:
`docs/modules/base_time_parameter_strict.md`. Posting, the bank file and advances are
`l10n_vn_payroll_account`; the garment company's configuration is `l10n_vn_payroll_garment`.

## Steps

| # | Scope | Status | Result |
|---|---|---|---|
| 1 | Components, scales, contract pay lines and the wage they set; payroll groups, the officer record rule, the new-user template, the parameter group for payroll managers; statutory parameters per Vietnamese company; configuration views and menus | done | 2026-11-02, two runs. First: `-i` installed; 32 tests, 29 passed, 3 errors in `test_security`, all *Access to unauthorized or invalid companies*: the fixtures' environment allows the superuser's companies, and `with_user` kept them for test users who belong to the test company only; fixed with `_as(user)`. Second: `-u`, `exit=0`, 32 tests, 0 failures; UI checked by Peter: the configuration menus, the statutory parameters of both companies, the *Pay Lines* page, a component refused with its missing setting, the new-user template without payroll roles |
| 2 | Participant types; contract fields (participant type, declared SI base, probation form) and the PIT method; employee fields; dependents on `hr_employee_relative`, with officers' write access to relatives | done | 2026-11-02, one run: `-i hr_employee_relative`, then `-u l10n_vn_payroll`, `exit=0`, 51 tests, 0 failures; UI checked by Peter: participant types, the declared SI base shown and required for a manager, the attendance mode following the pay group, a dependent refused on a date other than the 1st, no *Payroll* tab or PIT columns for an HR user without a payroll role |
| 3 | Periods; the monthly summary per employee built from core attendance, leave and calendars, with segments, paid breaks for women and the 0.8 h daily OT minimum; entered lines with approval; leave types paid by SI; the nursing break on the employee; attendance close | done | 2026-11-02, one run: `-u`, `exit=0`, 70 tests, 0 failures; UI checked by Peter: summaries built, *Close Attendance* blocking edits to figures while attainment stays editable |
| 3.1 | Zero figures stored as 0, not NULL: `_l10n_vn_build` drops the cached figures before writing them (D29); `test_zero_figures_stored` | done | 2026-11-02: found in the May 2026 summaries of the test copy, 53 of 287 with `days_worked` NULL. One run: `-u`, `exit=0`, 71 tests, 0 failures; May reopened and rebuilt by Peter |
| 4 | Calculation I: Vietnamese structures; the payslip's main contract, closed contracts included, rules run once; worked days from the monthly summary; the month's pieces, cut also at a probation clause's end; the pay context: pay line components with proration, probation rate, attainment and the attendance condition, entered, adjustment and IE lines, OT on the OT base, gross; the `l10n_vn_component` rule type with exact lines, one payslip line per context line; the snapshot; tests on the earnings of 19 acceptance cases | done | 2026-11-03, two runs. First: `-u`, 114 tests, 3 errors (C02, D07, G08): step 1's pay line check refused a line without `date_to` on a contract with an end date; fixed to read an empty `date_to` as the contract's end, with `test_open_line_on_ended_contract`. Second: `-u`, `exit=0`, 115 tests, 0 failures; UI checked by Peter: the structure flag, the rule's component, the payslip line columns. Trial on the test copy by hand: employee 441, May 2026, payslip 1819 = BASE 3,628,846, PROD 784,615, OT_WD 685,278, OT_RD 695,194, GROSS 5,793,933, as computed beforehand |
| 5 | Calculation II: the month's scheduled days on the summary; SI liability by the 14-day rule; the SI base, floor and caps; employee and employer insurance by fund, union fee and dues; PIT, progressive with exemptions and flat; damage decisions with their allocations; net pay; the advance hook for `l10n_vn_payroll_account` with `ADVANCE` and `TO_PAY`; deductions shown negative; tests on the whole payslip of 42 acceptance cases | done | 2026-11-03, two runs. First: `-u`, 160 tests, 1 failure: `test_month_scheduled_days_built` assumed the test company works Monday–Friday, but a new company copies the current company's calendar (Monday–Saturday on the instance); the test now has its own calendar. Second: `-u`, `exit=0`, 160 tests, 0 failures; UI checked by Peter: *Damage Decisions*, *Scheduled days in the month* on the input; May 2026 summaries rebuilt (287, each 26 days in the month). Trial on the test copy (`payroll-trial/`), May 2026, employees 441, 391, 378: payslips 1996–1998, SI base 3,700,000, insurance 296,000 + 55,500 + 37,000, employer 518,000 + 111,000 + 18,500 + 111,000 + 37,000 + union fee 74,000, PIT 0; net 5,405,433, 4,071,292, 3,897,324, each checked by hand |
| 6 | Checks: catalogue, levels from parameters, results | planned | |
| 7 | Runs: states, segregation, the lock, corrections, off-cycle runs; payslip access for approvers and readers | planned | |
| 8 | The bilingual payslip report | planned | |
| 9 | Statutory statements and opening data | planned | |

## Divergences from the design

| # | Design | This module | Reason |
|---|---|---|---|
| 1 | §1, §4.2: statutory parameters ship with no company | created for every company whose country is Vietnam, and kept up to date at every install and upgrade (D9) | OCA's global rule on parameters, `[('company_id', 'in', company_ids)]` (`oca/server-tools/base_time_parameter/security/security.xml:6-13`), matches no parameter without a company, so they would show on no screen (`base_time_parameter_strict` divergence 1) |
| 2 | §3.2: officers, reviewers and readers read parameters | only payroll managers see parameters, through OCA's *Manage Time Parameters* group, which their group now implies (D7) | The calculation reads parameters as superuser (`base_time_parameter_strict` D1), so other roles need no access; the design's convention of not granting another module's models through `ir.model.access` rows is kept |
| 3 | §7: `wage` follows "the base salary line" | follows the lines whose component has `sets_wage` (D5) | The design names no field that marks the base salary component |
| 4 | §3.2: approver and reader read payslips | in step 7, with the run workflow | Their access is tested where they use it, approving and reading runs |
| 5 | §8.1: participant types without a word on companies | one list for all companies, no `company_id` (step 2, D12) | They describe the law's participant categories, which are the same for every Vietnamese company |
| 6 | §8.3: the region defaults from `vn.policy.region` | the same, and left empty when the company has no such parameter (step 2, D15) | The parameter ships with the garment module; before it, a guessed region would be wrong for a company in another region |
| 7 | §10.4: attendance totals imported from Excel until the attendance module exists | built from core's `hr.attendance`, approved leave and the contracts' working calendars (step 3, D20) | Peter, 2026-11-02: the fingerprint → pandas → `hr.attendance` pipeline, with early check-ins trimmed and the calendar's breaks, already gives the right time; payroll reads it rather than a second file. The Attendance Specification's own engine is not needed for payroll v1 |
| 8 | §10.2: segments entered by hand when terms change | computed by the summary from the daily figures (step 3, D24) | The summary works day by day, so it can cut the month at contract and pay line dates itself |
| 9 | §10.4: supervisors and managers enter attainment and scores in their own lists | the payroll officer enters them in an editable list (step 3, D27) | A role for supervisors needs record rules per department and field-level write limits; it waits until the officer's list proves too slow |
| 10 | §10.1: late arrivals from attendance | not computed; the field stays for the attendance bonus, inactive in the current scheme (step 3) | Core has no notion of lateness, and nothing in the current scheme uses it |
| 11 | §14: night hours | not computed (step 3) | No work after 22:00, none planned (Peter, 2026-11-02); the night components and factors stay available |
| 12 | §12 step 3: standard days from `vn.policy.std_days.mode` and `vn.policy.std_days` | `vn.policy.std_days` only (step 4, D36) | The current scheme is fixed at 26 (Pay Policy); the variant from the month's schedule has no case yet (TC-B07) and comes with it |
| 13 | §13.1: a `none` line computed per segment | paid once a month, from the last piece in which the component has a pay line (step 4, D36) | Computed per segment, a fixed amount is paid twice in a split month |
| 14 | §13.1: one payslip line per pay line per segment; §17.1: one rule per component | both: after OCA files the rule's line, it is split into one payslip line per context line (step 4, D43) | OCA files one line per rule and contract (`oca/payroll/payroll/models/hr_payslip.py:524`), so a rule alone cannot show a probation split (TC-C02, TC-C06) |
| 15 | §11: the payslip overrides apply to every payslip | only to payslips whose structure has `l10n_vn_payroll` (step 4, D30) | The instance's own structures (`MINW`, `BNOT` …) run in the same company until go-live (§29 step 7); their contract choice and `WORK100` worked days must not change |
| 16 | §10.2: segments cut at contract and pay line dates | also the day after a probation clause ends (step 4, D33) | §12 step 2 needs each segment to know whether it is in probation, and a clause ends inside a contract |
| 17 | §15.1: no contribution when `si_absence_days` ≥ 14, and a separate rule for a contract starting mid-month | one rule: the month's scheduled days less the paid days under contracts with SI funds; contributions when that is under `vn.si.absence_days` (step 5, D47) | `si_absence_days` counts only days of employment, so a leaver who worked 10 days would contribute (TC-OPEN-12 says not); one count covers hires, leavers and probation contracts (Peter, 2026-11-03) |
| 18 | §15.2: the SI base from the lines in force at the month's end | on the main contract's last day in the month (step 5, D49) | A leaver's contract has no line in force at the month's end (Peter, 2026-11-03) |
| 19 | §15.2: the SI base from the lines at full amount | a `per_day` line counts at its daily rate × `vn.policy.std_days` (step 5, D49) | TC-OPEN-8's assumption; the company pays no one daily today, so the rule is untested in use (Peter, 2026-11-03) |
| 20 | §16.1: `exempt_cap` lines up to their cap | the cap applies once per cap parameter, over all the lines that name it (step 5, D54) | A meal allowance and its correction share one monthly cap (Peter, 2026-11-03) |
| 21 | §16.2: `deducted` = the sum of `DAMAGE` lines on done payslips | allocation records per decision and payslip (step 5, D55) | A payslip's one `DAMAGE` line cannot say how much it took from each of several decisions |
| 22 | §12: the sign of deduction lines unstated | deductions negative, employer contributions positive (step 5, D51) | The test cases show deductions with a minus, and OCA's categories then add up to net pay |

## Decisions

| # | Decision |
|---|---|
| D1 | **Naming** (PTD-01): models `l10n_vn.payroll.*`, fields on core and OCA models `l10n_vn_*`, parameter codes `vn.*` |
| D2 | **A component's amount source decides what its pay lines hold** (PTD-04): `line` → `amount`; `parameter` → the parameter `amount_parameter` on the date; `scale` → the cell `scale_key` of the version in force, unless the line has an `amount`; `scale_remainder` → that cell (or `amount`) minus the line amounts flagged `in_cell` on the same contract on the date. Components with source `entered`, `ie_units`, `ot` or `engine` never sit on a contract |
| D3 | **Configuration rules are checked when a component is saved** (design §5.3), so a run never meets a half-configured component. The checks are one `@api.constrains` on the required fields `kind` and `amount_source` among others, so they also run at creation |
| D4 | **A line's amount on a date is one method,** `_l10n_vn_amount_on(date)`, used by the wage and later by the pay context |
| D5 | **`wage` = the sum of the lines in force today whose component has `sets_wage`,** written after every change to a contract's lines. When an amount cannot be read (a parameter not configured yet), `wage` is left as it is and the reason is logged: setting up lines never fails because of `wage`. Payroll never reads `wage` |
| D6 | **Pay lines do not overlap:** two lines of one component on one contract cannot share a day, and two `scale_remainder` lines of one scale cannot either. A change is a new line, the old one ended the day before (design §7) |
| D7 | **Groups** (design §3.1): reviewer (implies officer), approver and reader (each implies internal user), in OCA's *Payroll* category. `payroll.group_payroll_manager` gains `base_time_parameter.group_time_parameter` |
| D8 | **New users get no payroll group** (PFG-10): `base.default_user` loses `payroll.group_payroll_user` and `payroll.group_payroll_manager`, in a `noupdate` record. Odoo's template also carries every app's top groups (on the instance: HR, contracts, accounting, stock, purchase and more); those stay as they are |
| D9 | **Statutory parameters per Vietnamese company:** the table `STATUTORY_PARAMETERS` in `models/res_company.py` holds each code, name, type and dated versions. `res.company._l10n_vn_payroll_ensure_parameters()` creates, for every company with country `VN`, each missing parameter and each missing version (by `date_from`); it never changes an existing version, so edits made in the UI stay. A data `<function>` runs it at every install and upgrade, so a new company or a new statutory version arrives with the next upgrade. Each company is processed in a savepoint; a failure is logged and the install continues (safe to fail) |
| D10 | **Officers see every payslip of their companies:** a rule for `payroll.group_payroll_user` with domain `[(1, '=', 1)]` on `hr.payslip`. Rules of a user's groups combine with OR, so OCA's narrower officer rule (`oca/payroll/payroll/security/hr_payroll_security.xml:28-36`) no longer limits them; OCA's global company rule still applies |
| D11 | **Pay lines are visible only to payroll groups:** `l10n_vn_line_ids` on the contract carries `groups="payroll.group_payroll_user"`, and the page that shows it the same |
| D12 | **Participant types are statutory data shared by all companies** (step 2): four records in a `noupdate` data file — `LABOUR`, `PROBATION`, `MANAGER`, `SHORT` (design §8.1) — editable by payroll managers, kept on upgrade |
| D13 | **A new contract is a labour contract by default** (step 2): `l10n_vn_participant_type_id` defaults to `LABOUR`. Existing contracts are left empty; setting them is go-live work (design §29 step 4) |
| D14 | **Every pay field on the employee, the contract and the relative carries `groups="payroll.group_payroll_user"`** (step 2, design §2), so other users neither see nor export them. Checks that read them run as superuser, since an HR user editing a contract's dates must not be refused because of a field they cannot see |
| D15 | **The employee's region defaults from the parameter `vn.policy.region` of the employee's company** on its creation date (step 2); with no such parameter it stays empty |
| D16 | **The attendance mode follows the pay group** (step 2): a stored compute, editable, set to `scan` for workers, production support and daily-paid workers and `exception` for office and managers (Attendance Specification §5) |
| D17 | **A dependent counts in a month** when it is a PIT dependent, its `l10n_vn_from` is on or before the month's first day, and its `l10n_vn_to` is empty or on or after it (step 2). Both dates are first days of months, as dependents are registered by month (FR-06) |
| D18 | **Payroll officers write relatives** (step 2): OCA lets every internal user read them and only HR managers write them (`oca/hr/hr_employee_relative/security/ir.model.access.csv`); registering dependents is the payroll officer's work (FR-06), so the officer group gets full access to `hr.employee.relative` |
| D20 | **The monthly summary reads core's time, it does not compute its own** (step 3): worked hours, overtime and validated overtime of `hr.attendance`; the working calendar of the contract in force each day; approved leave and public holidays through `list_leaves`. The only payroll rules applied on top are the daily OT minimum (D22), the paid breaks (D25) and the classification of leave (D21) |
| D21 | **Leave is classified by its type:** a public holiday (a calendar leave with no employee) and a leave type that is neither `unpaid` (core, `hr_holidays/models/hr_leave_type.py:102`) nor `l10n_vn_si_paid` are paid by the company; `l10n_vn_si_paid` types (sick leave, maternity) are paid by the SI fund; `unpaid` types are unpaid |
| D22 | **OT counts per day, from a minimum** `vn.policy.ot_min_hours_day` (garment: 0.8): a day's validated overtime below it is dropped, above it counts in full. The day's category: `HOL` when a public holiday covers it, `RD` when the calendar schedules no hours that day, else `WD`. No rounding (Peter, 2026-11-02). The parameter ships with `l10n_vn_payroll_garment`; without it, building stops with the strict reader's error naming it |
| D23 | **A day is measured against the calendar's hours for that day,** not `hours_per_day`: days worked on a scheduled day = min(1, (worked − overtime) ÷ scheduled hours). On the instance *8 Hours 2 Shifts* has `hours_per_day` 16, which today's rule `MINW` caps by falling back to 8 |
| D24 | **Segments are computed:** the month is cut at every start and end of a contract and of a pay line of the employee inside the month; with more than one piece, each gets its own days and OT (design §10.2) |
| D25 | **Paid breaks restore time, they add none** (Attendance Spec §5.3): on a day worked, the shortfall = scheduled − (worked − overtime) − leave hours, at least 0. A nursing break credits min(1 h, shortfall) when the employee has `l10n_vn_nursing_break` and a child relative whose first birthday is after that day; then `menstruation_days` × 0.5 h is spread over the month's remaining shortfalls in date order. Credits count as paid time |
| D26 | **A summary can be corrected by hand:** `figures_locked` keeps the computed figures from being rebuilt. Closing attendance freezes the computed figures; attainment, IE units, menstruation days and entered lines stay editable until the run (step 7) |
| D27 | **The officer enters attainment and scores** (divergence 9), with the source and, for an override, a note |
| D28 | **An entered line is paid only once approved** (FR-69): *Approve* is for `group_payroll_approver`; changing the component, amount or hours of an approved line clears its approval |
| D29 | **Figures are written over a dropped cache** (step 3.1): a summary is created empty and figured afterwards; a figure never written is cached as 0.0 while its column is NULL, and the ORM skips writing 0.0 over that cache (`CLAUDE.md`, ORM lessons). `_l10n_vn_build` invalidates the figures it is about to write |
| D19 | **The PIT method of a contract on a date** (design §8.2), `hr.contract._l10n_vn_pit_method(date)` (step 2): the employee not resident → `flat_nonresident`; else the participant type's method when it is not `progressive`; else, for a contract with an end date running under 3 months and no commitment form for that year, `flat_short`; else `progressive` |
| D30 | **Vietnamese structures** (step 4, divergence 15): `hr.payroll.structure.l10n_vn_payroll` marks a structure calculated by the pay context. Every step 4 override acts only on payslips whose `struct_id` has it; before a payslip exists (`get_payslip_vals`, worked days), the main contract's `struct_id` decides, or the structure passed in |
| D31 | **Period contracts and the main contract** (design §11): `hr.employee._l10n_vn_period_contracts(date_from, date_to)` returns the employee's contracts in state `open` or `close` overlapping the dates, ordered by `date_start`; the main contract is the last. It becomes the payslip's `contract_id` and the rules run once, against it. The summary (step 3) and the pay context use the same method |
| D32 | **A Vietnamese payslip covers one calendar month** and reads the monthly summary of its company's period for that month. A payslip on other dates, or without a summary, is refused at calculation |
| D33 | **Pieces of the month** (amends D24): `l10n_vn.payroll.input._l10n_vn_pieces()` cuts each period contract's span inside the month at its pay lines' `date_from` and `date_to` + 1 day, and, for a contract with `l10n_vn_probation_form = clause`, at `trial_date_end` + 1 day. A piece is in probation when its contract's form is `contract`, or `clause` with the piece ending on or before `trial_date_end`. Days between two contracts belong to no piece. The summary's segments and the pay context both come from it |
| D34 | **Segments must match the pieces:** with one piece, the pay context uses the summary's month figures and ignores segments; with more, it needs one segment per piece with the same dates, and otherwise stops, naming the dates. Rebuilding the summary creates them; a summary corrected by hand needs them entered |
| D35 | **A piece reads its values on its last day:** the pay lines in force, their amounts (`_l10n_vn_amount_on`), and dated parameters. Month-level parameters (`vn.policy.std_days`, the attainment cap, the unit rate, the attendance limit) are read on the month's last day |
| D36 | **Pay line components** (design §13.1, divergences 12 and 13), per piece and per pay line in force, with *A* the amount, *d* the piece's days on the component's basis, *s* `vn.policy.std_days`, *r* `vn.policy.probation_rate` when the piece is in probation and the component has `probation_applies` (else 1), *a* the attainment when the component is `variable` (else 1): `paid_days` and `days_worked` → round(*A* × *d* ÷ *s* × *r* × *a*); `per_day` → round(*A* × paid days × *r* × *a*); `none` → round(*A* × *r* × *a*), once a month, from the last piece in which the component has a pay line. Arithmetic in `Decimal` built from `str()` of the stored values, in that order, rounded once per line to whole dong, half up (FR-34, TC-R1) |
| D37 | **Attainment** (design §12 step 4): needed only when a `variable` component has a pay line in force. It is missing when the summary's `attainment_source` is empty, so 0 with a source pays 0. Applied as min(`attainment`, `vn.policy.attainment_cap`). The component's `attainment_source` is not compared with the summary's |
| D38 | **The attendance condition** (design §13.3): a component with `condition = attendance` pays its line as computed when the summary has no unexcused absence and `late_arrivals` ≤ `vn.policy.attendance_late_max`, else 0; the line stays, at 0 |
| D39 | **Entered, adjustment and IE lines** (design §13.2): one line per approved input line, on its component, with its amount rounded; an adjustment (`period_ref` set) also carries its `hours` and `period_ref`. Input lines without an approver are left out and listed in the snapshot's `unapproved` for step 6. Each active `ie_units` component gets one line, round(`ie_units` × `vn.policy.unit_rate`), when `ie_units` is not 0 |
| D40 | **OT** (design §14): per piece, OT base = the sum over the pay lines in force whose component is `in_ot_base` of *A* × *r* × *a*, not prorated (`per_day`: *A* × *s* × *r* × *a*, so the hourly rate is the daily rate ÷ 8); hourly = OT base ÷ (*s* × 8). For each active `ot` component of category *c* with hours in the piece: round(hourly × factor *c* × hours *c*), factors from `vn.ot.factors`; a component with `ot_category = all` adds round(its `amount_parameter` × Σ factor *c* × hours *c*). Hours come from each segment; when there are segments and none carries hours, all of the month's hours go to the last piece (PTD-OPEN-04). Hours in a category with no active `ot` component stop the calculation, naming the category |
| D41 | **Gross** (design §12 step 7): each active component with `engine_code = GROSS` gets one line, the sum of the earning lines. The other engine codes come in step 5 |
| D42 | **The context is built at calculation, in bulk** (design §12, §18): `compute_sheet` first prepares the Vietnamese payslips: the summaries of all of them in one search, parameters read once per code, date and company, everything read as superuser. Each payslip gets its main contract as `contract_id`, its summary as `l10n_vn_input_id`, worked days rewritten from the summary, and the whole context as `l10n_vn_context`, which a recalculation replaces. `get_payroll_dict` exposes it to rules as `payroll.vn` |
| D43 | **Exact lines** (design §17, PTD-10, divergence 14): an `l10n_vn_component` rule's line is filed by OCA with the sum of the component's context lines, so `localdict` and the categories hold that sum; `_get_lines_dict` then splits it into one payslip line per context line, each with quantity 1, rate 100, the rounded amount and the display fields. On a Vietnamese payslip, a rule of another type is filed with quantity 1, rate 100 and amount = its total rounded half up, so categories sum whole dong (PFG-06) |
| D44 | **Integrity stops are errors in step 4:** no main contract, no summary, missing segments, missing attainment, OT hours without a component, and a component with context lines but no rule in the payslip's structure raise a `UserError` naming the employee. Step 6 turns them into check results |
| D45 | **Line names:** a pay line or OT line takes the component's name, followed, when the month has more than one piece and the line belongs to one (not a `none` line), by the piece's dates (`dd/mm–dd/mm`) and, in probation, `probation` — `Base salary (01/10–07/10, probation)`; a whole month in probation reads `Base salary (probation)`. An entered line takes its `description`, else the component's name; an adjustment adds its month (`MM/YYYY`) in parentheses |
| D46 | **The month's scheduled days** (step 5): the summary's `month_scheduled_days` counts the dates of the whole month with scheduled hours in the main contract's calendar, public holidays included, as `scheduled_days` counts them inside the contracts. It is a figure of the summary (`FIGURES`), frozen at close and editable on a summary corrected by hand |
| D47 | **SI liability, the 14-day rule** (FR-23, divergence 17): a piece is *liable* when its contract's participant type has any of the pension, sickness, accident, HI or UI funds. Days without SI = `month_scheduled_days` − the paid days of the liable pieces. The month's contributions (employee, employer, union fee, dues) are calculated when that is below `vn.si.absence_days`; otherwise there are none. With no liable piece there are none |
| D48 | **Funds** come from the main contract's participant type: employee SI and employer pension with `fund_pension`, employer sickness with `fund_sickness`, employer accident with `fund_accident`, employee and employer HI with `fund_hi`, employee and employer UI with `fund_ui`, the union fee with `fund_union_fee`; dues when the type has `dues_allowed` and the employee `l10n_vn_union_member` |
| D49 | **The SI base** (design §15.2, divergences 18 and 19), read on the main contract's last piece's last day: base source `components` → the sum of that piece's pay lines (D35) whose component is `in_si_base`, at their amount (`per_day`: × *s*), with no attainment and no probation rate; `declared` → the contract's `l10n_vn_declared_si_base`. Floor: `min_wage` → `vn.min_wage.month` of the employee's region; `reference_level` → `vn.si.reference_level`; `none` → none. Base = max(sum, floor) |
| D50 | **Caps and lines** (design §15.3–4): *S* = min(base, `vn.si.cap_multiple` × `vn.si.reference_level`); *U* = min(base, `vn.ui.cap_multiple` × the region's `vn.min_wage.month`). Each line is round(rate × *S*), UI lines round(rate × *U*), rates `vn.rate.ee.*`, `vn.rate.er.*`, `vn.rate.union_fee`; dues = min(round(`vn.rate.union_dues` × *S*), `vn.union_dues.cap`). Parameters are read on the same day as the base. A line shows its rate as `factor` and its capped base as `unit_amount` |
| D51 | **Signs** (divergence 22): context lines of kind `deduction` are negative, employer lines positive. An entered line on a deduction component is entered as a positive amount (an amount to deduct) and becomes negative in the context; a negative entry gives back. The figures the context sums (insurance, dues, PIT, damage) are kept positive |
| D52 | **More integrity stops** (D44): a period contract without a participant type; an employee without a region when the floor is `min_wage` or UI applies; a summary whose `month_scheduled_days` is 0 (built before step 5: rebuild it). Each raises a `UserError` naming the employee |
| D53 | **The PIT method** is the main contract's `_l10n_vn_pit_method` on the month's last day (D19); a month mixing a probation contract and a labour contract is taxed by the labour contract's method (TC-OPEN-10) |
| D54 | **Progressive PIT** (design §16.1, divergence 20): *E*, the exempt amount = the earning lines with `pit_treatment` `exempt` or `excluded`; plus, per cap parameter, min(the sum of the earning lines with `exempt_cap` naming it, the parameter on the month's last day); plus the OT exemption: the month's own lines with `pit_treatment` `ot` (not adjustments), sum *P*, hours *H* = the summary's `ot_hours`, allowed = max(0, min(`vn.ot.limit.month`, `vn.ot.limit.year` − `ot_hours_ytd`)), exempt round(*P* × min(1, allowed ÷ *H*)); and per OT adjustment with hours *h*, its month's summary giving *H'* and its year-to-date, allowed' = max(0, min(month limit − *H'*, year limit − year-to-date − *H'*)), exempt round(amount × min(1, allowed' ÷ *h*)) — a month without a summary counts 0 hours; an OT adjustment without hours is taxable. *T* = gross − *E* − employee insurance − `vn.pit.self` − dependents (`_l10n_vn_dependent_count` on the month's last day) × `vn.pit.dependent`. PIT = round(the bracket sum of `vn.pit.brackets` on *T*), 0 when *T* ≤ 0. *T* is kept as computed, negative included |
| D55 | **Flat PIT:** `flat_short` → round(`vn.pit.flat_short` × gross) when gross ≥ `vn.pit.flat_short_threshold`, else 0 (TC-OPEN-3); `flat_nonresident` → round(`vn.pit.nonresident` × gross). *E* and *T* are not computed |
| D56 | **Damage compensation** (design §16.2, FR-31, divergence 21): decisions are `l10n_vn.payroll.damage` records; what a payslip takes from each is an `l10n_vn.payroll.damage.allocation`. Available per decision = its amount − its allocations on other payslips not cancelled. Deduction = round(min(the sum available over the employee's decisions dated on or before the month's last day, `vn.damage.cap` × (gross − employee insurance − PIT))), at least 0, allocated to decisions by date, oldest first. The payslip's allocations are rewritten at each calculation; a decision's `deducted` counts done payslips only |
| D57 | **Net and advances** (FR-32, FR-71): net = gross − employee insurance − dues − PIT − damage − the entered deduction lines (D51). `hr.payslip._l10n_vn_advances()` returns the advances to settle, oldest first, as `{id, amount}` with the open amount; this module returns none and `l10n_vn_payroll_account` overrides it. Settled = min(their sum, max(net, 0)), allocated oldest first; `ADVANCE` = −settled when not 0; `TO_PAY` = net − settled |
| D58 | **Engine lines** come from active components of the payslip's company with that `engine_code`, after `GROSS` in this order: `EE_SI`, `EE_HI`, `EE_UI`, `DUES`, `PIT` (always, 0 included, when a PIT component exists), `DAMAGE` (when not 0), `NET`, `ADVANCE`, `TO_PAY`, `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT`, `ER_HI`, `ER_UI`, `UNION_FEE`. Contribution lines exist only in a liable month for the funds that apply. An amount the context computes with no active component for its engine code stops the calculation, naming the code (*No active component with engine code %(code)s.*), so `PIT`, `NET` and `TO_PAY` components are needed by every Vietnamese structure's company |

## Folder structure

```
l10n_vn_payroll/
├── __init__.py, __manifest__.py
├── models/
│   ├── __init__.py
│   ├── l10n_vn_payroll_component.py
│   ├── l10n_vn_payroll_scale.py
│   ├── l10n_vn_payroll_contract_line.py
│   ├── hr_contract.py
│   ├── res_company.py
│   ├── l10n_vn_payroll_participant_type.py          # 2
│   ├── hr_employee.py                               # 2, 3
│   ├── hr_employee_relative.py                      # 2
│   ├── l10n_vn_payroll_period.py                    # 3
│   ├── l10n_vn_payroll_input.py                     # 3, 4
│   ├── hr_leave_type.py                             # 3
│   ├── hr_payroll_structure.py                      # 4
│   ├── hr_salary_rule.py                            # 4
│   ├── hr_payslip_line.py                           # 4
│   ├── hr_payslip.py                                # 4, 5
│   ├── pay_context.py                               # 4, 5
│   └── l10n_vn_payroll_damage.py                    # 5
├── data/
│   ├── l10n_vn_payroll_parameters.xml
│   └── l10n_vn_payroll_participant_types.xml        # 2
├── security/
│   ├── l10n_vn_payroll_security.xml
│   └── ir.model.access.csv
├── views/
│   ├── l10n_vn_payroll_component_views.xml
│   ├── l10n_vn_payroll_scale_views.xml
│   ├── hr_contract_views.xml
│   ├── l10n_vn_payroll_participant_type_views.xml   # 2
│   ├── hr_employee_views.xml                        # 2
│   ├── hr_employee_relative_views.xml               # 2
│   ├── l10n_vn_payroll_period_views.xml             # 3
│   ├── l10n_vn_payroll_input_views.xml              # 3
│   ├── hr_leave_type_views.xml                      # 3
│   ├── hr_payroll_structure_views.xml               # 4
│   ├── hr_salary_rule_views.xml                     # 4
│   ├── hr_payslip_views.xml                         # 4
│   ├── l10n_vn_payroll_damage_views.xml             # 5
│   └── menus.xml
├── tests/
│   ├── __init__.py, common.py
│   ├── test_component.py
│   ├── test_scale.py
│   ├── test_contract_line.py
│   ├── test_statutory_parameters.py
│   ├── test_security.py
│   ├── test_participant_type.py                     # 2
│   ├── test_contract_profile.py                     # 2
│   ├── test_employee_payroll.py                     # 2
│   ├── test_pit_method.py                           # 2
│   ├── input_common.py                              # 3
│   ├── test_input_build.py                          # 3
│   ├── test_input_workflow.py                       # 3
│   ├── payslip_common.py                            # 4, 5
│   ├── test_payslip_contract.py                     # 4
│   ├── test_pay_context.py                          # 4
│   ├── test_acceptance.py                           # 4 (as test_acceptance_earnings.py), 5
│   ├── test_contributions.py                        # 5
│   ├── test_pit.py                                  # 5
│   ├── test_damage.py                               # 5
│   └── data/
│       └── acceptance_cases.json                    # 4 (as acceptance_earnings.json), 5
└── readme/
    ├── DESCRIPTION.md
    └── USAGE.md
```

Files of later steps are added to this tree with their step.

## Manifest

| Key | Value |
|---|---|
| `name` | `Vietnam - Payroll` |
| `summary` | `Vietnamese payroll on OCA payroll: pay components, scales and dated pay lines, SI, OT and PIT, statutory parameters` |
| `version` | `18.0.1.0.0` |
| `author` | `1-Aria` |
| `website` | `https://github.com/1-Aria/odoo-qms-pms` |
| `license` | `AGPL-3` |
| `category` | `Human Resources/Payroll` |
| `countries` | `["vn"]` |
| `depends` | `payroll`, `base_time_parameter_strict` (step 1); `hr_employee_relative` (step 2) |
| `data` | `security/l10n_vn_payroll_security.xml`, `security/ir.model.access.csv`, `data/l10n_vn_payroll_parameters.xml`, `data/l10n_vn_payroll_participant_types.xml` (2), `views/l10n_vn_payroll_component_views.xml`, `views/l10n_vn_payroll_scale_views.xml`, `views/l10n_vn_payroll_participant_type_views.xml` (2), `views/hr_contract_views.xml`, `views/hr_employee_views.xml` (2), `views/hr_employee_relative_views.xml` (2), `views/l10n_vn_payroll_period_views.xml` (3), `views/l10n_vn_payroll_input_views.xml` (3), `views/hr_leave_type_views.xml` (3), `views/hr_payroll_structure_views.xml`, `views/hr_salary_rule_views.xml`, `views/hr_payslip_views.xml` (4), `views/l10n_vn_payroll_damage_views.xml` (5), `views/menus.xml` |
| `installable` | `True` |

The security file loads first: the access file names its groups.

## Python packages

| File | Content |
|---|---|
| `__init__.py` | `from . import models` |
| `models/__init__.py` | `from . import l10n_vn_payroll_component`, `from . import l10n_vn_payroll_scale`, `from . import l10n_vn_payroll_contract_line`, `from . import hr_contract`, `from . import res_company`, `from . import l10n_vn_payroll_participant_type` (2), `from . import hr_employee` (2), `from . import hr_employee_relative` (2), `from . import l10n_vn_payroll_period`, `from . import l10n_vn_payroll_input`, `from . import hr_leave_type` (3), `from . import hr_payroll_structure`, `from . import hr_salary_rule`, `from . import hr_payslip_line`, `from . import hr_payslip` (4), `from . import l10n_vn_payroll_damage` (5). `pay_context.py` holds no model and is imported by `hr_payslip.py` |
| `tests/__init__.py` | `from . import test_component`, `from . import test_scale`, `from . import test_contract_line`, `from . import test_statutory_parameters`, `from . import test_security`, `from . import test_participant_type`, `from . import test_contract_profile`, `from . import test_employee_payroll`, `from . import test_pit_method` (2), `from . import test_input_build`, `from . import test_input_workflow` (3), `from . import test_payslip_contract`, `from . import test_pay_context` (4), `from . import test_acceptance` (4, renamed in 5), `from . import test_contributions`, `from . import test_pit`, `from . import test_damage` (5) |

## Groups and rules — `security/l10n_vn_payroll_security.xml`

| XML id | Model | Content |
|---|---|---|
| `group_payroll_reviewer` | `res.groups` | *Reviewer*; category `payroll.module_category_payroll`; implies `payroll.group_payroll_user` |
| `group_payroll_approver` | `res.groups` | *Approver*; category as above; implies `base.group_user` |
| `group_payroll_reader` | `res.groups` | *Reader*; category as above; implies `base.group_user` |
| `payroll.group_payroll_manager` | `res.groups` | `implied_ids`: `Command.link(ref('base_time_parameter.group_time_parameter'))` (D7) |
| `base.default_user` | `res.users` | in a `noupdate="1"` block: `groups_id`: `Command.unlink` of `payroll.group_payroll_manager` and `payroll.group_payroll_user` (D8) |
| `rule_payslip_officer_all` | `ir.rule` | `hr.payslip`; groups `payroll.group_payroll_user`; domain `[(1, '=', 1)]` (D10) |
| `rule_component_company` | `ir.rule` | `l10n_vn.payroll.component`; global; `[('company_id', 'in', company_ids)]` |
| `rule_scale_company` | `ir.rule` | `l10n_vn.payroll.scale`; global; the same |
| `rule_scale_version_company` | `ir.rule` | `l10n_vn.payroll.scale.version`; global; the same |
| `rule_scale_cell_company` | `ir.rule` | `l10n_vn.payroll.scale.cell`; global; the same |
| `rule_contract_line_company` | `ir.rule` | `l10n_vn.payroll.contract.line`; global; the same |
| `rule_period_company`, `rule_input_company`, `rule_input_segment_company`, `rule_input_line_company` (3) | `ir.rule` | the step 3 models; global; the same |
| `rule_damage_company`, `rule_damage_allocation_company` (5) | `ir.rule` | the step 5 models; global; the same |

## Access — `security/ir.model.access.csv`

| id | model | group | r | w | c | u |
|---|---|---|---|---|---|---|
| `access_component_user` | `model_l10n_vn_payroll_component` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_component_reader` | `model_l10n_vn_payroll_component` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_component_manager` | `model_l10n_vn_payroll_component` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_scale_user` | `model_l10n_vn_payroll_scale` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_scale_manager` | `model_l10n_vn_payroll_scale` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_scale_version_user` | `model_l10n_vn_payroll_scale_version` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_scale_version_manager` | `model_l10n_vn_payroll_scale_version` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_scale_cell_user` | `model_l10n_vn_payroll_scale_cell` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_scale_cell_manager` | `model_l10n_vn_payroll_scale_cell` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_contract_line_user` | `model_l10n_vn_payroll_contract_line` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_participant_type_user` (2) | `model_l10n_vn_payroll_participant_type` | `payroll.group_payroll_user` | 1 | 0 | 0 | 0 |
| `access_participant_type_reader` (2) | `model_l10n_vn_payroll_participant_type` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_participant_type_manager` (2) | `model_l10n_vn_payroll_participant_type` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_relative_payroll_user` (2) | `hr_employee_relative.model_hr_employee_relative` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_period_user` (3) | `model_l10n_vn_payroll_period` | `payroll.group_payroll_user` | 1 | 1 | 1 | 0 |
| `access_period_reader` (3) | `model_l10n_vn_payroll_period` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_period_approver` (3) | `model_l10n_vn_payroll_period` | `group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_period_manager` (3) | `model_l10n_vn_payroll_period` | `payroll.group_payroll_manager` | 1 | 1 | 1 | 1 |
| `access_input_user` (3) | `model_l10n_vn_payroll_input` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_input_reader` (3) | `model_l10n_vn_payroll_input` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_input_approver` (3) | `model_l10n_vn_payroll_input` | `group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_input_segment_user` (3) | `model_l10n_vn_payroll_input_segment` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_input_segment_reader` (3) | `model_l10n_vn_payroll_input_segment` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_input_line_user` (3) | `model_l10n_vn_payroll_input_line` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_input_line_reader` (3) | `model_l10n_vn_payroll_input_line` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_input_line_approver` (3) | `model_l10n_vn_payroll_input_line` | `group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_component_approver` (3) | `model_l10n_vn_payroll_component` | `group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_damage_user` (5) | `model_l10n_vn_payroll_damage` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_damage_reader` (5) | `model_l10n_vn_payroll_damage` | `group_payroll_reader` | 1 | 0 | 0 | 0 |
| `access_damage_approver` (5) | `model_l10n_vn_payroll_damage` | `group_payroll_approver` | 1 | 0 | 0 | 0 |
| `access_damage_allocation_user` (5) | `model_l10n_vn_payroll_damage_allocation` | `payroll.group_payroll_user` | 1 | 1 | 1 | 1 |
| `access_damage_allocation_reader` (5) | `model_l10n_vn_payroll_damage_allocation` | `group_payroll_reader` | 1 | 0 | 0 | 0 |

Approvers approve through `action_approve`, which writes as superuser after checking the group (D28).

The reviewer and the manager reach these through the officer group they imply.

## Models

### `l10n_vn.payroll.component` — `models/l10n_vn_payroll_component.py`

`_name = "l10n_vn.payroll.component"`, `_description = "Payroll Component"`, `_order = "sequence, code"`, `_check_company_auto = True`. Module constant `LINE_SOURCES = ("line", "parameter", "scale", "scale_remainder")`, the sources that sit on pay lines, also used by the pay line's domain and checks. `_configuration_problem()` returns the first broken rule's message, or False; `_check_configuration` raises it.

| Field | Type | Attributes |
|---|---|---|
| `code` | Char | required |
| `name` | Char | required, `translate=True` |
| `sequence` | Integer | default 10 |
| `active` | Boolean | default True |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `kind` | Selection | required, default `earning`: `earning` *Earning*, `deduction` *Deduction*, `employer` *Employer contribution*, `total` *Total*, `info` *Information* |
| `legal_nature` | Selection | required: `job_salary` *Salary by job*, `fixed_allowance` *Fixed allowance*, `fixed_supplement` *Fixed supplement*, `variable_salary` *Variable salary*, `bonus` *Bonus (Art. 104)*, `welfare` *Welfare support*, `overtime` *Overtime*, `night` *Night work*, `leave_pay` *Leave pay*, `severance` *Severance*, `statutory` *Statutory contribution or tax*, `union` *Union*, `damage` *Damage compensation*, `advance` *Advance*, `adjustment` *Adjustment*, `total` *Total* |
| `in_si_base` | Boolean | string *In SI base* |
| `in_ot_base` | Boolean | string *In OT base* |
| `pit_treatment` | Selection | `taxable` *Taxable*, `exempt` *Exempt*, `exempt_cap` *Exempt up to a cap*, `excluded` *Excluded*, `ot` *Exempt within the OT limits* |
| `pit_cap_parameter` | Char | parameter code of the cap |
| `amount_source` | Selection | required: `line` *Amount on the pay line*, `parameter` *Parameter*, `scale` *Scale cell*, `scale_remainder` *Remainder of a scale cell*, `entered` *Entered each month*, `ie_units` *IE units × unit rate*, `ot` *Per OT hour*, `engine` *Calculated* |
| `amount_parameter` | Char | parameter code (`parameter`; and the per-hour amount of a supplement, `ot` with `ot_category = all`) |
| `scale_id` | Many2one `l10n_vn.payroll.scale` | `ondelete="restrict"`, `check_company=True` |
| `proration` | Selection | `paid_days` *Paid days*, `days_worked` *Days worked*, `none` *Not prorated*, `per_day` *Daily rate × paid days* |
| `probation_applies` | Boolean | |
| `variable` | Boolean | |
| `attainment_source` | Selection | `supervisor`, `manager`, `ie` |
| `condition` | Selection | required, default `none`: `none`, `attendance` |
| `ot_category` | Selection | `WD`, `RD`, `HOL`, `NIGHT`, `NWD`, `NWD_AFTER`, `NRD`, `NHOL`, `all` |
| `engine_code` | Selection | `GROSS`, `EE_SI`, `EE_HI`, `EE_UI`, `DUES`, `PIT`, `DAMAGE`, `NET`, `ADVANCE`, `TO_PAY`, `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT`, `ER_HI`, `ER_UI`, `UNION_FEE` |
| `section` | Selection | required, default `salary`: `salary`, `ot`, `bonus`, `other`, `deduction`, `employer`, `total` |
| `register_id` | Many2one `hr.contribution.register` | `ondelete="restrict"` |
| `sets_wage` | Boolean | string *Sets the contract wage* (D5) |
| `legal_reference` | Char | |
| `note` | Text | |

**SQL constraint:** `code_company_unique`: `unique(code, company_id)`.

**`_check_configuration`** — `@api.constrains("kind", "amount_source", "scale_id", "amount_parameter", "engine_code", "ot_category", "proration", "pit_treatment", "pit_cap_parameter", "variable", "attainment_source")`, raising `ValidationError` naming the component and the rule:

| Rule |
|---|
| `scale` and `scale_remainder` need `scale_id`; other sources have none |
| `parameter` needs `amount_parameter`; `ot` with `ot_category = all` needs it too |
| `engine` needs `engine_code`; other sources have none |
| `ot` needs `ot_category` and `kind = earning` |
| `kind = earning` needs `pit_treatment`; with a source that sits on pay lines (`line`, `parameter`, `scale`, `scale_remainder`), also `proration` |
| `pit_treatment = exempt_cap` needs `pit_cap_parameter` |
| `variable` only with `kind = earning`, and needs `attainment_source` |
| `per_day` proration only with source `line` |

### `l10n_vn.payroll.scale`, `.scale.version`, `.scale.cell` — `models/l10n_vn_payroll_scale.py`

**`l10n_vn.payroll.scale`** — `_description = "Payroll Scale"`, `_order = "code"`

| Field | Type | Attributes |
|---|---|---|
| `code` | Char | required |
| `name` | Char | required, `translate=True` |
| `kind` | Selection | required: `grade_step` *Grade and step*, `level` *Level* |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `version_ids` | One2many `l10n_vn.payroll.scale.version` | `scale_id` |

SQL: `code_company_unique`: `unique(code, company_id)`.

| Method | Behaviour |
|---|---|
| `_version_on(date)` | the version with the latest `date_from ≤ date`, or an empty recordset |
| `_cell_amount(key, date)` | the `amount` of the cell `key` in `_version_on(date)`; raises `UserError` when there is no version on the date (*Scale %(scale)s has no version on %(date)s.*) or no such cell (*Scale %(scale)s has no cell %(key)s on %(date)s.*) |
| `_has_key(key)` | True when any version holds the cell `key` |

**`l10n_vn.payroll.scale.version`** — `_description = "Payroll Scale Version"`, `_order = "scale_id, date_from desc"`, `_rec_name = "date_from"`

| Field | Type | Attributes |
|---|---|---|
| `scale_id` | Many2one | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `scale_id.company_id`, stored |
| `date_from` | Date | required |
| `note` | Char | |
| `cell_ids` | One2many `l10n_vn.payroll.scale.cell` | `version_id`, `copy=True` |

SQL: `scale_date_unique`: `unique(scale_id, date_from)`.

**`l10n_vn.payroll.scale.cell`** — `_description = "Payroll Scale Cell"`, `_order = "version_id, key"`

| Field | Type | Attributes |
|---|---|---|
| `version_id` | Many2one | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `version_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `key` | Char | required (`G2-2`, `S4`) |
| `grade` | Char | |
| `step` | Integer | |
| `amount` | Monetary | required |

SQL: `version_key_unique`: `unique(version_id, key)`.

### `l10n_vn.payroll.contract.line` — `models/l10n_vn_payroll_contract_line.py`

`_description = "Contract Pay Line"`, `_order = "contract_id, date_from, component_id"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `contract_id` | Many2one `hr.contract` | required, `ondelete="cascade"`, index |
| `employee_id` | Many2one | related `contract_id.employee_id`, stored |
| `company_id` | Many2one | related `contract_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `component_id` | Many2one `l10n_vn.payroll.component` | required, `ondelete="restrict"`, domain `[('amount_source', 'in', ('line', 'parameter', 'scale', 'scale_remainder'))]`, `check_company=True` |
| `amount_source` | Selection | related `component_id.amount_source` |
| `amount` | Monetary | for `line`; for `scale` and `scale_remainder`, overrides the cell |
| `scale_key` | Char | |
| `in_cell` | Boolean | string *Part of the scale cell* |
| `date_from` | Date | required |
| `date_to` | Date | empty = until the contract ends |
| `granted_by` | Many2one `res.users` | |
| `review_date` | Date | |
| `note` | Char | |

**Default:** `date_from` from the context key `default_contract_id`'s `date_start` when given (the contract form's list), else today.

**`_check_line`** — `@api.constrains("contract_id", "component_id", "date_from", "date_to", "amount", "scale_key")`, `ValidationError`:

| Rule |
|---|
| `date_from ≥ contract.date_start`; `date_to ≥ date_from` when set; when the contract has `date_end`, `date_from ≤ date_end` and, when set, `date_to ≤ date_end` (an empty `date_to` runs until the contract ends) |
| source `line`: `amount` set and not 0 |
| sources `scale`, `scale_remainder`: `scale_key` or `amount`; a `scale_key` must be found by the component's scale's `_has_key` |
| no other line of the same contract and component overlaps (D6) |
| no other line of the same contract with a `scale_remainder` component on the same scale overlaps (D6) |

Two lines overlap when `a.date_from ≤ (b.date_to or max)` and `b.date_from ≤ (a.date_to or max)`.

| Method | Behaviour |
|---|---|
| `_l10n_vn_in_force(date)` | lines of `self` with `date_from ≤ date` and (`date_to` empty or `≥ date`) |
| `_l10n_vn_amount_on(date)` | one line's amount on `date` (D2): `line` → `amount`; `parameter` → `base.time.parameter._strict_get(component.amount_parameter, date, company)`; `scale` → `amount` or `scale_id._cell_amount(scale_key, date)`; `scale_remainder` → (`amount` or the cell) − the sum of `_l10n_vn_amount_on(date)` over the contract's lines in force on `date` with `in_cell` |
| `create`, `write`, `unlink` | after the change, `contract_id._l10n_vn_sync_wage()` on the contracts touched (for `unlink`, read before deleting) |

### `hr.contract` — `models/hr_contract.py`

`_inherit = "hr.contract"`.

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_line_ids` | One2many `l10n_vn.payroll.contract.line` | `contract_id`, string *Pay Lines*, `groups="payroll.group_payroll_user"`, `copy=True` |

| Method | Behaviour |
|---|---|
| `_l10n_vn_sync_wage()` | per contract, as superuser: today = `fields.Date.context_today(contract)`; lines = `l10n_vn_line_ids._l10n_vn_in_force(today)` with `component_id.sets_wage`; none → nothing. Otherwise the sum of `_l10n_vn_amount_on(today)`; a `UserError` while reading is caught, logged at `info` with the contract and the message, and `wage` left as it is (D5). Writes `wage` only when it differs |
| `_check_l10n_vn_line_dates` | `@api.constrains("date_start", "date_end")`: runs the lines' `_check_line` again, so a contract cannot be shortened past its lines |

### `hr.contract` additions — `models/hr_contract.py` (step 2)

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_participant_type_id` | Many2one `l10n_vn.payroll.participant.type` | string *Participant Type*, `ondelete="restrict"`, default `l10n_vn_payroll.participant_labour` (looked up with `raise_if_not_found=False`), payroll groups (D13, D14) |
| `l10n_vn_base_source` | Selection | related `l10n_vn_participant_type_id.base_source`, payroll groups |
| `l10n_vn_declared_si_base` | Monetary | string *Declared SI Base*, payroll groups |
| `l10n_vn_probation_form` | Selection | string *Probation*, required, default `none`: `none` *No probation*, `clause` *Clause in this contract*, `contract` *Separate probation contract*; payroll groups |

| Method | Behaviour |
|---|---|
| `_check_l10n_vn_profile` | `@api.constrains("l10n_vn_participant_type_id", "l10n_vn_declared_si_base", "l10n_vn_probation_form", "trial_date_end")`, as superuser, `ValidationError`: a participant type whose `base_source` is `declared` needs `l10n_vn_declared_si_base` above 0; `clause` needs `trial_date_end` |
| `_l10n_vn_pit_method(date)` | D19. "Under 3 months": `date_end` set and `date_start + relativedelta(months=3) > date_end + 1 day`. "Commitment form for that year": the employee's `l10n_vn_pit_commitment_year == date.year`. Runs as superuser. Returns `progressive`, `flat_short` or `flat_nonresident` |

### `l10n_vn.payroll.participant.type` — `models/l10n_vn_payroll_participant_type.py` (step 2)

`_description = "Payroll Participant Type"`, `_order = "code"`.

| Field | Type | Attributes |
|---|---|---|
| `code` | Char | required |
| `name` | Char | required, `translate=True` |
| `active` | Boolean | default True |
| `fund_pension`, `fund_sickness`, `fund_accident`, `fund_hi`, `fund_ui`, `fund_union_fee` | Boolean | strings *Pension and survivorship*, *Sickness and maternity*, *Occupational accident*, *Health insurance*, *Unemployment insurance*, *Union fee (employer)* |
| `dues_allowed` | Boolean | string *Union dues for members* |
| `base_source` | Selection | required, default `components`: `components` *Contract components in the SI base*, `declared` *Declared on the contract* |
| `floor` | Selection | required, default `min_wage`: `min_wage` *Regional minimum wage*, `reference_level` *SI reference level*, `none` *None* |
| `pit_method` | Selection | required, default `progressive`: `progressive` *Progressive*, `flat_short` *Flat 10%, short contracts*, `flat_nonresident` *Flat 20%, non-residents* |
| `note` | Text | |

SQL: `code_unique`: `unique(code)`.

### `hr.employee` — `models/hr_employee.py` (step 2)

`_inherit = "hr.employee"`. Every field with `groups="payroll.group_payroll_user"` (D14).

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_pay_group` | Selection | string *Pay Group*: `worker` *Worker*, `support` *Production support*, `office` *Office*, `daily` *Daily-paid*, `manager` *Manager without labour contract* |
| `l10n_vn_attendance_mode` | Selection | string *Attendance Mode*: `scan` *Scans decide time*, `exception` *Present unless on leave*; stored compute from `l10n_vn_pay_group`, `readonly=False` (D16) |
| `l10n_vn_region` | Selection | string *Minimum Wage Region*: `I`, `II`, `III`, `IV`; default D15 |
| `l10n_vn_resident` | Boolean | string *Tax Resident*, default True |
| `l10n_vn_union_member` | Boolean | string *Union Member* |
| `l10n_vn_pit_commitment_year` | Integer | string *PIT Commitment Form Year* |

| Method | Behaviour |
|---|---|
| `_compute_l10n_vn_attendance_mode` | `@api.depends("l10n_vn_pay_group")`: `worker`, `support`, `daily` → `scan`; `office`, `manager` → `exception`; no pay group → leaves the value |
| `_default_l10n_vn_region` | `base.time.parameter._strict_get("vn.policy.region", today, company=self.env.company)`, its value when it is one of the four regions; a `UserError` gives False (D15) |
| `_l10n_vn_dependent_count(date)` | as superuser, the number of `relative_ids` counted in the month of `date` (D17) |

### `hr.employee.relative` — `models/hr_employee_relative.py` (step 2)

`_inherit = "hr.employee.relative"`. Every field with `groups="payroll.group_payroll_user"` (D14).

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_pit_dependent` | Boolean | string *PIT Dependent* |
| `l10n_vn_tax_code` | Char | string *Dependent Tax Code* |
| `l10n_vn_from` | Date | string *Registered From* |
| `l10n_vn_to` | Date | string *Registered To* |
| `l10n_vn_document_ref` | Char | string *Registration Document* |
| `l10n_vn_document` | Binary | string *Document File*, `attachment=True` |
| `l10n_vn_document_name` | Char | the file name |

| Method | Behaviour |
|---|---|
| `_check_l10n_vn_dependent` | `@api.constrains("l10n_vn_pit_dependent", "l10n_vn_from", "l10n_vn_to")`, as superuser, `ValidationError`: a PIT dependent needs `l10n_vn_from`; `l10n_vn_from` and `l10n_vn_to` are first days of months; `l10n_vn_to ≥ l10n_vn_from` |
| `_l10n_vn_counts_in(month_start)` | D17, for one relative |

### `l10n_vn.payroll.period` — `models/l10n_vn_payroll_period.py` (step 3)

`_description = "Payroll Period"`, `_order = "date_from desc"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `name` | Char | stored compute from `date_from`: `YYYY-MM` |
| `date_from` | Date | required; the first day of a month (constraint) |
| `date_to` | Date | stored compute: the month's last day |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `attendance_closed` | Boolean | readonly; set by `action_close_attendance` |
| `attendance_closed_by`, `attendance_closed_at` | Many2one `res.users`, Datetime | readonly |
| `ie_required` | Boolean | string *IE figures required* |
| `ie_closed` | Boolean | |
| `input_ids` | One2many `l10n_vn.payroll.input` | `period_id` |
| `input_count` | Integer | compute |

SQL: `company_month_unique`: `unique(company_id, date_from)`.

| Method | Behaviour |
|---|---|
| `_check_first_day` | `@api.constrains("date_from")`: day 1 |
| `action_build` | refused when `attendance_closed`. For every employee of the company with an `hr.contract` in state `open` or `close` overlapping the month: finds or creates the input, then `input._l10n_vn_build()` |
| `action_close_attendance` | refused when there is no input; sets the three close fields |
| `action_reopen_attendance` | payroll managers only; clears them (step 7 refuses it once a run of the period is approved) |
| `action_open_inputs` | the inputs of the period in a list |

### `l10n_vn.payroll.input`, `.input.segment`, `.input.line` — `models/l10n_vn_payroll_input.py` (step 3)

**`l10n_vn.payroll.input`** — `_description = "Monthly Payroll Input"`, `_order = "period_id desc, employee_id"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `period_id` | Many2one | required, `ondelete="cascade"`, index |
| `employee_id` | Many2one `hr.employee` | required, `ondelete="restrict"`, index |
| `company_id` | Many2one | related `period_id.company_id`, stored |
| `department_id` | Many2one | related `employee_id.department_id`, stored |
| `scheduled_days`, `days_worked`, `company_leave_days`, `si_leave_days`, `unpaid_leave_days`, `paid_days`, `unpaid_days`, `si_absence_days` | Float `(16, 4)` | computed figures (D20–D25) |
| `unexcused_absences` | Integer | scheduled days with no attendance and no leave |
| `leave_days_json` | Json | days by leave type name; public holidays under *Public holiday* |
| `leave_days_display`, `ot_display` | Char | non-stored computes: the two Json fields as text for the views (`WD 2 · RD 4`) |
| `ot_hours_json` | Json | hours by category (`WD`, `RD`, `HOL`) |
| `ot_hours` | Float | stored compute: the sum of `ot_hours_json` |
| `ot_hours_ytd` | Float | OT hours of the company's earlier inputs of the same year for the employee |
| `paid_break_hours` | Float | credited by D25 |
| `menstruation_days` | Integer | entered |
| `late_arrivals` | Integer | entered; not computed (divergence 10) |
| `attainment` | Float `(16, 4)` | entered; 1.0 = 100% |
| `attainment_source` | Selection | `supervisor` / `manager` / `ie` / `override` |
| `attainment_note` | Char | required when `override` (constraint) |
| `attainment_by` | Many2one `res.users` | readonly; set when `attainment` is written |
| `ie_units` | Float | entered (FR-16) |
| `figures_locked` | Boolean | string *Corrected by hand* (D26) |
| `built_at` | Datetime | readonly |
| `segment_ids` | One2many `l10n_vn.payroll.input.segment` | `input_id` |
| `line_ids` | One2many `l10n_vn.payroll.input.line` | `input_id` |

SQL: `period_employee_unique`: `unique(period_id, employee_id)`.

The computed figures are `FIGURES`, a module constant listing the fields above from `scheduled_days` to `paid_break_hours`, and `segment_ids`.

| Method | Behaviour |
|---|---|
| `write` | when the period's `attendance_closed` is set, refuses a write touching `FIGURES` or `figures_locked`; sets `attainment_by` when `attainment` is written |
| `_l10n_vn_build()` | for each input not `figures_locked`: `vals = self._l10n_vn_compute_figures()`; writes them, replaces `segment_ids`, sets `built_at` |
| `_l10n_vn_compute_figures()` | returns the figures and segments for the month (below) |
| `_l10n_vn_days()` | the per-day table the figures sum (below) |

**The per-day table** (`_l10n_vn_days`), for each contract of the employee in state `open` or `close` overlapping the month, over the overlap, with `cal` = the contract's `resource_calendar_id` and its `tz`:

| Per local date | From |
|---|---|
| `scheduled` | the hours of `cal._attendance_intervals_batch(start, end, resources=employee.resource_id)` on that date (lunch excluded) |
| `holiday` | True when a calendar leave with no resource covers the date in `cal` |
| `leave_company`, `leave_si`, `leave_unpaid`, `leave_types` | hours of `employee.list_leaves(start, end, calendar=cal)` on that date, by D21 |
| `worked`, `ot_raw`, `ot_valid` | the sums of `worked_hours`, and of `overtime_hours` and `validated_overtime_hours` each taken at 0 when negative (core reports missing hours as negative overtime; `MINW` filters them the same way), of the employee's `hr.attendance` whose `check_in`, in `cal`'s time zone, falls on that date |
| `contract` | the contract |

**The figures,** from the table, with `m` = `vn.policy.ot_min_hours_day` on the month's last day:

| Figure | Per scheduled date (`scheduled` > 0), summed |
|---|---|
| `days_worked` | min(1, max(0, `worked` − `ot_raw`) ÷ `scheduled`) |
| `company_leave_days` | min(1 − days worked, `leave_company` ÷ `scheduled`) |
| `si_leave_days`, `unpaid_leave_days` | the same for `leave_si`, `leave_unpaid`, each capped by what is left of the day |
| paid break days | credited hours (D25) ÷ `scheduled` |
| `paid_days` | days worked + company leave days + paid break days |
| `scheduled_days` | the count of scheduled dates |
| `unpaid_days` | `scheduled_days` − `paid_days`, at least 0 |
| `si_absence_days` | `scheduled_days` − `paid_days`, the same days counted for FR-23: neither worked nor paid by the company |
| `unexcused_absences` | scheduled dates with no attendance and no leave |
| `ot_hours_json` | on every date (scheduled or not) with `ot_valid` ≥ `m`: `ot_valid` added to `HOL`, `RD` or `WD` (D22) |
| `segment_ids` | D24: when the month has more than one piece, one segment per piece with its own `paid_days`, `days_worked` and `ot_hours_json` |

A rest day (no scheduled hours) adds nothing to days; its overtime counts under `RD`.

**`l10n_vn.payroll.input.segment`** — `_description = "Monthly Payroll Input Segment"`, `_order = "input_id, date_from"`.

| Field | Type | Attributes |
|---|---|---|
| `input_id` | Many2one | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `input_id.company_id`, stored |
| `date_from`, `date_to` | Date | required |
| `contract_id` | Many2one `hr.contract` | |
| `paid_days`, `days_worked` | Float `(16, 4)` | |
| `ot_hours_json` | Json | |

**`l10n_vn.payroll.input.line`** — `_description = "Monthly Payroll Input Line"`, `_order = "input_id, id"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `input_id` | Many2one | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `input_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `component_id` | Many2one `l10n_vn.payroll.component` | required, `ondelete="restrict"`, `check_company=True` |
| `amount` | Monetary | |
| `hours` | Float | for an OT adjustment |
| `period_ref` | Date | first day of the month an adjustment belongs to |
| `description` | Char | |
| `approved_by`, `approved_at` | Many2one `res.users`, Datetime | readonly |

| Method | Behaviour |
|---|---|
| `_check_line` | `@api.constrains("component_id", "period_ref")`: without `period_ref`, the component's source is `entered`; with it, the component is an earning or a deduction, and `period_ref` is a first day of a month before the input's period |
| `write` | writing `component_id`, `amount`, `hours` or `period_ref` on an approved line clears `approved_by` and `approved_at` |
| `action_approve` | for `group_payroll_approver` (else `AccessError`): sets both fields as superuser |
| `action_reset_approval` | the same group: clears them |

### `hr.leave.type` — `models/hr_leave_type.py` (step 3)

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_si_paid` | Boolean | string *Paid by social insurance*; constraint: not together with core's `unpaid` |

### `hr.employee` addition (step 3)

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_nursing_break` | Boolean | string *Nursing Break*, payroll groups (D25) |

| Method | Behaviour |
|---|---|
| `_l10n_vn_nursing_until()` | the latest first birthday (date of birth + 12 months) among the employee's relatives with relation `hr_employee_relative.relation_child` and a date of birth, when `l10n_vn_nursing_break`; else False |

### `hr.employee` addition (step 4)

| Method | Behaviour |
|---|---|
| `_l10n_vn_period_contracts(date_from, date_to)` | as superuser, the contracts of the employee (`ensure_one`) in state `open` or `close` with `date_start ≤ date_to` and (`date_end` empty or `≥ date_from`), ordered by `date_start` (D31) |

### `l10n_vn.payroll.input` changes (step 4)

| Method | Behaviour |
|---|---|
| `_l10n_vn_pieces()` | D33. For each contract of `employee_id._l10n_vn_period_contracts(period.date_from, period.date_to)`: span = (max(`date_start`, month start), min(`date_end` or month end, month end)); cut dates inside the span after its first day: each of the contract's pay lines' `date_from` and `date_to` + 1 day, and `trial_date_end` + 1 day when `l10n_vn_probation_form == "clause"` and `trial_date_end` is set (pay lines and `trial_date_end` read as superuser). Returns, in date order, one dict per piece: `date_from`, `date_to`, `contract` (record), `probation` (Boolean) |
| `_l10n_vn_days()` | unchanged, except that its contracts come from `_l10n_vn_period_contracts` |
| `_l10n_vn_compute_figures()` | segments from `_l10n_vn_pieces()`: when there is more than one piece, one segment per piece with its dates, `contract_id`, and `paid_days`, `days_worked` and `ot_hours_json` summed over the piece's days. `_l10n_vn_cut_dates` is removed |

### `hr.payroll.structure` — `models/hr_payroll_structure.py` (step 4)

`_inherit = "hr.payroll.structure"`.

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_payroll` | Boolean | string *Vietnamese Pay Context* (D30) |

### `hr.salary.rule` — `models/hr_salary_rule.py` (step 4)

`_inherit = "hr.salary.rule"`. `hr.payslip.line` inherits the rule (`oca/payroll/payroll/models/hr_payslip_line.py:9`), so these fields reach payslip lines too.

| Field | Type | Attributes |
|---|---|---|
| `amount_select` | Selection | `selection_add=[("l10n_vn_component", "Pay Component")]`, `ondelete={"l10n_vn_component": "set default"}` |
| `condition_select` | Selection | the same |
| `l10n_vn_component_id` | Many2one `l10n_vn.payroll.component` | string *Pay Component*, `ondelete="restrict"` |

| Method | Behaviour |
|---|---|
| `_check_l10n_vn_component` | `@api.constrains("amount_select", "condition_select", "l10n_vn_component_id")`; returns at once when `self._name != "hr.salary.rule"` (payslip lines inherit the constraint); `amount_select` or `condition_select` equal to `l10n_vn_component` needs `l10n_vn_component_id`, else `ValidationError` |
| `_satisfy_condition_l10n_vn_component(localdict)` | `bool(localdict["payslip"]._l10n_vn_context_lines(self.l10n_vn_component_id))`; OCA calls it by name (`oca/payroll/payroll/models/hr_salary_rule.py:299`) |
| `_compute_rule_l10n_vn_component(localdict)` | parts = `localdict["payslip"]._l10n_vn_context_lines(self.l10n_vn_component_id)`; returns `name` (the first part's name, else the rule's), `quantity` 1.0, `rate` 100.0, `amount` the sum of the parts' `amount`, and `l10n_vn_parts`: per part, `name`, `amount` and the display fields `l10n_vn_days`, `l10n_vn_hours`, `l10n_vn_factor`, `l10n_vn_unit_amount`, `l10n_vn_date_from`, `l10n_vn_date_to`, `l10n_vn_attainment`, `l10n_vn_period_ref` from the part's `days`, `hours`, `factor`, `unit_amount`, `date_from`, `date_to`, `attainment`, `period_ref` (D43) |

### `hr.payslip.line` — `models/hr_payslip_line.py` (step 4)

`_inherit = "hr.payslip.line"`. Display fields (D43), empty when the context line has no such value:

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_days` | Float `(16, 4)` | string *Days* |
| `l10n_vn_hours` | Float `(16, 4)` | string *Hours* |
| `l10n_vn_factor` | Float `(16, 6)` | string *Factor* |
| `l10n_vn_unit_amount` | Float `(16, 4)` | string *Unit Amount* (the OT hourly rate) |
| `l10n_vn_date_from`, `l10n_vn_date_to` | Date | strings *From*, *To* |
| `l10n_vn_attainment` | Float `(16, 4)` | string *Attainment* |
| `l10n_vn_period_ref` | Date | string *Belongs to month* |

### `hr.payslip` — `models/hr_payslip.py` (step 4)

`_inherit = "hr.payslip"`.

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_input_id` | Many2one `l10n_vn.payroll.input` | string *Monthly Input*, readonly, `copy=False`, `ondelete="restrict"` |
| `l10n_vn_context` | Json | string *Pay Context*, readonly, `copy=False` (the snapshot, below) |

| Method | Behaviour |
|---|---|
| `_l10n_vn_is_vn()` | True when `struct_id.l10n_vn_payroll` (`ensure_one`) |
| `get_payslip_vals(date_from, date_to, employee_id=False, contract_id=False, struct_id=False)` | main = the last of `employee._l10n_vn_period_contracts(date_from, date_to)`; when there is one and the structure (`struct_id[0]` when given, as OCA's batch passes it, else `main.struct_id`) has `l10n_vn_payroll`: `super()` under the context key `contract=True` with `contract_id=main.id`, so OCA keeps that contract (`oca/payroll/payroll/models/hr_payslip.py:638-651`); otherwise `super()` unchanged (D30, D31) |
| `_get_employee_contracts()` | per payslip: without `contract_id`, when the employee's main contract for the payslip's dates has a structure with `l10n_vn_payroll`, that contract; otherwise OCA's choice |
| `get_worked_day_lines(contracts, date_from, date_to)` | when `contracts[:1].struct_id.l10n_vn_payroll`: `_l10n_vn_worked_day_vals(input, contract)` with the summary from `_l10n_vn_find_input(contract.employee_id, contract.company_id, date_from)`, or `[]` when there is none; otherwise `super()`. OCA's `WORK100` is not produced (design §11) |
| `_l10n_vn_find_input(employee, company, date_from)` | `@api.model`: the input of `employee` in the period of `company` whose `date_from` is `date_from`, or an empty recordset |
| `_l10n_vn_worked_day_vals(input, contract)` | `@api.model`: a list of worked-day values, each with `contract_id` = `contract.id`: `PAID` *Paid days* (sequence 1, `paid_days`), `WORKED` *Days worked* (2, `days_worked`), `UNPAID` *Unpaid days* (3, `unpaid_days`), and per entry of `leave_days_json` a line `LEAVE` named after the entry (10, its days) |
| `compute_sheet()` | `self.filtered(lambda p: p._l10n_vn_is_vn())._l10n_vn_prepare()`, then `super()` |
| `_l10n_vn_prepare()` | D42, D44. Refuses a payslip whose `date_from` is not a 1st or whose `date_to` is not that month's last day (D32). Finds every summary in one search (employees and periods of `self`). `builder = PayContext(self.env(su=True))`. Per payslip: main = the last period contract, else `UserError` (*%(employee)s has no contract in %(month)s.*); the summary, else `UserError` (*%(employee)s has no monthly input for %(month)s.*); `context = builder.build(payslip, main, input)`; writes `contract_id` main, `l10n_vn_input_id`, `l10n_vn_context`, and `worked_days_line_ids` = `[Command.clear()]` + `Command.create` of `_l10n_vn_worked_day_vals(input, main)`. Then every `component_id` among the context's lines must have a rule in `_get_salary_rules()` with that `l10n_vn_component_id`, else `UserError` (*Component %(code)s has amounts for %(employee)s but no rule in structure %(structure)s.*) |
| `get_payroll_dict(contracts)` | `super()`; for a Vietnamese payslip adds `vn`: `l10n_vn_context` |
| `_l10n_vn_context_lines(component)` | the context lines whose `component_id` is `component.id`, in context order |
| `_get_lines_dict(rule, localdict, lines_dict, key, values, previous_amount)` | D43. Pops `l10n_vn_parts` from `values`. On a Vietnamese payslip, for a rule whose `amount_select` is not `l10n_vn_component`: `values` gets quantity 1, rate 100 and amount = round half up of quantity × rate × amount ÷ 100. Calls `super()`. For an `l10n_vn_component` rule: `lines_dict[key]` gets `l10n_vn_component_id`; with parts, the first part's values (with quantity 1, rate 100, `total` = its amount) update `lines_dict[key]`, and each further part *n* is filed under `f"{key}-{n}"` as a copy of that line with its own values. Returns `localdict, lines_dict` |

### Pay context — `models/pay_context.py` (step 4)

A plain Python class, `PayContext`, not a model. It reads as superuser, so record rules do not apply: every search for components (`ot`, `ie_units`, `GROSS`) has `company_id` = the payslip's company and `active` in its domain. Module helpers: `_dec(value)` = `Decimal(str(value or 0))`; `_round(d)` = `int(d.quantize(Decimal(1), rounding=ROUND_HALF_UP))`; `HOURS_PER_DAY = 8`.

| Member | Behaviour |
|---|---|
| `__init__(env)` | `env`, a superuser environment; `params`, a dict cache |
| `param(code, date, company)` | `base.time.parameter._strict_get(code, date, company=company)`, once per `(code, date, company.id)`; each value read is also kept for the snapshot's `parameters` |
| `build(payslip, contract, input)` | the context below, in the order of the steps |

**Steps of `build`:**

| # | Step |
|---|---|
| 1 | pieces = `input._l10n_vn_pieces()`; their figures by D34: one piece → the summary's `paid_days`, `days_worked`, `ot_hours_json`; more → the matching segments', else `UserError` (*The monthly input of %(employee)s for %(month)s needs segments for %(pieces)s; rebuild it.*) |
| 2 | *s* = `vn.policy.std_days` on the month's last day |
| 3 | per piece, the pay lines in force on its last day (`contract.l10n_vn_line_ids._l10n_vn_in_force`) of active components, with `_l10n_vn_amount_on(piece date_to)` (D35) |
| 4 | attainment (D37): when any of them is `variable`, `UserError` (*%(employee)s has no attainment or score for %(month)s.*) if `attainment_source` is empty, else *a* = min(`attainment`, `vn.policy.attainment_cap`) |
| 5 | pay line components (D36), with the attendance condition (D38) |
| 6 | OT (D40): per piece its OT base and hourly rate, then the lines; `vn.ot.factors` on the piece's last day; hours in a category without an active `ot` component → `UserError` (*%(employee)s has %(category)s overtime and no active component pays it.*) |
| 7 | IE lines, then entered and adjustment lines (D39), so an adjustment follows the month's own line of its component |
| 8 | gross (D41) |

**A context line** (a dict): `component_id`, `code`, `kind`, `name` (D45), `amount` (int), `days`, `hours`, `factor`, `unit_amount`, `date_from`, `date_to`, `attainment`, `period_ref`, `pay_line_id`, `input_line_id`, `piece` (its index, or None for a month-level line). Pay line lines set `days` (the basis days), `piece`, `date_from`/`date_to` when the month has more than one piece, `attainment` when `variable`; a `none` line is month-level: no `days`, `piece`, dates. OT lines set `hours`, `factor`, `unit_amount` (the hourly rate, rounded to 4 places), `piece`, and the piece's dates when there is more than one; a supplement line sets `hours` (the sum over its categories), `unit_amount` (the supplement per hour) and no `factor`. Lines appear in this order: pay line components by piece (month-level `none` lines after them), OT lines by piece, IE lines, entered and adjustment lines, gross.

**The snapshot** (`l10n_vn_context`), JSON values only (dates as ISO strings, amounts as int, figures as float):

| Key | Content |
|---|---|
| `version` | 1 |
| `employee_id`, `contract_id`, `input_id` | ids |
| `date_from`, `date_to` | the month |
| `parameters` | list of `{code, date, value}` read by `param` |
| `input` | the summary's `paid_days`, `days_worked`, `unpaid_days`, `scheduled_days`, `si_absence_days`, `unexcused_absences`, `late_arrivals`, `ot_hours_json`, `ot_hours_ytd`, `attainment`, `attainment_source`, `ie_units`, `figures_locked`, `built_at` |
| `std_days` | *s* |
| `attainment` | *a* applied, or null |
| `pieces` | per piece: `date_from`, `date_to`, `contract_id`, `probation`, `paid_days`, `days_worked`, `ot_hours_json`, `ot_base`, `hourly` |
| `pay_lines` | per pay line used per piece: `id`, `piece`, `component`, `scale_key`, `amount` (on the piece's last day) |
| `lines` | the context lines |
| `unapproved` | ids of input lines left out for lack of an approver |
| `gross` | the gross |

### `l10n_vn.payroll.input` additions (step 5)

| Field | Type | Attributes |
|---|---|---|
| `month_scheduled_days` | Float `(16, 4)` | string *Scheduled days in the month*; a computed figure, in `FIGURES` (D46) |

| Method | Behaviour |
|---|---|
| `_l10n_vn_month_scheduled_days()` | with the last of `employee_id._l10n_vn_period_contracts(period dates)` as main contract (none → 0), `cal` its calendar and its `tz`: the number of local dates from the month's first to its last day carrying hours in `cal._attendance_intervals_batch(month start, day after month end, resources=employee.resource_id)` |
| `_l10n_vn_compute_figures()` | also returns `month_scheduled_days` from the method above |

### `l10n_vn.payroll.damage`, `.damage.allocation` — `models/l10n_vn_payroll_damage.py` (step 5)

**`l10n_vn.payroll.damage`** — `_description = "Damage Compensation Decision"`, `_order = "employee_id, decision_date, id"`, `_check_company_auto = True`.

| Field | Type | Attributes |
|---|---|---|
| `employee_id` | Many2one `hr.employee` | required, `ondelete="restrict"`, index, `check_company=True` |
| `company_id` | Many2one `res.company` | required, default `self.env.company` |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `decision_ref` | Char | required, string *Decision* |
| `decision_date` | Date | required |
| `reason` | Char | required |
| `amount` | Monetary | required, string *Amount decided* |
| `allocation_ids` | One2many `l10n_vn.payroll.damage.allocation` | `damage_id`, readonly |
| `deducted` | Monetary | stored compute: the sum of `allocation_ids.amount` whose payslip is `done`; depends `allocation_ids.amount`, `allocation_ids.payslip_id.state` |
| `balance` | Monetary | stored compute: `amount` − `deducted` |
| `state` | Selection | stored compute: `open` *Open* while `balance` > 0, else `done` *Settled* |
| `note` | Text | |

SQL: `amount_positive`: `CHECK(amount > 0)`.

| Method | Behaviour |
|---|---|
| `unlink` | refused (`UserError`) for a decision with `deducted` > 0 |
| `_l10n_vn_available(payslip)` | per decision: `amount` − the sum of its allocations on payslips other than `payslip` whose state is not `cancel` |

**`l10n_vn.payroll.damage.allocation`** — `_description = "Damage Compensation Allocation"`, `_order = "damage_id, id"`.

| Field | Type | Attributes |
|---|---|---|
| `damage_id` | Many2one | required, `ondelete="restrict"`, index |
| `payslip_id` | Many2one `hr.payslip` | required, `ondelete="cascade"`, index |
| `company_id` | Many2one | related `damage_id.company_id`, stored |
| `currency_id` | Many2one | related `company_id.currency_id` |
| `amount` | Monetary | |
| `payslip_state` | Selection | related `payslip_id.state` |

### `hr.payslip` additions (step 5)

| Field | Type | Attributes |
|---|---|---|
| `l10n_vn_damage_allocation_ids` | One2many `l10n_vn.payroll.damage.allocation` | `payslip_id`, readonly, string *Damage Deductions* |

| Method | Behaviour |
|---|---|
| `_l10n_vn_advances()` | the advances this payslip settles, oldest first, as a list of `{"id", "amount"}`; returns `[]` here (D57), `l10n_vn_payroll_account` overrides it |
| `_l10n_vn_prepare()` | after writing the context: replaces `l10n_vn_damage_allocation_ids` with one allocation per entry of the context's `damage` (D56) |

### Pay context additions (step 5)

`build(payslip, contract, inp)` gains, after gross:

| # | Step |
|---|---|
| 9 | contributions (D47–D50): `month_scheduled_days` of 0 → `UserError` (*The monthly input of %(employee)s for %(month)s has no scheduled days for the month; rebuild it.*); every period contract needs a participant type, else `UserError` (*Contract %(contract)s of %(employee)s has no participant type.*); the region, when needed, else `UserError` (*%(employee)s has no minimum wage region.*) |
| 10 | PIT (D53–D55) |
| 11 | damage compensation (D56) |
| 12 | net, advances and to pay (D57) |
| 13 | the engine lines (D58) |

`_entered_lines` turns the amount of a deduction component's line negative (D51).

**Snapshot additions:**

| Key | Content |
|---|---|
| `contributions` | `liable` (Boolean), `days_without_si`, `base_source`, `base` (after the floor), `floor`, `si_capped` (*S*), `ui_capped` (*U*), `funds` (the engine codes calculated), `region`, `rates` (per engine code, `[rate, capped base]`), or null figures when not liable |
| `pit` | `method`, `exempt` (*E*), `ot_exempt`, `taxable` (*T*), `dependents`, `pit` |
| `damage` | `{"allocations": [{damage_id, amount}, …], "total": …}` |
| `advances` | per advance `{id, amount, settled}` |
| `employee_insurance`, `dues`, `net`, `settled`, `to_pay` | positive figures |

### `res.company` — `models/res_company.py`

`_inherit = "res.company"`.

**`STATUTORY_PARAMETERS`**, a module-level list of `(code, name, type, versions)`, `versions` a list of `(date_from, value)` with the value as stored text:

| Code | Name | Type | Versions |
|---|---|---|---|
| `vn.min_wage.month` | Regional minimum wage, monthly | json | 2026-01-01 `{"I": 5310000, "II": 4730000, "III": 4140000, "IV": 3700000}` |
| `vn.min_wage.hour` | Regional minimum wage, hourly | json | 2026-01-01 `{"I": 25500, "II": 22700, "III": 19900, "IV": 17800}` |
| `vn.si.reference_level` | SI reference level | float | 2024-07-01 `2340000`; 2026-07-01 `2530000` |
| `vn.si.cap_multiple` | SI and HI cap, multiple of the reference level | float | 2026-01-01 `20` |
| `vn.ui.cap_multiple` | UI cap, multiple of the regional minimum wage | float | 2026-01-01 `20` |
| `vn.rate.ee.si` | Employee SI rate | float | 2026-01-01 `0.08` |
| `vn.rate.ee.hi` | Employee HI rate | float | 2026-01-01 `0.015` |
| `vn.rate.ee.ui` | Employee UI rate | float | 2026-01-01 `0.01` |
| `vn.rate.er.pension` | Employer pension and survivorship rate | float | 2026-01-01 `0.14` |
| `vn.rate.er.sickness` | Employer sickness and maternity rate | float | 2026-01-01 `0.03` |
| `vn.rate.er.accident` | Employer occupational accident rate | float | 2026-01-01 `0.005` |
| `vn.rate.er.hi` | Employer HI rate | float | 2026-01-01 `0.03` |
| `vn.rate.er.ui` | Employer UI rate | float | 2026-01-01 `0.01` |
| `vn.rate.union_fee` | Employer union fee rate | float | 2026-01-01 `0.02` |
| `vn.rate.union_dues` | Union dues rate, members | float | 2026-01-01 `0.005` |
| `vn.union_dues.cap` | Union dues cap | float | 2026-01-01 `253000` |
| `vn.si.absence_days` | Working days without work or pay that suspend contributions | integer | 2026-01-01 `14` |
| `vn.pit.self` | PIT personal deduction | float | 2026-01-01 `15500000` |
| `vn.pit.dependent` | PIT deduction per dependent | float | 2026-01-01 `6200000` |
| `vn.pit.brackets` | PIT monthly brackets | json | 2026-01-01 `[[10000000, 0.05], [30000000, 0.10], [60000000, 0.20], [100000000, 0.30], [null, 0.35]]` |
| `vn.pit.flat_short` | PIT flat rate, contracts under 3 months | float | 2026-01-01 `0.10` |
| `vn.pit.flat_short_threshold` | PIT flat rate threshold per payment | float | 2026-01-01 `5000000` |
| `vn.pit.nonresident` | PIT rate, non-residents | float | 2026-01-01 `0.20` |
| `vn.pit.meal_cap` | PIT-free cash meal allowance | float | 2026-01-01 `730000`; 2026-07-01 `1200000` |
| `vn.ot.factors` | OT and night factors | json | 2026-01-01 `{"WD": 1.5, "RD": 2.0, "HOL": 3.0, "NIGHT": 0.3, "NWD": 2.0, "NWD_AFTER": 2.1, "NRD": 2.7, "NHOL": 3.9}` |
| `vn.ot.limit.month` | OT hours limit per month | integer | 2026-01-01 `40` |
| `vn.ot.limit.year` | OT hours limit per year, textile and garment | integer | 2026-01-01 `300` |
| `vn.damage.cap` | Damage compensation cap, share of pay after insurance and PIT | float | 2026-01-01 `0.30` |
| `vn.probation.min_rate` | Minimum probation pay rate | float | 2026-01-01 `0.85` |
| `vn.probation.max_days` | Maximum probation by job | json | 2026-01-01 `{"manager": 180, "college": 60, "vocational": 30, "other": 6}` (`other` in working days) |

| Method | Behaviour |
|---|---|
| `_l10n_vn_payroll_ensure_parameters()` | for each company in `self` with `country_id.code == "VN"`, as superuser, inside `self.env.cr.savepoint()`: for each entry, the parameter with that `code` and `company_id` is found or created (`name`, `code`, `type`, `company_id`, `country_id` the company's country); each version whose `date_from` the parameter lacks is created. Existing versions are not touched. An exception is logged at `warning` with the company and the code, and the next company continues (D9) |
| `_l10n_vn_payroll_ensure_parameters_all()` | `@api.model`: calls the above on every company |

## Data — `data/l10n_vn_payroll_parameters.xml`

`<function model="res.company" name="_l10n_vn_payroll_ensure_parameters_all"/>`, not in a `noupdate` block, so it runs at every install and upgrade (D9).

## Data — `data/l10n_vn_payroll_participant_types.xml` (step 2)

`noupdate="1"` (D12):

| XML id | Code | Name | Funds | Dues | Base | Floor | PIT |
|---|---|---|---|---|---|---|---|
| `participant_labour` | `LABOUR` | Labour contract of 1 month or more | all six | yes | components | min_wage | progressive |
| `participant_probation` | `PROBATION` | Probation contract | none | no | components | none | flat_short |
| `participant_manager` | `MANAGER` | Manager paid without a labour contract | pension, sickness, accident, HI, union fee | yes | declared | reference_level | progressive |
| `participant_short` | `SHORT` | Contract under 1 month | none | no | components | none | flat_short |

`MANAGER`'s `note`: *Funds and floor to confirm with the SI office (Regulation Reference v0.2).*

## Views

### `views/l10n_vn_payroll_component_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_component_view_list` | list | `sequence` (handle), `code`, `name`, `kind`, `legal_nature`, `amount_source`, `in_si_base`, `in_ot_base`, `pit_treatment`, `proration`, `variable`, `company_id` (multi-company group), `active` (hidden) |
| `l10n_vn_payroll_component_view_form` | form | title `code` and `name`; groups *Treatment* (`kind`, `legal_nature`, `in_si_base`, `in_ot_base`, `pit_treatment`, `pit_cap_parameter` visible when `pit_treatment == 'exempt_cap'`), *Amount* (`amount_source`, `amount_parameter` visible when `amount_source in ('parameter', 'ot')`, `scale_id` visible when `amount_source in ('scale', 'scale_remainder')`, `proration`, `probation_applies`, `variable`, `attainment_source` visible when `variable`, `condition`, `ot_category` visible when `amount_source == 'ot'`, `engine_code` visible when `amount_source == 'engine'`), *Payslip and posting* (`section`, `sequence`, `register_id`, `sets_wage`), *Legal* (`legal_reference`, `note`); `company_id`, `active` |
| `l10n_vn_payroll_component_view_search` | search | `code`, `name`; filters by `kind`, *Variable*, *Archived*; group by `kind`, `legal_nature`, `amount_source` |
| `l10n_vn_payroll_component_action` | action | *Pay Components*, list, form |

### `views/l10n_vn_payroll_scale_views.xml`

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_scale_view_list` | list | `code`, `name`, `kind`, `company_id` |
| `l10n_vn_payroll_scale_view_form` | form | `code`, `name`, `kind`, `company_id`; `version_ids` as a list (`date_from`, `note`) opening the version form |
| `l10n_vn_payroll_scale_version_view_form` | form | `scale_id` (read-only), `date_from`, `note`; `cell_ids` as an editable list (`key`, `grade`, `step`, `amount`) |
| `l10n_vn_payroll_scale_action` | action | *Pay Scales*, list, form |

### `views/hr_contract_views.xml`

| XML id | Inherits | Content |
|---|---|---|
| `hr_contract_view_form_l10n_vn_payroll` | `hr_contract.hr_contract_view_form` | after the page `information`, a page *Pay Lines* (`name="l10n_vn_pay_lines"`, `groups="payroll.group_payroll_user"`) with `l10n_vn_line_ids` as an editable list: `component_id`, `scale_key`, `amount`, `in_cell`, `date_from`, `date_to`, `granted_by` (optional), `review_date` (optional), `note` (optional); the list's context sets `default_contract_id` |

### `views/l10n_vn_payroll_participant_type_views.xml` (step 2)

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_participant_type_view_list` | list | `code`, `name`, the six funds, `dues_allowed`, `base_source`, `floor`, `pit_method`, `active` (hidden) |
| `l10n_vn_payroll_participant_type_view_form` | form | title `name`; `code`, `active`; group *Funds* (the six, `dues_allowed`); group *Base and tax* (`base_source`, `floor`, `pit_method`); `note` |
| `l10n_vn_payroll_participant_type_action` | action | *Participant Types*, list, form |

### `views/hr_contract_views.xml` additions (step 2)

In `hr_contract_view_form_l10n_vn_payroll`, at the top of the *Pay Lines* page, before `l10n_vn_line_ids`: a group with `l10n_vn_participant_type_id`, `l10n_vn_declared_si_base` (visible when `l10n_vn_base_source == 'declared'`, with the hidden `l10n_vn_base_source`), `l10n_vn_probation_form`.

### `views/hr_employee_views.xml` (step 2)

| XML id | Inherits | Content |
|---|---|---|
| `hr_employee_view_form_l10n_vn_payroll` | `hr.view_employee_form` | inside `//notebook`, a page *Payroll* (`name="l10n_vn_payroll"`, `groups="payroll.group_payroll_user"`) with `l10n_vn_pay_group`, `l10n_vn_attendance_mode`, `l10n_vn_region`, `l10n_vn_resident`, `l10n_vn_union_member`, `l10n_vn_pit_commitment_year` |

### `views/hr_employee_relative_views.xml` (step 2)

| XML id | Inherits | Content |
|---|---|---|
| `hr_employee_relative_view_tree_l10n_vn_payroll` | `hr_employee_relative.hr_employee_relative_view_tree` | after `notes`, each with `groups="payroll.group_payroll_user"`: `l10n_vn_pit_dependent`, `l10n_vn_tax_code`, `l10n_vn_from`, `l10n_vn_to`, `l10n_vn_document_ref` (optional), `l10n_vn_document` with `filename="l10n_vn_document_name"` (optional), `l10n_vn_document_name` (column invisible) |

### `views/l10n_vn_payroll_period_views.xml` (step 3)

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_period_view_list` | list | `name`, `company_id`, `attendance_closed`, `ie_required`, `ie_closed`, `input_count` |
| `l10n_vn_payroll_period_view_form` | form | header buttons *Build Summaries* (`action_build`, visible while open), *Close Attendance* (`action_close_attendance`, while open), *Reopen Attendance* (`action_reopen_attendance`, closed, managers); smart button *Inputs* (`action_open_inputs`, `input_count`); `date_from`, `name`, `company_id`; `attendance_closed`, `attendance_closed_by`, `attendance_closed_at`, `ie_required`, `ie_closed` |
| `l10n_vn_payroll_period_action` | action | *Payroll Periods*, list, form |

### `views/l10n_vn_payroll_input_views.xml` (step 3)

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_input_view_list` | list, editable `bottom`, no create | `period_id`, `employee_id`, `department_id`, `paid_days`, `days_worked`, `unpaid_days`, `ot_hours`, `paid_break_hours`, `menstruation_days`, `attainment`, `attainment_source`, `attainment_note`, `ie_units`, `figures_locked`; the computed figures read-only |
| `l10n_vn_payroll_input_view_form` | form | `period_id`, `employee_id`, `department_id`; `figures_locked`, `built_at`; groups *Days* (the eight day figures, read-only unless `figures_locked`), *Overtime and breaks* (`ot_display`, `ot_hours`, `ot_hours_ytd` and `paid_break_hours` read-only unless `figures_locked`, `menstruation_days`), *Attainment* (`attainment`, `attainment_source`, `attainment_note` required when `attainment_source == 'override'`, `attainment_by`, `ie_units`), *Other* (`leave_days_display`, `unexcused_absences` read-only unless `figures_locked`, `late_arrivals`); the Json fields are shown through their display fields; pages *Entered Lines* (`line_ids` editable: `component_id`, `amount`, `hours`, `period_ref`, `description`, `approved_by`, buttons *Approve* / *Reset* for approvers) and *Segments* (`segment_ids`, read-only) |
| `l10n_vn_payroll_input_view_search` | search | `employee_id`, `department_id`, `period_id`; filters *Attainment missing* (`attainment = 0`), *Corrected by hand*; group by `period_id`, `department_id` |
| `l10n_vn_payroll_input_action` | action | *Monthly Inputs*, list, form |

### `views/hr_leave_type_views.xml` (step 3)

| XML id | Inherits | Content |
|---|---|---|
| `hr_leave_type_view_form_l10n_vn_payroll` | `hr_holidays.edit_holiday_status_form` | after `requires_allocation`: `unpaid`, `l10n_vn_si_paid` |

### `views/hr_employee_views.xml` addition (step 3)

`l10n_vn_nursing_break` in the *Payroll* page, after `l10n_vn_union_member`.

### `views/hr_payroll_structure_views.xml` (step 4)

| XML id | Inherits | Content |
|---|---|---|
| `hr_payroll_structure_view_form_l10n_vn_payroll` | `payroll.hr_payroll_structure_view_form` | after `parent_id`: `l10n_vn_payroll` |

### `views/hr_salary_rule_views.xml` (step 4)

| XML id | Inherits | Content |
|---|---|---|
| `hr_salary_rule_view_form_l10n_vn_payroll` | `payroll.hr_salary_rule_view_form` | after `amount_select`: `l10n_vn_component_id`, invisible and not required unless `amount_select == 'l10n_vn_component' or condition_select == 'l10n_vn_component'` |

### `views/hr_payslip_views.xml` (step 4)

| XML id | Inherits | Content |
|---|---|---|
| `hr_payslip_view_form_l10n_vn_payroll` | `payroll.hr_payslip_view_form` | after `contract_id`: `l10n_vn_input_id`, invisible when empty; in the list of `dynamic_filtered_payslip_lines`, before `quantity`, each `optional="hide"`: `l10n_vn_date_from`, `l10n_vn_date_to`, `l10n_vn_days`, `l10n_vn_hours`, `l10n_vn_factor`, `l10n_vn_unit_amount`, `l10n_vn_attainment`, `l10n_vn_period_ref` |

`l10n_vn_context` is on no view: a Json field has no form widget, and the payslip report (step 8) reads it.

### `views/l10n_vn_payroll_damage_views.xml` (step 5)

| XML id | Type | Content |
|---|---|---|
| `l10n_vn_payroll_damage_view_list` | list | `employee_id`, `decision_ref`, `decision_date`, `reason`, `amount`, `deducted`, `balance`, `state`, `company_id` (multi-company group) |
| `l10n_vn_payroll_damage_view_form` | form | `employee_id`, `decision_ref`, `decision_date`, `reason`, `amount`; `deducted`, `balance`, `state`, `company_id`; page *Deductions* with `allocation_ids` read-only (`payslip_id`, `payslip_state`, `amount`); `note` |
| `l10n_vn_payroll_damage_view_search` | search | `employee_id`, `decision_ref`; filter *Open* (`state = open`); group by `employee_id` |
| `l10n_vn_payroll_damage_action` | action | *Damage Decisions*, list, form, default filter *Open* |

### `views/l10n_vn_payroll_input_views.xml` addition (step 5)

`month_scheduled_days` in the form's *Days* group, after `scheduled_days`, read-only unless `figures_locked`.

### `views/menus.xml`

Under `payroll.payroll_menu_configuration` (*Payroll → Configuration*, payroll managers):

| XML id | Name | Action | Sequence |
|---|---|---|---|
| `menu_l10n_vn_payroll_component` | Pay Components | `l10n_vn_payroll_component_action` | 30 |
| `menu_l10n_vn_payroll_scale` | Pay Scales | `l10n_vn_payroll_scale_action` | 31 |
| `menu_l10n_vn_payroll_parameter` | Time Parameters | `base_time_parameter.base_time_parameter_action` | 32 |
| `menu_l10n_vn_payroll_participant_type` (2) | Participant Types | `l10n_vn_payroll_participant_type_action` | 33 |

Under `payroll.payroll_menu_root` (step 3):

| XML id | Name | Action | Sequence | Groups |
|---|---|---|---|---|
| `menu_l10n_vn_payroll_inputs_root` | Monthly Inputs | — | 20 | `payroll.group_payroll_user`, `group_payroll_reader`, `group_payroll_approver` |
| `menu_l10n_vn_payroll_period` | Payroll Periods | `l10n_vn_payroll_period_action` | 1 | the same |
| `menu_l10n_vn_payroll_input` | Monthly Inputs | `l10n_vn_payroll_input_action` | 2 | the same |
| `menu_l10n_vn_payroll_damage` (5) | Damage Decisions | `l10n_vn_payroll_damage_action` | 3 | the same |

## Tests

All classes derive from `PayrollCase(TransactionCase)` in `tests/common.py`, which holds no test methods, and are `@tagged("post_install", "-at_install")`: the fixtures create a company, employees and users, core records later modules extend. No import from any core `tests` package.

**Fixtures** (`setUpClass`): `company` — a new `res.company` with `country_id` `base.vn`, `currency_id` `base.VND`, added to the env's `allowed_company_ids`; `calendar` — the company's `resource_calendar_id`; `department`; `employee` in that company and department; `contract` — `hr.contract` for `employee`, `date_start` 2026-01-01, `wage` 1, `resource_calendar_id` `calendar`, state `open`. Codes are prefixed `TEST_`. **Helpers:** `_component(code, **values)` creates a component in `company` with `kind` `earning`, `legal_nature` `job_salary`, `pit_treatment` `taxable`, `proration` `paid_days`, `amount_source` `line` unless given; `_scale(code, kind, versions)` creates a scale with versions from `{date_from: {key: amount}}`; `_line(component, **values)` creates a pay line on `contract`; `_parameter(code, versions)` creates a float `base.time.parameter` in `company`; `_user(login, groups)` creates an internal user in `company` with the groups' XML ids; `_as(user)` returns an environment for that user whose `allowed_company_ids` is `company` only. Tests act as a user through `_as`, never `with_user`: the fixtures' environment also allows the superuser's companies, which a test user does not belong to, and `with_user` keeps them (step 1, first run).

### `tests/test_component.py` — `TestComponent(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_scale_source_needs_scale` | `amount_source = scale` without `scale_id` raises `ValidationError` |
| `test_engine_needs_code` | `engine` without `engine_code` raises; `line` with an `engine_code` raises |
| `test_ot_needs_category` | `ot` without `ot_category` raises; `ot_category = all` without `amount_parameter` raises |
| `test_earning_needs_treatment` | an earning with source `line` and no `proration` raises; with no `pit_treatment` raises |
| `test_variable_needs_source` | `variable` without `attainment_source` raises; `variable` on a deduction raises |
| `test_exempt_cap_needs_parameter` | `exempt_cap` without `pit_cap_parameter` raises |
| `test_entered_needs_no_proration` | an earning with source `entered` and no `proration` is accepted |
| `test_code_unique_per_company` | a component in another company with the same code is accepted; a second one in `company` raises `IntegrityError` (inside a savepoint) |
| `test_valid_examples` | `BASE` (parameter), `PROD` (scale, variable, supervisor), `PERF` (scale_remainder), `OT_WD` (ot, `WD`), `PIT` (engine) are created without error |

### `tests/test_scale.py` — `TestScale(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_cell_by_date` | versions 2026-01-01 `{S4: 2800000}` and 2027-01-01 `{S4: 3000000}`: 2026-12-31 → 2,800,000; 2027-01-01 → 3,000,000 |
| `test_missing_cell_raises` | key `S9` raises `UserError`; a date before the first version raises `UserError` |
| `test_has_key` | `S4` True; `S9` False |
| `test_unique_version_date` | a second version on the same date raises `IntegrityError` (inside a savepoint) |

### `tests/test_contract_line.py` — `TestContractLine(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_line_inside_contract` | `date_from` before `date_start` raises; with `date_end` set, `date_to` after it raises |
| `test_line_amount_required` | source `line` with no amount raises |
| `test_scale_key_checked` | a `scale` line with key `S9`, absent from the scale, raises |
| `test_no_overlap` | two lines of one component from 2026-01-01 and 2026-06-01, the first open-ended, raise; with the first ended 2026-05-31, accepted |
| `test_one_remainder_per_scale` | two different `scale_remainder` components on one scale, overlapping, raise |
| `test_amounts_by_source` | parameter `TEST.base` 3,700,000: `BASE` line → 3,700,000; `PROD` at `S4` → 2,800,000; `PROD` with `amount` 3,000,000 → 3,000,000 |
| `test_remainder` | grade scale `G2-2` = 8,000,000; `BASE` (parameter 3,700,000, `in_cell`) and `PERF` at `G2-2` → `PERF` 4,300,000; `PERF` with `amount` 45,000,000 (G6) → 41,300,000 |
| `test_wage_follows_lines` | `BASE` with `sets_wage` from 2026-01-01 → `contract.wage` 3,700,000; a new `BASE` line from tomorrow, the old one ended today → still 3,700,000 today; deleting all lines leaves `wage` unchanged |
| `test_wage_safe_without_parameter` | a `sets_wage` component on a parameter code with no parameter: the line is created, `wage` keeps its value, no error |
| `test_contract_shortened_past_lines` | a line to 2026-12-31; setting the contract's `date_end` to 2026-06-30 raises |
| `test_open_line_on_ended_contract` (step 4) | a line without `date_to`; setting the contract's `date_end` to 2026-06-30 is accepted (found by the step 4 cases C02, D07, G08) |

### `tests/test_statutory_parameters.py` — `TestStatutoryParameters(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_created_for_vietnamese_company` | after `_l10n_vn_payroll_ensure_parameters()` on `company`: every code of `STATUTORY_PARAMETERS` exists in `company` with all its versions; `_strict_get("vn.si.reference_level", 2026-06-30, company)` → 2,340,000 and on 2026-07-01 → 2,530,000; `vn.pit.brackets` reads as a list of five pairs |
| `test_idempotent_and_keeps_edits` | after editing the 2026-01-01 version of `vn.rate.ee.si` to `0.09` and running again: no new parameter or version, the value still `0.09` |
| `test_missing_version_added` | after deleting the 2026-07-01 version of `vn.si.reference_level` and running again: it is back with `2530000` |
| `test_not_for_other_countries` | a company with `country_id` `base.fr` gets no `vn.*` parameter |

### `tests/test_security.py` — `TestSecurity(PayrollCase)`

| Test | Asserts |
|---|---|
| `test_new_user_template` | `base.default_user` has neither `payroll.group_payroll_user` nor `payroll.group_payroll_manager` |
| `test_manager_manages_parameters` | `payroll.group_payroll_manager` implies `base_time_parameter.group_time_parameter` |
| `test_officer_sees_all_payslips` | a payslip of `employee`, whose department has a manager who is not the officer: an officer finds it with `search` (OCA's officer rule alone would hide it) |
| `test_hr_user_cannot_read_pay_lines` | a user in `hr_contract.group_hr_contract_manager` without payroll groups reads `contract.name` (positive control) and gets `AccessError` reading `l10n_vn.payroll.contract.line` |
| `test_officer_writes_pay_lines` | an officer creates and edits a pay line (positive), and cannot create a component (`AccessError`) |

### `tests/test_participant_type.py` — `TestParticipantType(PayrollCase)` (step 2)

| Test | Asserts |
|---|---|
| `test_data_records` | the four records exist by XML id with their codes |
| `test_labour` | all six funds, dues allowed, `components`, `min_wage`, `progressive` |
| `test_manager` | no UI, the other five funds; `declared`, `reference_level`, `progressive` |
| `test_probation_and_short` | no fund, no dues, `flat_short` |

### `tests/test_contract_profile.py` — `TestContractProfile(PayrollCase)` (step 2)

| Test | Asserts |
|---|---|
| `test_default_labour` | a new contract gets `participant_labour` |
| `test_manager_needs_declared_base` | switching to `participant_manager` without a declared base raises `ValidationError`; with 10,000,000 it is accepted |
| `test_clause_needs_trial_date` | `clause` without `trial_date_end` raises; with it, accepted |
| `test_hr_user_edits_contract_dates` | a user with contract rights and no payroll role changes `date_end` of a contract with a pay profile without error (D14) |

### `tests/test_employee_payroll.py` — `TestEmployeePayroll(PayrollCase)` (step 2)

| Test | Asserts |
|---|---|
| `test_attendance_mode_follows_pay_group` | `worker` → `scan`; `office` → `exception`; set by hand to `scan` on an office employee, it stays `scan` |
| `test_region_default` | with a string parameter `vn.policy.region` = `IV` in `company`, a new employee of `company` has region `IV`; without the parameter (another company), empty |
| `test_dependent_count` | a child PIT dependent from 2026-03-01 to 2026-08-01, and a parent who is not a PIT dependent: February 0, March 1, August 1, September 0 |
| `test_dependent_dates` | a PIT dependent without `l10n_vn_from` raises; `l10n_vn_from` 2026-03-15 raises; `l10n_vn_to` before `l10n_vn_from` raises |
| `test_hr_user_cannot_read_pay_fields` | a user with HR rights and no payroll role reads the employee's `name` (positive control) and gets `AccessError` reading `l10n_vn_pay_group` through `read` |
| `test_officer_registers_dependent` | an officer creates a relative with `relation_id` `hr_employee_relative.relation_child` and the PIT fields (D18) |

### `tests/test_pit_method.py` — `TestPitMethod(PayrollCase)` (step 2)

| Test | Asserts |
|---|---|
| `test_labour_open_ended` | `progressive` |
| `test_non_resident` | `l10n_vn_resident` False → `flat_nonresident` |
| `test_short_contract` | `date_end` 2 months after `date_start` → `flat_short`; with `l10n_vn_pit_commitment_year` = that year → `progressive`; the previous year → `flat_short` |
| `test_three_months_is_not_short` | 2026-01-01 to 2026-03-31 → `progressive` |
| `test_probation_type` | `participant_probation` on an open-ended contract → `flat_short` |

### `tests/test_input_build.py` — `TestInputBuild(PayrollCase)` (step 3)

`TestInputBuild(InputCase)`; `InputCase(PayrollCase)` in `tests/input_common.py`, shared with `test_input_workflow`. **Fixtures:** a calendar, Monday–Saturday 07:00–11:00, lunch 11:00–12:00, 12:00–16:00 (8 hours a day), time zone `Asia/Ho_Chi_Minh`, on the employee and the contract; the parameter `vn.policy.ot_min_hours_day` = 0.8; a period for October 2026: 27 scheduled days (31 less 4 Sundays), one of them a public holiday, 2026-10-20, as a calendar leave with no resource. **Helpers:** `_attend(day, start, end)` creates an `hr.attendance` from local times; `_leave(leave_type, first, last)` creates and validates an `hr.leave`; `_build()` builds the period and returns the employee's input.

| Test | Asserts |
|---|---|
| `test_full_month` | attendance 07:00–16:00 on every scheduled day but the holiday: 27 scheduled days, 26 days worked, the holiday as 1 company leave day, 27 paid days, 0 unpaid, 0 SI absence days, no OT |
| `test_early_arrival_and_short_overtime` | one day 06:30–16:30 (core's overtime 1 h in total): its OT is 1 h when early check-ins are not trimmed; trimmed to 07:00–16:30, overtime 0.5 h is below 0.8 and dropped. Days worked unaffected |
| `test_overtime_categories` | 07:00–18:00 on a workday (`WD` 2), 07:00–11:00 on a Sunday (`RD` 4), 07:00–10:00 on the holiday (`HOL` 3) |
| `test_absence_and_unpaid_leave` | full days except two scheduled days without attendance and one approved day of an `unpaid` type: 2 unexcused absences, 3 unpaid days, 24 paid days |
| `test_si_paid_leave` | 15 days of an `l10n_vn_si_paid` type, full days otherwise: SI leave days 15, 11 days worked, 12 paid days (with the holiday), `si_absence_days` 15 |
| `test_paid_leave` | 2 days of a company-paid type, full days otherwise: 3 company leave days (with the holiday), 27 paid days |
| `test_nursing_break` | `l10n_vn_nursing_break`, a child born 2026-03-10; working 07:00–15:00 on every scheduled day but the holiday: 26 h credited, 27 paid days |
| `test_nursing_break_child_over_one` | the same with a child born 2025-09-01 (first birthday before October): no credit, 23.75 paid days |
| `test_menstruation_days` | working 07:00–15:30 on 3 days, full days otherwise, `menstruation_days` 3: 1.5 h credited; with 5 days entered, still 1.5 h (no shortfall left) |
| `test_segments` | a contract ending 2026-10-14 and a new one from 2026-10-15: two segments with their own paid days, summing to the input's |
| `test_locked_kept` | `figures_locked`, `paid_days` set by hand to 20: a rebuild keeps 20 |
| `test_calendar_hours_per_day_ignored` | the calendar's `hours_per_day` set to 16: days worked unchanged (D23) |
| `test_ot_hours_ytd` | a September input with 12 h of OT: October's `ot_hours_ytd` is 12 |
| `test_zero_figures_stored` (3.1) | no attendance in October: read through SQL, `days_worked`, `unpaid_leave_days` and `paid_break_hours` are 0, not NULL, and `unexcused_absences` 26 |

### `tests/test_input_workflow.py` — `TestInputWorkflow(InputCase)` (step 3)

| Test | Asserts |
|---|---|
| `test_close_freezes_figures` | after `action_close_attendance`, writing `paid_days` raises `UserError`; writing `attainment` succeeds; `action_build` raises |
| `test_reopen_managers_only` | an officer's `action_reopen_attendance` raises `AccessError`; a manager's reopens |
| `test_override_needs_note` | `attainment_source` `override` without `attainment_note` raises `ValidationError` |
| `test_line_rules` | a line of a `line` component without `period_ref` raises; with `period_ref` the month after the period raises |
| `test_approval` | an officer's `action_approve` raises `AccessError` (positive control: the officer edits the amount); an approver's sets `approved_by`; writing the amount clears it |
| `test_one_input_per_employee` | a second input for the same period and employee raises `IntegrityError` (inside a savepoint) |

### `tests/payslip_common.py` — `PayslipCase(PayrollCase)` (step 4)

Holds no test methods; shared by the step 4 and step 5 files. October 2026, 26 standard days. Expected acceptance figures are never typed: they come from `tests/data/acceptance_cases.json` (`CASES_FILE`; `acceptance_earnings.json` in step 4).

**Fixtures** (`setUpClass`):

| Fixture | Content |
|---|---|
| Parameters | `company._l10n_vn_payroll_ensure_parameters()` (`vn.ot.factors` among them); with `_parameter`, from 2026-01-01: `vn.policy.std_days` 26, `vn.policy.probation_rate` 0.85, `vn.policy.attainment_cap` 1, `vn.policy.unit_rate` 1500, `vn.policy.attendance_late_max` 2, `vn.policy.base_salary` 3700000, `vn.policy.ot_supplement` 3846, `vn.policy.ot_min_hours_day` 0.8 |
| Scales | `PROD` (`level`): Entry 800,000, S1 1,300,000, S2 1,800,000, S3 2,300,000, S4 2,800,000; `GRADE` (`grade_step`): G2-2 8,000,000, G3-2 10,000,000; versions from 2026-01-01 |
| Components, current scheme | `BASE`: parameter `vn.policy.base_salary`, `in_si_base`, `in_ot_base`, `probation_applies`, `sets_wage`, `paid_days`; `PROD`: scale `PROD`, `variable_salary`, `variable`, `supervisor`, `in_ot_base`, `probation_applies`, `paid_days`; `PERF`: scale_remainder `GRADE`, the same with `manager` |
| Components, reference configuration | `SAL`: line, `in_si_base`, `in_ot_base`, `probation_applies`, `paid_days`; `SKILL`: line, `fixed_allowance`, `in_si_base`, `in_ot_base`, `paid_days`; `ATT`: line, `bonus`, `condition` `attendance`, `none`; `TRAVEL`: line, `welfare`, `none`; `DAILY`: line, `in_si_base`, `in_ot_base`, `per_day`; `INC`: `ie_units`, `bonus` |
| Components, both | `EFF`, `ONE`: entered, `bonus`; `OT_WD`, `OT_RD`, `OT_HOL`: `ot` with that category, `overtime`, PIT `ot`; `SUPP`: `ot`, category `all`, `amount_parameter` `vn.policy.ot_supplement`, `overtime`, PIT `ot`, **archived**; `GROSS`: engine `GROSS`, kind `total`, `total`, section `total` |
| Categories | `hr.salary.rule.category` `TEST_EARN` and `TEST_TOTAL` |
| Structure | `structure`: `hr.payroll.structure` *TEST VN*, code `TEST_VN`, in `company`, `l10n_vn_payroll`; one rule per component above, in that order (sequence 10, 20 …), in `company`, code and name of the component, `amount_select` and `condition_select` `l10n_vn_component`, `l10n_vn_component_id`, category `TEST_TOTAL` for `GROSS` and `TEST_EARN` for the rest |
| Contract and period | `contract.struct_id` = `structure`; `period` for October 2026 in `company` |

**Helpers:**

| Helper | Does |
|---|---|
| `_hire(lines=(), date_start=2026-01-01, date_end=None, state="open", employee=None, **values)` | a new employee in `company` (unless given) and a contract with `structure` and `calendar`; `lines` is a list of `(component, values)` created with `_line` from `date_start` unless the values give `date_from`; returns `(employee, contract)` |
| `_input(employee, segments=(), lines=(), **figures)` | an input of `period` with `figures_locked` and the figures given (by default `scheduled_days`, `paid_days`, `days_worked` 26); `segments` a list of segment values; `lines` a list of `(component, values)`, approved (`approved_by`, `approved_at` written as superuser) unless the values say `approved=False` |
| `_payslip(employee)` | as OCA's batch does: `hr.payslip.get_payslip_vals(2026-10-01, 2026-10-31, employee.id)`; creates the payslip with its `contract_id`, `struct_id`, worked days and `company_id`; `compute_sheet()`; returns it |
| `_totals(payslip, code)` | the `total` of the payslip's lines of that code, in id order |
| `_expect(payslip, case, codes)` | the case's `earnings` rows zipped with `codes` (strict); a row whose code is `None` must be 0 and has no line; the payslip's line totals per code equal the case's amounts for that code, in order; no earning line (component kind `earning`) has another code (step 5: the deduction, employer and total lines are `_expect_pay`'s); `GROSS` equals the case's `gross` |

**Step 5 additions to `PayslipCase`:**

| Fixture or helper | Content |
|---|---|
| Components | `KPI`, `ANNUAL`: entered, `bonus`; `LEAVE`: entered, `leave_pay`, PIT `exempt`; `PHONE`: line, `welfare`, PIT `exempt`, `none`; `MEAL`: line, `welfare`, PIT `exempt_cap` with `vn.pit.meal_cap`, `none`; engine components, kind `deduction` and section `deduction`: `EE_SI`, `EE_HI`, `EE_UI` (`statutory`), `DUES` (`union`), `PIT` (`statutory`), `DAMAGE` (`damage`); kind `employer` and section `employer`, `statutory`: `ER_PENSION`, `ER_SICKNESS`, `ER_ACCIDENT`, `ER_HI`, `ER_UI`, `UNION_FEE`; kind `total`: `NET`, `TO_PAY`; kind `info`, `advance`: `ADVANCE` |
| Categories and rules | `TEST_DED` for the deductions, `TEST_ER` for the employer lines; one rule per new component, after `GROSS` in the order of D58 |
| `_hire` | also sets the employee's `l10n_vn_region` to `IV`; new contracts take the `LABOUR` participant type by default (D13) |
| `_input` | also defaults `month_scheduled_days` to 26 |
| `_dependents(employee, count, date_from=2026-01-01)` | `count` relatives with relation child, `l10n_vn_pit_dependent`, `l10n_vn_from` = `date_from` |
| `_damage(employee, amount, date=2026-10-01)` | a damage decision |
| `_expect_pay(payslip, case, advances=True)` | per engine code, the payslip's totals equal the case: `EE_SI`, `EE_HI`, `EE_UI`, `DUES` = [−figure] when not 0, else no line; `PIT` = [−`pit`] (a line of 0 when there is none); `DAMAGE` = [−`damage`] when not 0; `NET` = [`net`]; employer lines = [figure] when not 0, else no line; the snapshot's `contributions.base` = `si_base` (null when not liable), `pit.method`, and for progressive `pit.exempt` = `exempt` and `pit.taxable` = `taxable`; with `advances`, `TO_PAY` = [`to_pay`] |

### `tests/data/acceptance_cases.json` (step 4 as `acceptance_earnings.json`, step 5)

Generated by `docs/HR-Contract-Payroll/payroll_reference_calc.py` with its `--json` option, never edited: for every case, `earnings` (its earning rows as `[label, amount]`, in the case's order), `gross`, `si_base`, `ee_si`, `ee_hi`, `ee_ui`, `dues`, `pit_method`, `exempt`, `taxable`, `pit`, `damage`, `net`, `settled`, `to_pay`, and `employer` (`pension`, `sickness`, `accident`, `hi`, `ui`, `union_fee`).

### `tests/test_payslip_contract.py` — `TestPayslipContract(PayslipCase)` (step 4)

| Test | Asserts |
|---|---|
| `test_main_contract_latest` | a contract ended 2026-10-14 (`close`) and the next from 2026-10-15: the payslip's contract is the second, and it has one `GROSS` line |
| `test_leaver_closed_contract` | the only contract, `close`, ended 2026-10-20: `get_payslip_vals` returns it, while core's `_get_contracts` finds none |
| `test_form_without_contract` | a payslip created with the employee, the dates and `structure` only: `compute_sheet` sets the main contract |
| `test_worked_days_from_input` | a summary with paid 24, worked 22, unpaid 2 and `leave_days_json` `{"Annual leave": 2}`: worked days `PAID` 24, `WORKED` 22, `UNPAID` 2, `LEAVE` *Annual leave* 2; no `WORK100` |
| `test_worked_days_refreshed` | the summary's paid days changed after the payslip was created: `compute_sheet` writes the new `PAID` |
| `test_other_structure_untouched` | a contract whose structure lacks `l10n_vn_payroll`: `get_payslip_vals` keeps OCA's contract and a `WORK100` line; `compute_sheet` writes no `l10n_vn_context` |
| `test_month_only` | a payslip from 2026-10-05 to 2026-10-31: `UserError` |
| `test_no_input` | no summary: `UserError` naming the employee |

### `tests/test_pay_context.py` — `TestPayContext(PayslipCase)` (step 4)

| Test | Asserts |
|---|---|
| `test_pieces` | a contract from 2026-01-01 with a clause ending 2026-10-07, and a `SAL` line of 4,500,000 ended 2026-10-14 followed by one of 5,000,000 from 2026-10-15: pieces 10-01–10-07 (probation), 10-08–10-14, 10-15–10-31 |
| `test_pieces_gap` | a contract ended 2026-10-10 and the next from 2026-10-20: pieces 10-01–10-10 and 10-20–10-31; building the summary gives two segments with those dates (step 3's cut dates failed here, on a piece with no days) |
| `test_missing_segments` | the `SAL` change of `test_pieces` without the clause, a summary without segments: `UserError` naming 2026-10-01–2026-10-14 and 2026-10-15–2026-10-31 |
| `test_bases` | four `line` components of 2,600,000 (`paid_days`, `days_worked`), 300,000 (`none`) and 100,000 (`per_day`), paid 24, worked 22: lines 2,400,000, 2,200,000, 300,000, 2,400,000 |
| `test_none_paid_once` | `TRAVEL` 200,000 across the two pieces of the `SAL` change: one `TRAVEL` line of 200,000, without dates |
| `test_missing_attainment` | a `PROD` line and no attainment source: `UserError`; with source `supervisor` and attainment 0: a `PROD` line of 0 |
| `test_attainment_cap` | attainment 1.2: `PROD` at Entry pays 800,000 |
| `test_attendance_condition` | `ATT` 300,000: 3 late arrivals → 0; 2 late arrivals and no absence → 300,000; one unexcused absence → 0 |
| `test_unapproved_not_paid` | an `EFF` input line without approver: no `EFF` line, and its id in the snapshot's `unapproved`; once approved and recomputed, a line |
| `test_ot_without_component` | 4 `HOL` hours with `OT_HOL` archived: `UserError` naming `HOL` |
| `test_ot_last_piece` | the `SAL` change, segments matching the pieces without hours, the summary's `WD` 10: one `OT_WD` line, round(5,000,000 ÷ 208 × 1.5 × 10) computed in the test with `Decimal` |
| `test_component_without_rule` | an entered component with an approved line and no rule in `structure`: `UserError` naming it |
| `test_snapshot_replaced` | after a calculation, the summary's paid days changed and the payslip recalculated: the snapshot's `input.paid_days` is the new value and the lines exist once |
| `test_exact_lines` | on a G01 payslip: every `l10n_vn_component` line has quantity 1, rate 100 and `total` = `amount`, a whole number; `GROSS` = the sum of the earning lines |
| `test_split_names` | the C06 payslip: two `SAL` lines named *SAL (01/10–07/10, probation)* and *SAL (08/10–31/10)*, with `l10n_vn_date_from`, `l10n_vn_date_to` and `l10n_vn_days` 6 and 20 |
| `test_other_rule_rounded` | a `code` rule in `structure` after `GROSS`, `result = payroll.vn["gross"] + 0.5`: its line has quantity 1, rate 100 and total = gross + 1 |

### `tests/test_acceptance.py` — `TestAcceptance(PayslipCase)` (step 4 as `test_acceptance_earnings.py` / `TestAcceptanceEarnings`, step 5)

One test per case, `test_<case>`, asserting with `_expect`. Inputs not given are 0; attainment source `supervisor` for `PROD`, `manager` for `PERF`; entered lines approved; `BASE` lines have `in_cell`, so `PERF` is the cell less the base. *As A02* means `SAL` 4,500,000, `SKILL` 1,500,000, `ATT` 300,000, `TRAVEL` 200,000.

| Case | Contract | Pay lines | Summary | Codes |
|---|---|---|---|---|
| G01 | from 2026-01-01 | `BASE`; `PROD` Entry | OT `WD` 20; attainment 1; `EFF` 300,000 | `BASE`, `PROD`, `OT_WD`, `EFF` |
| G02 | | `BASE`; `PROD` S4 | OT `WD` 30; attainment 1; `EFF` 1,000,000 | the same |
| G03 | | `BASE`; `PROD` S4 | OT `WD` 30; attainment 0.8 | `BASE`, `PROD`, `OT_WD`, None |
| G04 | | `BASE`; `PROD` Entry | paid and worked 24, 2 unexcused absences; OT `WD` 20; attainment 1; `EFF` 300,000 | `BASE`, `PROD`, `OT_WD`, `EFF` |
| G07 | | as G01 | as G01, and `ONE` 500,000 | `BASE`, `PROD`, `OT_WD`, `EFF`, `ONE` |
| G08 | 2026-01-01 to 2026-10-24, `close` | `BASE`; `PROD` Entry | paid and worked 20; attainment 1; `EFF` 200,000 | `BASE`, `PROD`, `EFF` |
| G10 | | `BASE`; `PERF` G2-2 | OT `WD` 30; attainment 1 | `BASE`, `PERF`, `OT_WD` |
| G11 | | `BASE`; `PERF` G2-2 | OT `WD` 30; attainment 0.8 | the same |
| G12 | | `BASE`; `PERF` G3-2 | OT `WD` 16; attainment 1 | the same |
| G13 | | `BASE`; `PERF` with amount 45,000,000 | attainment 1 | `BASE`, `PERF` |
| A01 | | `SAL` 4,500,000; `ATT`; `TRAVEL` | OT `WD` 20; IE units 200 | `SAL`, `OT_WD`, `INC`, `ATT`, `TRAVEL` |
| A02 | | as A02 | OT `WD` 30; IE units 1,000 | `SAL`, `SKILL`, `OT_WD`, `INC`, `ATT`, `TRAVEL` |
| B01 | | as A02 | OT `WD` 36, `RD` 16; IE units 1,200 | `SAL`, `SKILL`, `OT_WD`, `OT_RD`, `INC`, `ATT`, `TRAVEL` |
| B02 | | as A02 | paid and worked 25, 1 unexcused absence; OT `WD` 20; IE units 900 | `SAL`, `SKILL`, `OT_WD`, `INC`, `ATT`, `TRAVEL` |
| C02 | a probation contract 2026-09-21 to 2026-10-12, `close`, form `contract`, participant `PROBATION`; then a labour contract from 2026-10-13 | `SAL` 4,500,000 on each; `ATT`, `TRAVEL` on the labour contract | segments 10-01–10-12 (paid 10) and 10-13–10-31 (paid 16); IE units 300 | `SAL`, `SAL`, `INC`, `ATT`, `TRAVEL` |
| C06 | from 2026-10-01, form `clause`, `trial_date_end` 2026-10-07 | `SAL` 4,500,000; `ATT`; `TRAVEL` | segments 10-01–10-07 (paid 6) and 10-08–10-31 (paid 20) | `SAL`, `SAL`, `ATT`, `TRAVEL` |
| D07 | 2026-10-01 to 2026-11-30 | `DAILY` 350,000 | paid 26 | `DAILY` |
| D08 | | as A02 | OT `WD` 30; IE units 1,000; `SUPP` unarchived | `SAL`, `SKILL`, `OT_WD`, `SUPP`, `INC`, `ATT`, `TRAVEL` |
| E01 | | as A02 | OT `WD` 20; IE units 1,000; an `OT_WD` line with `period_ref` 2026-09-01, hours 4, the case's last row as amount, description *OT workday 4 h* | `SAL`, `SKILL`, `OT_WD`, `INC`, `ATT`, `TRAVEL`, `OT_WD` |

**Step 5:** every test above also calls `_expect_pay`, except that G14 and G15 pass `advances=False` (their advances come with `l10n_vn_payroll_account`). G08 adds a damage decision of 300,000; G10 and G11 add 1 dependent, G13 2; A01's employee is a union member. The cases added in step 5, each with `_expect` and `_expect_pay`; reference configuration unless the pay lines say `BASE`:

| Case | Contract and people | Pay lines | Summary | Codes |
|---|---|---|---|---|
| A03 | 1 dependent | `SAL` 8,000,000 | OT `WD` 30 | `SAL`, `OT_WD` |
| A04 | | `SAL` 10,000,000 | OT `WD` 16; `KPI` 1,000,000 | `SAL`, `OT_WD`, `KPI` |
| A05 | | `SAL` 14,000,000; `PHONE` 200,000 | OT `WD` 8; `KPI` 1,500,000 | `SAL`, `OT_WD`, `KPI`, `PHONE` |
| A06 | 1 dependent | `SAL` 17,000,000; `PHONE` 500,000 | `KPI` 3,000,000 | `SAL`, `KPI`, `PHONE` |
| A07 | | `SAL` 18,000,000; `PHONE` 300,000 | `KPI` 2,000,000 | the same |
| A08 | 2 dependents | `SAL` 45,000,000; `PHONE` 1,000,000 | `KPI` 8,000,000 | the same |
| A09 | 1 dependent | `SAL` 70,000,000; `PHONE` 2,000,000 | `KPI` 15,000,000 | the same |
| B06 | | `SAL` 10,000,000 | paid and worked 24, unpaid 2 | `SAL` |
| C01 | from 2026-10-15 to 2026-11-13, form `contract`, participant `PROBATION` | `SAL` 4,500,000; `TRAVEL` 200,000 | paid and worked 13 | `SAL`, `TRAVEL` |
| C03 | to 2026-10-22, `close` | `SAL` 4,500,000; `SKILL` 1,500,000; `TRAVEL` 200,000 | paid and worked 18; IE units 600; `LEAVE` with the case's row as amount | `SAL`, `SKILL`, `INC`, `LEAVE`, `TRAVEL` |
| C04 | | `SAL` 4,500,000; `SKILL` 1,500,000 | paid and worked 0, SI leave 26 | earnings not asserted (one row for two lines of 0) |
| C05 | | as A02 | paid and worked 11, SI leave 15; IE units 300 | `SAL`, `SKILL`, `INC`, `ATT`, `TRAVEL` |
| D01 | | `SAL` 80,000,000 | | `SAL` |
| D02 | 2026-10-01 to 2026-11-30 | `SAL` 6,000,000 | | `SAL` |
| D03 | | `SAL` 10,000,000; `MEAL` 1,500,000 | | `SAL`, `MEAL` |
| D04 | | `SAL` 10,000,000 | `ANNUAL` 10,000,000 | `SAL`, `ANNUAL` |
| D05 | 1 dependent from 2026-10-01 | as A07 | as A07 | as A07 |
| D06 | participant `MANAGER`, declared SI base 10,000,000 | `SAL` 40,000,000 | | `SAL` |
| E02 | a damage decision of 3,000,000 | as A02 | OT `WD` 20; IE units 1,000 | `SAL`, `SKILL`, `OT_WD`, `INC`, `ATT`, `TRAVEL` |
| G05 | | `BASE`; `PROD` Entry | worked 24, paid 26; OT `WD` 20; attainment 1; `EFF` 300,000 | `BASE`, `PROD`, `OT_WD`, `EFF` |
| G06 | | `BASE`; `PROD` S2 | attainment 1 | `BASE`, `PROD` |
| G14 | | as G01 | as G01 | as G01; `advances=False` |
| G15 | | `BASE`; `PROD` Entry | paid and worked 10, unpaid 16; attainment 1 | `BASE`, `PROD`; `advances=False` |

Not run: B04 (night hours are not computed, divergence 11), B05 (blocked on late minutes, Attendance OPEN-04), C04's earnings, and the advances of G14 and G15.

### `tests/test_contributions.py` — `TestContributions(PayslipCase)` (step 5)

| Test | Asserts |
|---|---|
| `test_floor` | `SAL` 3,000,000 in the SI base: the base is 3,700,000 (region IV) and `EE_SI` −296,000 |
| `test_base_on_last_day` | a contract ended 2026-10-24 with `SAL` 4,500,000, paid 20: the base is 4,500,000 |
| `test_leaver_not_liable` | a contract ended 2026-10-10, paid 8, `month_scheduled_days` 26: no contribution line; the snapshot has `liable` false and `days_without_si` 18 |
| `test_hire_liable` | a contract from 2026-10-13, paid 14: 12 days without SI, contributions calculated |
| `test_dues_cap` | a union member on `SAL` 80,000,000: `DUES` −253,000 |
| `test_no_participant_type` | the contract's participant type emptied: `UserError` naming the contract |
| `test_no_region` | the employee's region emptied: `UserError` naming the employee |
| `test_month_days_missing` | `month_scheduled_days` 0: `UserError` asking for a rebuild |
| `test_month_scheduled_days_built` | a contract ended 2026-10-10 on a Monday–Friday calendar of the test's own (a new company copies the current company's calendar, Monday–Saturday on the instance): the built summary has `scheduled_days` 7 and `month_scheduled_days` 22 |
| `test_missing_engine_component` | `NET` archived: `UserError` naming `NET` |

### `tests/test_pit.py` — `TestPit(PayslipCase)` (step 5)

| Test | Asserts |
|---|---|
| `test_year_limit` | `ot_hours_ytd` 290 and `WD` 20 h: the OT exemption is round(OT pay × 10 ÷ 20) |
| `test_adjustment_own_month` | an `OT_WD` adjustment for September with 4 h: with a September summary of 38 OT h, half of it is exempt; with no September summary, all of it; without hours, none |
| `test_exempt_cap_shared` | `MEAL` 1,000,000 and a second line component with the same cap parameter, 500,000: *E* includes 1,200,000 |
| `test_non_resident` | `l10n_vn_resident` false, 1 dependent, `SAL` 10,000,000: `PIT` −2,000,000 and no dependent deduction |
| `test_negative_taxable` | `SAL` 4,500,000: a `PIT` line of 0 and a negative `pit.taxable` in the snapshot |
| `test_deduction_entered_positive` | an entered deduction component, 100,000 entered: its line is −100,000 and `NET` falls by 100,000 |

### `tests/test_damage.py` — `TestDamage(PayslipCase)` (step 5)

| Test | Asserts |
|---|---|
| `test_carry_forward` | the E02 payslip set to `done`: the decision's `deducted` 2,470,616, `balance` 529,384, `open`; a second payslip of the employee takes 529,384; once it is `done`, the decision is `done` |
| `test_oldest_first` | decisions of 300,000 (2026-09-01) and 2,000,000 (2026-10-01), `SAL` 4,500,000: cap 1,208,250; allocations 300,000 and 908,250 |
| `test_later_decision_waits` | a decision dated 2026-11-05: no `DAMAGE` line in October |
| `test_recompute_replaces` | two calculations of one payslip: one allocation |
| `test_cannot_delete_deducted` | a decision with a `done` allocation: `unlink` raises `UserError` |
| `test_access` | an officer creates a decision (positive control); a reader's `create` raises `AccessError` |

## Readme

| File | Content |
|---|---|
| `readme/DESCRIPTION.md` | Vietnamese payroll on OCA payroll; step 5 adds the rest of the payslip: social, health and unemployment insurance by fund with the 14-day rule, the union fee and dues, PIT (progressive with OT and capped exemptions, or flat), damage compensation decisions deducted within the legal cap, net pay and the amount to pay after advances; step 4 adds the calculation of earnings: the pay context computed per payslip from pay lines, the monthly input and parameters, with probation, attainment and OT, shown as exact payslip lines through the *Pay Component* rule type, and kept as a snapshot; step 2 adds participant types, the contract's pay profile and PIT method, the employee's payroll fields and PIT dependents; step 1: pay components with their SI, OT and PIT treatment and amount sources, salary and productivity scales with dated versions, dated pay lines on contracts that keep the contract wage in step, the payroll roles, and the statutory parameters created for Vietnamese companies |
| `readme/USAGE.md` | *Payroll → Configuration → Pay Components, Pay Scales, Time Parameters*; the *Pay Lines* page on a contract: a change is a new line from its date, the old one ended the day before; what each amount source expects on a line; the roles (Officer, Reviewer, Approver, Reader, Manager) and that new users receive no payroll role; step 2: *Participant Types*, the contract's *Pay Lines* page heading (participant type, declared SI base, probation), the employee's *Payroll* page, dependents on the *Relatives* page (registered from and to the first day of a month); step 4: a structure marked *Vietnamese Pay Context* with one *Pay Component* rule per component; a payslip of such a structure covers one month, takes the latest contract of the month, reads the month's input, and shows one line per pay line and piece, with dates, days, hours and rates in the optional columns; step 5: the structure also needs the engine components (insurance, dues, PIT, damage, net, to pay, employer funds); contracts need a participant type and employees a region; *Monthly Inputs → Damage Decisions* records work-rules decisions, deducted oldest first within the 30% cap |
