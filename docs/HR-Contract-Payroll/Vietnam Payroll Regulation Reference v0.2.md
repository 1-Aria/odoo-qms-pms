# Vietnam Payroll Regulation Reference

v0.2 · Oct 30, 2026 · @Peter

The legal limits the payroll module and the pay policy work within. v0.2 corrects the workplace region, and adds who must contribute, the union fee without a union, probation limits, paid breaks for women and the room to pay above the statutory minimums (change log at the end).

The five-category model holds up, but Vietnamese law sorts every pay item on three separate tests — does it count toward the social insurance (SI) base, toward the overtime (OT) base, and is it taxable — and the item's nature in the contract decides, not its label. Three of the working assumptions need correcting:

- **The SI base is more than base pay.** Fixed, job-linked allowances (position, responsibility, hazard, seniority) and fixed "other supplements" written into the contract are also in it.
- **OT and night pay are no longer simply taxable.** From tax year 2026 they are PIT-exempt within the legal hour limits.
- **A "bonus" paid as a fixed monthly amount is not a bonus.** It counts as an "other supplement" and enters both the SI base and the OT base. Only true bonuses under Labor Code Art. 104 stay out of both.

Figures are as of 29 Oct 2026. Minimum wage, the SI cap, PIT law and union dues all changed during 2026, and another minimum-wage rise is proposed for 1 Jan 2027, so every number here belongs in effective-dated parameters, not in rule code. This is research for system design, not legal or tax advice; confirm the open items with your accountant and the local SI office.

## Legal basis and 2026 parameters

The framework is the Labor Code 2019 plus four laws that took effect in 2025–2026: the SI Law 2024, the Trade Union Law 2024, the Employment Law 2025 and the PIT Law 2025.

| Parameter | Value (VND) | Effective | Basis |
| --- | --- | --- | --- |
| Regional minimum wage, monthly (Region I / II / III / IV) | 5,310,000 / 4,730,000 / 4,140,000 / 3,700,000 | 1 Jan 2026 | Decree 293/2025 |
| Regional minimum wage, hourly (I / II / III / IV) | 25,500 / 22,700 / 19,900 / 17,800 | 1 Jan 2026 | Decree 293/2025 |
| SI reference level (mức tham chiếu) | 2,530,000 (was 2,340,000) | 1 Jul 2026 | SI Law 2024 Art. 7; Decree 161/2026 |
| SI and HI salary cap (20 × reference level) | 50,600,000 (was 46,800,000) | 1 Jul 2026 | SI Law 2024 Art. 31 |
| UI salary cap (20 × regional minimum wage) | Region I 106,200,000; Region II 94,600,000; Region IV 74,000,000 | 1 Jan 2026 | Employment Law 2025 Art. 34 |
| Employer SI + HI + UI | 21.5% | 1 Jul 2025 | SI Law 2024 Arts. 33–34 |
| Employee SI + HI + UI | 10.5% | 1 Jul 2025 | SI Law 2024 Arts. 33–34 |
| Union fee, employer (kinh phí công đoàn) | 2% of SI salary fund | 1 Jul 2025 | Trade Union Law 2024 Art. 29; Decree 105/2026 |
| Union dues, members only (đoàn phí) | 0.5% of SI salary, max 10% of base salary (253,000) `[to confirm: whether "base salary" is the state base salary (lương cơ sở) or the SI reference level; the module needs one named parameter]` | 1 Jul 2025 | Decision 61/QĐ-TLĐ |
| PIT personal deduction / per dependent | 15,500,000 / 6,200,000 per month | 1 Jan 2026 | Resolution 110/2025 |
| PIT brackets | 5 brackets, 5%–35% | Tax year 2026 | PIT Law 2025 Art. 9 |
| Cash meal allowance, PIT-free cap | 1,200,000 per month (was 730,000) | 1 Jul 2026 | Decree 253/2026 Art. 8 |
| OT hour caps | 40 h/month; 300 h/year for textile and garment | Current | Labor Code Art. 107; Decree 145 Art. 61 |

The minimum-wage region is set by the ward or commune of the workplace under the post-merger list in the annex to Decree 293/2025 ([source](https://thuvienphapluat.vn/hoi-dap-phap-luat/muc-luong-toi-thieu-vung-2026-tinh-an-giang-la-bao-nhieu-138069866.html)). The garment company's workplace, phường Chi Lăng in An Giang, is **Region IV**: 3,700,000 a month, 17,800 an hour (confirmed by Peter, 2026-10-30). The UI cap is therefore 20 × 3,700,000 = 74,000,000.

The hourly minimum applies to workers paid by the hour or day. A monthly salary at exactly 3,700,000 gives 3,700,000 ÷ 208 = 17,788 an hour, just under it. That is lawful for monthly-paid workers, but a daily rate must be checked against the hourly minimum times the day's hours.

Key texts to keep on file: Labor Code 2019 Arts. 90, 93, 98, 104, 107; Decree 145/2020 Arts. 55–57, 61; SI Law 2024 Art. 31; Decree 158/2025 Art. 7; Official Letter 1198/CTL&BHXH-BHXH (2025), which lists 14 allowances excluded from the SI base; Employment Law 2025 and Decree 374/2025; Trade Union Law 2024 and Decree 105/2026; PIT Law 2025 (Law 109/2025), Decree 253/2026 and Circular 87/2026.

## How the law classifies pay

Every pay item must be tagged on three independent tests, and the three sets do not coincide. The SI base excludes anything that fluctuates with productivity or performance; the OT base includes variable pay if it is salary for the job; PIT taxes almost everything except a short exempt list.

| Pay item (by legal nature) | SI base | OT base | PIT |
| --- | --- | --- | --- |
| Salary by job or title, from the salary scale (Art. 93) | Yes | Yes | Taxable |
| Allowance fixed in the contract that compensates working conditions, job complexity, living conditions or labour attraction (position, responsibility, hazard, seniority) | Yes | Yes | Taxable; a few state-listed allowances exempt |
| Other supplement: a fixed amount agreed in the contract and paid every pay period | Yes | Yes | Taxable |
| Allowance or supplement that varies with productivity, work process or quality (KPI pay, output pay, attendance-conditional pay) | No | Yes if it is salary for the job; No if it is an Art. 104 bonus | Taxable |
| Bonus under Art. 104 (business results, completion level) and initiative bonus | No | No | Taxable |
| Welfare support: meal, fuel, phone, travel, housing, childcare, weddings, funerals, birthdays, hardship | No | No | Meal exempt to 1.2M/month cash; lump-sum phone, travel, stationery, uniform exempt up to the prescribed level; others generally taxable |
| OT pay and night-work premium | No | Not applicable | Exempt within legal hour limits |
| Pay for untaken annual leave | No | Not applicable | Exempt |
| Severance and job-loss allowance | No | Not applicable | Not taxable, including amounts above the statutory level |

The SI rule is Decree 158/2025 Art. 7: salary by job or title, plus job-linked allowances and fixed supplements agreed in the contract, minus anything that depends on or fluctuates with productivity, work process or quality ([source](https://lsvn.vn/huong-dan-chi-tiet-ve-tien-luong-lam-can-cu-dong-bao-hiem-xa-hoi-bat-buoc-a159743.html)). For a piece-rate or hourly contract, the SI base is the time-based monthly wage in the contract, converted at the agreed hours or days.

The OT rule is Decree 145/2020 Art. 55: the actual wage paid for the job in the month, excluding OT and night pay, holiday pay, Art. 104 and initiative bonuses, meal money, the fuel/phone/travel/housing/childcare supports, life-event supports, and any support unrelated to the job.

Labels do not decide. In August 2026 the Ministry of Home Affairs answered a factory that splits pay 70% base and 30% KPI: KPI pay that is a salary component tied to the job must go into the OT base at the amount actually earned that month, while KPI that is genuinely an Art. 104 bonus does not ([source](https://baodautu.vn/doanh-nghiep-phai-can-cu-luong-thuc-tra-de-tinh-tien-lam-them-gio-d662034.html)). The same answer said fixed monthly position and responsibility allowances must be judged on their nature, not their name.

## Your five categories, checked

Deductions hold as stated; base pay, bonus and allowances need refining; the OT tax treatment is out of date.

| Category | Working assumption | Verdict | What the rules say |
| --- | --- | --- | --- |
| 1. Base pay | The SI base | Partly | SI base = salary by job + fixed job-linked allowances + fixed supplements. It cannot be below the regional minimum wage for full normal hours and is capped at 50.6M. |
| 2. Bonus pay | Not in OT base, not in SI base, taxable | Right for true bonuses; split needed | Art. 104 bonuses are out of SI and OT. A "bonus" that is a fixed sum in the contract paid every period is an other supplement: in SI and OT. Worker efficiency pay that is wage for output is in the OT base but out of the SI base. |
| 3. Overtime pay | Not in OT or SI base, taxable | Tax part outdated | Still outside both bases. From tax year 2026, OT and night pay within legal hour caps are PIT-exempt; only pay for hours beyond the caps is taxed. |
| 4. Allowances | Two groups, neither in SI or OT base, taxable | Split is right; treatment of group A is wrong | Group A (position, responsibility, hazard, seniority), when fixed and job-linked, is in both SI and OT bases. Group B (attendance, meal, fuel, phone, housing, childcare) is outside both; meal is PIT-free to 1.2M. |
| 5. Deductions | SI, PIT, union, other | Right, with detail | Employee pays 8% SI + 1.5% HI + 1% UI = 10.5%, PIT withholding, and 0.5% union dues only if a union member. The 2% union fee is an employer cost, not a payslip deduction. |

Only one category sits **in the OT base but outside the SI base**: salary for the job that varies with productivity or quality. A bonus is outside both, and a fixed allowance is inside both. A component that should count for OT but not for SI must therefore be variable salary that actually varies, not a bonus and not a fixed amount.

Two cases deserve care in a garment plant. An attendance allowance stays outside the SI base only if it is genuinely conditional on attendance; a flat amount always paid risks being treated as a fixed supplement. Worker efficiency pay should be defined explicitly in the pay regulation as either output wage (raises OT cost) or Art. 104 bonus (does not), because that choice changes the OT bill every month.

## Insurance and union contributions

Total statutory contributions are 32% of the SI base (21.5% employer, 10.5% employee), plus a 2% employer union fee.

| Fund | Employer | Employee | Base and cap |
| --- | --- | --- | --- |
| Pension and survivorship | 14% | 8% | SI base, cap 50.6M |
| Sickness and maternity | 3% | – | SI base, cap 50.6M |
| Occupational accident and disease | 0.5% | – | SI base, cap 50.6M |
| Health insurance (HI) | 3% | 1.5% | SI base, cap 50.6M |
| Unemployment insurance (UI) | 1% | 1% | Same base, cap 20 × regional minimum wage |
| Union fee | 2% | – | Total SI salary fund |
| Union dues (members) | – | 0.5% | SI salary, max 253,000 per month |

- **Caps differ by fund.** SI and HI cap at 20 × the reference level (50.6M from 1 Jul 2026); UI caps at 20 × the regional minimum wage of the workplace ([source](https://thuvienphapluat.vn/lao-dong-tien-luong/mau-bang-trich-nop-tien-bhtn-2025-ra-sao-52308.html)).
- **UI rate is now a ceiling.** The Employment Law 2025 sets UI at up to 1% for each side; Decree 374/2025 keeps both at 1% for now.
- **Union dues dropped.** Decision 61/QĐ-TLĐ cut member dues from 1% to 0.5% of the SI salary from 1 Jul 2025 for non-state enterprises.
- **Probation contracts** are outside compulsory SI under Decree 158/2025. Probation written as a clause inside a labour contract is not a probation contract: SI applies from the contract's first day.
- **Rates are per-fund in the declarations,** so the module should store them per fund, not as two totals.

### Who contributes, and on what base

Participation and the base differ by participant type, so the module keeps them per person, not per company.

| Participant | SI (pension, sickness, accident) | HI | UI | Base |
| --- | --- | --- | --- | --- |
| Employee on a labour contract of 1 month or more | Yes | Yes | Yes | Contract salary + fixed allowances + fixed supplements, floored at the regional minimum wage |
| Employee on a probation contract | No | No | No | – |
| Enterprise manager or owner paid a salary, without a labour contract | Yes | Yes | No | The salary they are paid, floored at the reference level `[to confirm]` |
| Non-resident or foreign employee | Per SI Law 2024 rules for foreign workers | Yes | No | `[to confirm if it arises]` |

The manager row follows SI Law 2024 Art. 2 and Art. 31 as reported in secondary sources. Confirm the floor, the funds and whether the union fee applies with the SI office before configuring an owner.

### Union fee without a union

The 2% employer union fee (kinh phí công đoàn) is owed on the SI salary fund **whether or not the company has a grassroots union**. Member dues (0.5%) apply only to members, so with no union they are zero. Confirm with the accountant that the fee is being paid and to which body while no grassroots union exists.

## Overtime, night work and piece rate

OT is paid at no less than 150% on workdays, 200% on weekly rest days and 300% on public holidays and paid leave days, on top of the holiday pay itself for day-paid workers (Labor Code Art. 98).

```latex
\text{OT pay} = \text{actual hourly wage} \times \text{OT rate} \times \text{OT hours}
```

| Situation | Minimum pay |
| --- | --- |
| OT on a workday | 150% |
| OT on a weekly rest day | 200% |
| OT on a public holiday or paid leave day | 300%, plus the day's holiday pay for day-paid workers |
| Normal hours at night (22:00–06:00) | +30% of the day rate |
| OT at night | OT rate + 30% night premium + 20% of the day-time rate for that day type |

- **Time-paid workers:** the hourly base is the month's actual wage for the job divided by actual hours worked, after the Art. 55 exclusions (see the classification table).
- **Piece-rate workers:** OT is paid per piece at no less than 150% / 200% / 300% of the normal unit price, so output data per OT period is required (Decree 145 Art. 55.2).
- **Hour limits:** OT may not exceed 50% of normal daily hours, 40 hours a month and 200 hours a year; textile and garment production may go to 300 hours a year with written notice to the provincial labour authority within 15 days of passing 200 hours ([source](https://luatminhkhue.vn/quy-dinh-ve-gioi-han-so-gio-lam-them-ot-toi-da-trong-ngay-thang-nam.aspx)).
- **Consent:** the worker's agreement is required for OT, outside the emergency cases in Art. 108.
- **Paying above the minimum:** the rates in Art. 98 are floors. A company may pay a higher OT rate, or a per-hour OT supplement on top of the statutory rate, as long as the pay regulation states it. Such a supplement is pay for OT hours, so it shares OT's tax treatment `[to confirm with the tax advisor]`.

## Working time items with pay effects

These rules decide paid time, so the attendance spec must capture them and payroll must pay them.

| Item | Rule | Basis |
| --- | --- | --- |
| Probation length | At most 180 days for enterprise managers; 60 days for jobs needing a college degree or higher; 30 days for jobs needing intermediate vocational or technical qualifications, technical workers and skilled staff; 6 working days for other jobs. No probation on contracts under 1 month. | Labor Code Arts. 24–25 |
| Probation pay | At least 85% of the salary for the job | Art. 26 |
| Nursing break | Women raising a child under 12 months: 60 minutes a day, paid as working time | Art. 137(4) |
| Menstruation break | 30 minutes a day for at least 3 days a month, paid as working time | Decree 145 Art. 80 |
| Annual leave | 12 days; 14 for heavy, hazardous or dangerous jobs; 16 for especially heavy ones; +1 day per 5 years of service | Arts. 113–114; job list in Circular 11/2020 |
| Sick child care | SI-paid leave to care for a sick child under 7 | SI Law |
| Work accident treatment | Employer pays full salary during treatment | OSH Law |
- **Tax link:** hours beyond these caps lose the PIT exemption, so the module must track OT hours by month and year, not only by payslip.

## Personal income tax

From tax year 2026, residents are taxed on a 5-bracket progressive scale after a 15.5M personal deduction and 6.2M per dependent; employment-income rules of the PIT Law 2025 apply from 1 Jan 2026 even though the law as a whole took effect on 1 Jul 2026.

| Monthly taxable income (VND) | Rate |
| --- | --- |
| Up to 10M | 5% |
| Over 10M to 30M | 10% |
| Over 30M to 60M | 20% |
| Over 60M to 100M | 30% |
| Over 100M | 35% |

Taxable income = gross employment income − exempt and excluded items − employee insurance contributions − family deductions − other allowed deductions ([source](https://ketoananpha.vn/diem-moi-luat-thue-tncn-2025.html)).

Items a payroll engine must handle (Decree 253/2026, [source](https://einvoice.vn/tin-tuc/10-diem-moi-noi-bat-cua-nghi-dinh-253-2026-nd-cp)):

- **OT and night pay:** exempt when within labour-law limits; the employer must keep a schedule of OT and night hours and amounts paid. Pay beyond the limits is taxable.
- **Untaken leave pay:** exempt.
- **Meal money:** cash up to 1.2M per person per month is not taxable from 1 Jul 2026; meals provided in kind are not taxable at all.
- **Lump-sum allowances** for stationery, business travel, phone and uniforms: only the part above the prescribed level is taxable.
- **Severance and job-loss allowances:** not taxable, including amounts above the statutory minimum when set in company rules or the contract.
- **New annual deductions:** medical costs up to 23M and education costs up to 24M per year, with invoices; mostly applied at year-end finalisation.
- **Non-residents:** flat 20%, no family deductions. **Casual workers** (no contract or under 3 months): 10% withholding on payments of 5M or more.

Reports conflict on whether the OT exemption covers the whole OT payment or only the premium above normal pay; most sources, including summaries of Decree 253 Art. 26, describe the whole payment. Confirm against Circular 87/2026 before coding it.

## Pay-structure levers and risks

The law leaves real room to shape cost, but only through the genuine nature of each payment; a mislabelled item is reclassified and back-charged.

| Lever | Effect | Condition and risk |
| --- | --- | --- |
| Keep the SI base to job salary plus genuinely fixed allowances | Lowers 32% contributions | Base must stay at or above the regional minimum wage; a lower base also lowers workers' pension, maternity and sickness benefits |
| Pay performance through an Art. 104 bonus regulation | Outside SI and OT bases | Must actually vary with results; a fixed monthly "bonus" is a supplement |
| Define worker output pay as bonus rather than output wage | Lowers OT cost | Must be written that way in the pay regulation and contract; inspectors judge nature, not name |
| Use welfare items on the excluded list (meal, travel, housing, childcare) | Outside SI and OT bases | Must be genuine support; meal is also PIT-free to 1.2M cash |
| Provide meals in kind (canteen) | Fully PIT-free | Needs invoices or meal records |
| Keep OT within 40 h/month and 300 h/year | OT stays PIT-free | Hours above the caps are taxable and are also a labour violation |

OT no longer creates a PIT reason to disguise pay, since legal OT is tax-free. The main remaining tension is between SI cost and OT cost on one side and worker benefits and retention on the other. Late or under-declared SI is subject to back-payment with interest under Decree 274/2025 and administrative fines.

## Implications for the Odoo module

The regulation maps cleanly onto data rather than Python: tag each pay component once with its legal nature and three flags, and the salary rules become short, generic sums.

1. **Pay component master.** Fields: legal type (job salary, fixed allowance, fixed supplement, variable pay, Art. 104 bonus, welfare support, OT, night premium, deduction), `in_si_base`, `in_ot_base`, PIT treatment (taxable, exempt, exempt up to a cap, excluded), the cap parameter, legal reference.
2. **Contract pay lines** replacing the single `contract.wage`: component, amount or rate, pay frequency, effective dates. The contract's SI base is derived from these lines, not typed.
3. **Salary scale (Art. 93).** Job group (worker, office) × grade × step × amount; contracts point to a step, positions carry default allowance profiles.
4. **Effective-dated parameters.** Regional minimum wages, reference level, per-fund rates, caps, PIT brackets, family deductions, meal cap, OT hour caps. Each workplace carries its region.
5. **Generic rules:**
   - SI base = sum of contract lines with `in_si_base`, floored at the regional minimum wage and capped per fund.
   - OT hourly base = sum of the month's paid items with `in_ot_base` ÷ actual hours.
   - PIT taxable = gross − exempt and excluded items − employee insurance − family and other deductions.
6. **OT and attendance inputs** by type (workday, rest day, holiday × day, night), with monthly and yearly cap checks; hours over the cap flow to taxable income automatically.
7. **Piece-rate inputs:** output quantity and unit price per period, including OT periods; the planned IE module is a natural source for standard rates and output.
8. **Employee tax and union data:** residency, dependents register, union membership flag; a year-end finalisation view and the OT/night schedule Decree 253 requires.
9. **Payslip** showing each component and deduction, as Art. 95 requires a written pay notice each period.
10. **Contribution profile per person:** participant type, the funds that apply, where each base comes from (contract lines or a declared amount), its floor and cap, union membership and the PIT method. An owner and a worker differ here, not in rule code.
11. **Checks, not constraints:** the module records each component's legal nature beside its flags and reports a mismatch, such as a welfare item counted in the OT base. Whether that blocks a run is configuration, because the company decides how to apply the law and answers for it.

## Open questions

- [x] Workplace region: phường Chi Lăng, Region IV (Peter, 2026-10-30).
- [x] Grassroots union: none yet; the structure must support one later (Peter, 2026-10-30). The employer fee still applies.
- [ ] How is worker skill and efficiency pay written in contracts and the pay regulation: variable salary, fixed allowance or Art. 104 bonus? The Pay Policy's current-scheme options A and B decide this.
- [ ] Is the attendance allowance reduced or forfeited on absence? Check it against the 14 excluded items in Official Letter 1198.
- [ ] Tax advisor to confirm: OT exemption on the whole payment or only the premium; a company OT supplement above the statutory rate; how OT pay above the monthly limit is split into exempt and taxable; the PIT treatment of travel, housing, childcare and phone allowances under Decree 253 and Circular 87/2026.
- [ ] SI office to confirm: the base, funds and union fee for an owner or manager paid without a labour contract; the base for a daily-paid contract.
- [ ] Which jobs, if any, are on the heavy or hazardous list (14 days of annual leave)?
- [ ] Is there a current published salary scale (Art. 93) and a written bonus regulation (Art. 104)?
- [ ] Watch list: the proposed 7.8% minimum-wage rise from 1 Jan 2027 and the draft Labor Code amendment.

## Sources

- [Decree 158/2025 Art. 7: SI salary basis (LSVN)](https://lsvn.vn/huong-dan-chi-tiet-ve-tien-luong-lam-can-cu-dong-bao-hiem-xa-hoi-bat-buoc-a159743.html)
- [Ministry of Home Affairs on OT base and KPI pay (Báo Đầu tư, Aug 2026)](https://baodautu.vn/doanh-nghiep-phai-can-cu-luong-thuc-tra-de-tinh-tien-lam-them-gio-d662034.html)
- [PIT Law 2025: brackets and family deductions (Kế toán Anpha)](https://ketoananpha.vn/diem-moi-luat-thue-tncn-2025.html)
- [Decree 253/2026: ten key PIT changes (Einvoice)](https://einvoice.vn/tin-tuc/10-diem-moi-noi-bat-cua-nghi-dinh-253-2026-nd-cp)
- [Minimum wage 2026 by ward, An Giang (Thư viện Pháp luật)](https://thuvienphapluat.vn/hoi-dap-phap-luat/muc-luong-toi-thieu-vung-2026-tinh-an-giang-la-bao-nhieu-138069866.html)
- [Minimum wage 2026 for all 34 provinces (LuatVietnam)](https://luatvietnam.vn/lao-dong-tien-luong/muc-luong-toi-thieu-vung-cua-34-tinh-thanh-tu-01-01-2026-562-103349-article.html)
- [SI cap 50.6M from 1 Jul 2026 (Thư viện Pháp luật)](https://thuvienphapluat.vn/hoi-dap-phap-luat/muc-dong-bhxh-toi-da-tu-ngay-0172026-la-bao-nhieu-138091227.html)
- [UI cap and rates under the Employment Law 2025 (Thư viện Pháp luật)](https://thuvienphapluat.vn/lao-dong-tien-luong/mau-bang-trich-nop-tien-bhtn-2025-ra-sao-52308.html)
- [Decree 374/2025 keeps UI at 1% (Tạp chí Nguồn nhân lực)](https://tcnnld.vn/news/detail/71061/Quy-dinh-moi-ve-dong-va-huong-bao-hiem-that-nghiep-tu-nam-2026.html)
- [Union fee 2% under Decree 105/2026 (Thư viện Pháp luật)](https://thuvienphapluat.vn/lao-dong-tien-luong/kinh-phi-cong-doan-nam-2026-muc-dong-va-muc-phat-cham-dong-hoac-khong-dong-59354.html)
- [Union dues cut to 0.5% by Decision 61/QĐ-TLĐ](https://hethongphapluat.com/phap-luat/node/3391)
- [OT hour caps and the 300-hour garment exception (Luật Minh Khuê)](https://luatminhkhue.vn/quy-dinh-ve-gioi-han-so-gio-lam-them-ot-toi-da-trong-ngay-thang-nam.aspx)
- [Meal allowance PIT cap 1.2M (Thuế MAN)](https://thue.man.net.vn/?p=6839)
- [SI contribution split 21.5% / 10.5% (CareerLink)](https://www.careerlink.vn/cam-nang-viec-lam/?p=29110)

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-29 | First draft. |
| 0.2 | 2026-10-30 | Region corrected to Chi Lăng, Region IV, with the hourly-minimum note; the variable-salary category (in OT base, out of SI base) spelled out; participants and their bases, including owners and managers without a labour contract; union fee owed without a union; probation inside a labour contract; paying OT above the statutory rate; a table of working-time items with pay effects (probation limits, paid breaks for women, annual leave by job type, sick-child leave, work accidents); module implications 10–11; open questions updated. |
