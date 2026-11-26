# Payroll and Contract Documents — Technical Review

2026-11-26 · @Peter

The modules reviewed are `base_time_parameter_strict`, `hr_attendance_day`, `l10n_vn_payroll`,
`l10n_vn_payroll_garment`, `l10n_vn_payroll_payment`, `l10n_vn_payroll_account` and
`l10n_vn_hr_contract_document`, at 68 + 363 tests, all passing. The question is whether they work for
go-live. Each finding is weighed by its value against what fixing it costs, not by completeness (Peter,
2026-11-26). Checks were made against the code, the views and the test copy's database.

## 1. Verified

| Check | Result |
|---|---|
| Every model has access rules | Yes, all models of the seven modules |
| Every model with company data has a company rule | Yes, 25 models (the trading company shares the database) |
| Every field a constraint or check requires is on a form | Yes. The one gap, the trial end of a probation clause, was fixed in engine step 12.1 |
| Posting happens once per run, even with accounts on a salary rule | Yes. OCA `payroll_account` posts a payslip at confirmation only from accounts on its salary rules (`oca/payroll/payroll_account/models/hr_payslip.py`, the move is created only when lines have accounts); our rules carry none, since accounts sit on the components. An account typed on a rule is caught when the run is calculated: the `posting` check reports *no OCA account on salary rule …* as an error, which blocks review and so approval (`l10n_vn_payroll_account/models/hr_payslip.py:67-73`, its D8, D9). This was first listed as finding B3; a constraint added for it was reverted the same day as a second guard for one risk |
| A run's calculation fits the server's limits | `limit_time_real` 720 s and `limit_time_cpu` 600 s per request; about 235 payslips in one request is within reach. The rehearsal measures it |

## 2. Fix before go-live

Both have high value and a small cost.

| # | Finding | Fix | Cost |
|---|---|---|---|
| A1 | **Pay is readable outside payroll through contract versions.** A version's snapshot holds the salary terms, and versions are readable by contract administrators (`hr_contract.group_hr_contract_manager`) as well as payroll users. On the test copy, one of the six contract administrators has no payroll rights. Approval is also open to contract administrators without payroll rights, who approve terms they cannot see. | Versions readable by payroll users only; *Approve*, *Amend*, the amendment actions, *Annexes for a Date* and *Next Contract* need contract administration **and** payroll rights | One access line removed, one group check and the button groups, two tests adjusted |
| A2 | ***Annexes for a Date* can list a contract not in force on the date**, which *Confirm* then fails on, and an empty result gives no feedback (found in the UI check) | Consider only contracts in force on the date; say so when nothing changes | A few lines and one test |

## 3. Configuration, no code

| # | Finding | Action |
|---|---|---|
| B1 | **Core's new-user template grants contract administration** (`hr_contract/security/security.xml`, `base.default_user`), so every new internal user can open contracts; 6 of the 10 active internal users have it on the test copy | On production: remove *Contracts: Administrator* from *Default User Template*, and review the users who have it. A go-live checklist line, not a module: production is set up once |
| B2 | **The test copy's `BASE` is the pre-step-6 version** reading `vn.policy.base_salary`, so UI checks there do not show production's scale-based salary (seen in the step 3 UI check) | None: the October rehearsal on a freshly restored `prod_copy` loads the current scheme |

## 4. Leave as is

Low value against their cost: each would add code for a case that does no harm.

| # | Finding | Why it stays |
|---|---|---|
| C1 | `wage` is editable on a contract not yet approved | Payroll never reads it, and the next pay-line change rewrites it; it is read-only once approved (contract documents D37) |
| C2 | A pay line's amount can be typed for a component whose amount comes from a parameter, and is ignored | In the garment scheme no parameter-based component sits on pay lines once `BASE` comes from the scale (garment step 6) |
| C3 | Our access lines call core's line-manager contract group "officer" | A name in a CSV; no behaviour |

## 5. Left to the October rehearsal

These cannot be settled by reading code: a run's time on about 235 real payslips, the monthly summaries built from real November attendance, posting against the real chart, the transfer file at the bank, and the UI as the payroll officer, reviewer, approver and accountant.
