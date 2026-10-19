# IE Module: Roadmap to Development

**Status:** reference for future sessions · created 2026-10-18
**Purpose:** the major steps the IE module project must complete before actual Odoo module development starts. Read this together with the current document set.

## Current document set

| File | Role |
|------|------|
| `IE_Business_Logic_Spec_v0.6.md` | Business rules of record (DEC-01 to DEC-24, OPEN items, FLAG-TECH items) |
| `IE_Framework_Rationale_v0.6.md` | Explanation with worked numbers, for human review |
| `IE_Module_Function_Map.md` (v0.8) | v1 scope index, document set and workflow |
| `IE_Acceptance_Test_Cases_v0.3.md` | Expected results per case, with priorities P1 to P3 |
| `ie_reference_calc.py` | Reference calculator; checks the calculated cases and the document |
| `Archive/` | Superseded versions (spec and rationale v0.1 to v0.5, test cases v0.1 to v0.2, IE Design.md) |

## Where the project stands

- Business logic baseline reached on 2026-10-18.
- Function map trimmed to v1. Costing (area 3) is deferred; the self-funding check stays in v1.
- Context: Odoo CE 18 on Docker/VPS; timeSSD for SAM; existing Maintenance/CMMS setup; payroll is handled by a separate payroll module.

## Steps to development

| # | Step | Status |
|---|------|--------|
| 1 | Acceptance test cases | Done (v0.3); assumptions resolved |
| 2 | Settle or park remaining open items | In progress |
| 3 | Fit-gap against Odoo CE 18 | Not started |
| 4 | Integration inventory with real sample data | Not started |
| 5 | Prototype the riskiest assumption | Not started |
| 6 | Technical design spec | Not started |
| 7 | Module breakdown and build order | Not started |
| 8 | Development environment | Not started |

### 1. Acceptance test cases
- Turn the spec into concrete scenarios with expected numbers: normal month, ramp days, learner (PF and PF_cap), defects and repair, mid-bundle reassignment, off-standard channels, time-category split, tier multiplier, skill level changes.
- A small reference calculator (Python) produces the "golden" results.
- This is the last business-side step. It also becomes the developer's pass/fail check for every pay calculation.
- Outputs: `IE_Acceptance_Test_Cases_v0.3.md` and `ie_reference_calc.py` (test data held in the calculator; no separate CSV files).

### 2. Settle or park remaining open items
- Review the open items in spec §15 (OPEN-04 to 07, 11 to 15).
- Decide which change the data model and must be answered now, e.g. OPEN-15 (clipping bundle time to attendance) and OPEN-12 (shadow-mode pay and switch-on checks).
- The rest stay as parameters or go to later versions.
- Status 2026-10-18: OPEN-04, 05, 06 and 13 closed (spec v0.5, DEC-22 to 24). OPEN-15 restated as two options, decided during technical design (step 6). OPEN-12 (shadow-mode design) open until before shadow mode. OPEN-01, 07, 10 and 11 deferred by design.

### 3. Fit-gap against Odoo CE 18
- For each function-map item: standard Odoo, existing OCA or own module, or new build.
- Key gaps to settle:
  - CE has no Quality module and no Payroll module. Decide which modules IE receives defects from and sends figures to.
  - How IE works with the existing Maintenance/CMMS setup (breakdown call RT-3, OS-01 minutes).
  - Attendance arriving as `hr.attendance` records.

### 4. Integration inventory with real sample data
- Collect actual exports:
  - timeSSD operation bulletins;
  - attendance data from the devices;
  - a sample of MOs and work orders;
  - the format the payroll side expects.
- Confirm that the fields the spec assumes really exist, especially library operation codes and SAM versions.

### 5. Prototype the riskiest assumption
- One MO per bundle means thousands of MOs and work orders per month.
- Test in a staging copy before committing to the design:
  - Odoo 18 performance at that volume;
  - the scanning and pausing experience on the shop floor;
  - how easily work-order pauses can carry reason codes.
- If this fails, parts of the design change, so it comes before the technical spec.

### 6. Technical design spec
- Data model: models, fields, relations.
- Resolve FLAG-TECH-01 to 12.
- What is computed live vs in nightly or period-close jobs; period locking.
- Parameter versioning with effective dates (DEC-21).
- Roles, security and approvals.
- Refresh mechanism for the real-time features (RT-1 to RT-7).

### 7. Module breakdown and build order
- Split IE into a few addons with clear dependencies, for example:
  - master data and SAM;
  - balancing;
  - capture and metrics;
  - skill;
  - incentive;
  - real-time.
- Order them to match go-live. Shadow mode needs only capture, metrics and skill working, so incentive payout can be built last.

### 8. Development environment
- A staging Odoo instance cloned from production.
- A git repository.
- Claude Code access to the Docker setup.
- Odoo's test framework wired to the acceptance cases from step 1.

## Parallel track: shop-floor readiness (does not block coding)
- Bundle barcodes and tickets.
- Scanning devices.
- A station layout per line.
- Leader training on pauses and off-standard approvals.

## Change log
- 2026-10-18: created.
- 2026-10-18: step 1 done; step 2 in progress; document set updated.
- 2026-10-19: test-case assumptions resolved (spec v0.6); FLAG-TECH-13 and 14 added for technical design.
