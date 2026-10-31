"""Reference calculation for the Payroll Acceptance Test Cases.

Every expected figure in the test cases comes from this script, so no amount is typed by hand.
It also lists the expected gross, insurance, PIT, net and employer cost per case, which the
module's automated tests can assert against.

Usage (from this folder):
    python3 -I payroll_reference_calc.py
        prints a summary line per case
    python3 -I payroll_reference_calc.py payroll_test_cases_template.md "Payroll Acceptance Test Cases v0.5.md"
        fills each {{CASE:ID}} placeholder in the template with that case's table and footer

To change a case: edit its inputs below and its prose in the template, then regenerate.
"""
import sys
from decimal import Decimal as D, ROUND_HALF_UP

MW = 3_700_000          # Region IV monthly minimum
REF = 2_530_000         # SI reference level
SI_CAP = 20 * REF       # 50,600,000
UI_CAP = 20 * MW        # 74,000,000
DUES_CAP = 253_000
SELF, DEP = 15_500_000, 6_200_000
BRACKETS = [(10_000_000, D("0.05")), (30_000_000, D("0.10")), (60_000_000, D("0.20")),
            (100_000_000, D("0.30")), (None, D("0.35"))]


def rnd(x):
    return int(D(str(x)).quantize(D(1), rounding=ROUND_HALF_UP))


def f(n):
    return f"{n:,}"


def pit_progressive(t):
    tax, lo = D(0), 0
    for hi, rate in BRACKETS:
        if t <= lo:
            break
        top = t if hi is None else min(t, hi)
        tax += (top - lo) * rate
        lo = hi if hi is not None else lo
    return rnd(tax)


def pit_formula(t):
    if t <= 10_000_000:
        return f"5% × {f(t)}"
    if t <= 30_000_000:
        return f"500,000 + 10% × {f(t - 10_000_000)}"
    if t <= 60_000_000:
        return f"2,500,000 + 20% × {f(t - 30_000_000)}"
    if t <= 100_000_000:
        return f"8,500,000 + 30% × {f(t - 60_000_000)}"
    return f"18,500,000 + 35% × {f(t - 100_000_000)}"


def ot(base, factor, hours):
    """OT line on a monthly OT base: base / 208 × factor × hours."""
    return rnd(D(base) / D(208) * D(str(factor)) * D(hours))


def prorate(amount, num, den=26):
    return rnd(D(amount) * D(str(num)) / D(den))


CASES = {}


def case(cid, earnings, *, exempt=0, si_base=None, funds=("SI", "HI", "UI"), member=False,
         deps=0, pit="prog", after_tax=(), si_note=None, hourly=None, exempt_note=None,
         notes=(), pit_text=None, advance=0, advance_text=""):
    """earnings: list of (label, calculation, amount). si_base None = no contributions."""
    gross = sum(a for _, _, a in earnings)
    rows = [f"| {l} | {c} | {f(a)} |" for l, c, a in earnings]
    rows.append(f"| **Gross pay** |  | **{f(gross)}** |")
    ins = 0
    er = {}
    if si_base is not None:
        b = max(si_base, MW) if "UI" in funds else si_base
        s, u = min(b, SI_CAP), min(b, UI_CAP)
        cap_s = " (capped)" if b > SI_CAP else ""
        cap_u = " (capped)" if b > UI_CAP else ""
        e_si, e_hi = rnd(D("0.08") * s), rnd(D("0.015") * s)
        rows.append(f"| Social insurance | 8% × {f(s)}{cap_s} | −{f(e_si)} |")
        rows.append(f"| Health insurance | 1.5% × {f(s)}{cap_s} | −{f(e_hi)} |")
        ins = e_si + e_hi
        er["SI"], er["HI"] = rnd(D("0.175") * s), rnd(D("0.03") * s)
        if "UI" in funds:
            e_ui = rnd(D("0.01") * u)
            rows.append(f"| Unemployment insurance | 1% × {f(u)}{cap_u} | −{f(e_ui)} |")
            ins += e_ui
            er["UI"] = rnd(D("0.01") * u)
        er["union fee"] = rnd(D("0.02") * s)
    dues = 0
    if member and si_base is not None:
        dues = min(rnd(D("0.005") * min(max(si_base, MW), SI_CAP)), DUES_CAP)
        rows.append(f"| Union dues | 0.5% × {f(min(max(si_base, MW), SI_CAP))} | −{f(dues)} |")
    # PIT
    if pit == "flat10":
        tax = rnd(D("0.10") * gross) if gross >= 5_000_000 else 0
        txt = pit_text or (f"10% × {f(gross)}" if tax else
                           f"Payment {f(gross)} is under 5,000,000: no withholding")
        rows.append(f"| PIT (flat 10%) | {txt} | {'−' + f(tax) if tax else '0'} |")
    else:
        ded = SELF + DEP * deps
        t = gross - exempt - ins - ded
        parts = f"{f(gross)}" + (f" − {f(exempt)} exempt" if exempt else "") + \
            (f" − {f(ins)} insurance" if ins else "") + f" − {f(ded)} deduction"
        if t <= 0:
            tax = 0
            txt = f"{parts} → below zero, no tax"
        else:
            tax = pit_progressive(t)
            txt = f"{parts} = {f(t)} taxable; {pit_formula(t)}"
        rows.append(f"| PIT | {pit_text or txt} | {'−' + f(tax) if tax else '0'} |")
    other = 0
    for label, calc, amount in after_tax:
        rows.append(f"| {label} | {calc} | −{f(amount)} |")
        other += amount
    net = gross - ins - dues - tax - other
    rows.append(f"| **Net pay** |  | **{f(net)}** |")
    settled = min(advance, max(net, 0))
    if advance:
        rows.append(f"| Advance settled | {advance_text} | −{f(settled)} |")
        rows.append(f"| **Remaining to pay** |  | **{f(net - settled)}** |")
    er_total = sum(er.values())
    foot = []
    if si_base is not None:
        foot.append(si_note or f"SI base {f(max(si_base, MW) if 'UI' in funds else si_base)}")
    else:
        foot.append(si_note or "No SI base")
    if hourly:
        foot.append(f"OT hourly rate {hourly}")
    if exempt:
        foot.append(f"PIT-exempt {f(exempt)}" + (f" ({exempt_note})" if exempt_note else ""))
    if er:
        foot.append(f"Employer contributions {f(er_total)} (" +
                    " + ".join(f"{f(v)} {k}" for k, v in er.items()) + ")")
    else:
        foot.append("Employer contributions 0")
    foot.append(f"Employer cost {f(gross + er_total)}")
    if advance and advance > settled:
        foot.append(f"Advance carried to next month: {f(advance)} − {f(settled)} = {f(advance - settled)}")
    foot.extend(notes)
    table = "| Line | Calculation | Amount |\n| --- | --- | --: |\n" + "\n".join(rows)
    CASES[cid] = dict(md=table + "\n\n" + " · ".join(foot), gross=gross, ins=ins, dues=dues,
                      tax=tax, net=net, er=er_total, cost=gross + er_total, to_pay=net - settled)


# ---------------------------------------------------------------- reference configuration
W, S3 = 4_500_000, 1_500_000
H = lambda base: f"{f(base)} ÷ 208 = {D(base) / D(208):,.4f}"  # noqa: E731

# Group A
case("A01", [("Salary", "Full month", W), ("OT workday 20 h", "4,500,000 ÷ 208 × 150% × 20", ot(W, 1.5, 20)),
             ("Efficiency incentive", "200 units × 1,500", 300_000), ("Attendance bonus", "", 300_000),
             ("Travel allowance", "", 200_000)],
     exempt=ot(W, 1.5, 20), si_base=W, member=True, hourly=H(W))
skilled = [("Salary", "Full month", W), ("Skill allowance", "Full month", S3)]
case("A02", skilled + [("OT workday 30 h", "6,000,000 ÷ 208 × 150% × 30", ot(6e6, 1.5, 30)),
                       ("Efficiency incentive", "1,000 units × 1,500", 1_500_000),
                       ("Attendance bonus", "", 300_000), ("Travel allowance", "", 200_000)],
     exempt=ot(6e6, 1.5, 30), si_base=6_000_000, hourly=H(6_000_000))
case("A03", [("Salary", "Full month", 8_000_000), ("OT workday 30 h", "8,000,000 ÷ 208 × 150% × 30", ot(8e6, 1.5, 30))],
     exempt=ot(8e6, 1.5, 30), si_base=8_000_000, deps=1, hourly=H(8_000_000))
case("A04", [("Salary", "Full month", 10_000_000), ("OT workday 16 h", "10,000,000 ÷ 208 × 150% × 16", ot(10e6, 1.5, 16)),
             ("KPI bonus", "Entered", 1_000_000)],
     exempt=ot(10e6, 1.5, 16), si_base=10_000_000, hourly=H(10_000_000))
case("A05", [("Salary", "Full month", 14_000_000), ("OT workday 8 h", "14,000,000 ÷ 208 × 150% × 8", ot(14e6, 1.5, 8)),
             ("KPI bonus", "Entered", 1_500_000), ("Phone lump-sum", "PIT-free", 200_000)],
     exempt=ot(14e6, 1.5, 8) + 200_000, si_base=14_000_000, hourly=H(14_000_000),
     exempt_note=f"OT {f(ot(14e6, 1.5, 8))} + phone 200,000")
case("A06", [("Salary", "Full month", 17_000_000), ("KPI bonus", "Entered", 3_000_000),
             ("Phone lump-sum", "PIT-free", 500_000)], exempt=500_000, si_base=17_000_000, deps=1)
case("A07", [("Salary", "Full month", 18_000_000), ("KPI bonus", "Entered", 2_000_000),
             ("Phone lump-sum", "PIT-free", 300_000)], exempt=300_000, si_base=18_000_000)
case("A08", [("Salary", "Full month", 45_000_000), ("KPI bonus", "Entered", 8_000_000),
             ("Phone lump-sum", "PIT-free", 1_000_000)], exempt=1_000_000, si_base=45_000_000, deps=2)
case("A09", [("Salary", "Full month", 70_000_000), ("KPI bonus", "Entered", 15_000_000),
             ("Phone lump-sum", "PIT-free", 2_000_000)], exempt=2_000_000, si_base=70_000_000, deps=1,
     si_note="SI base 70,000,000, capped to 50,600,000 for SI and HI")

# Group B (skilled worker from A02)
otp = ot(6e6, 1.5, 36) + ot(6e6, 2, 16)
b01_ex = rnd(D(otp) * 40 / 52)
case("B01", skilled + [("OT workday 36 h", "6,000,000 ÷ 208 × 150% × 36", ot(6e6, 1.5, 36)),
                       ("OT rest day 16 h", "6,000,000 ÷ 208 × 200% × 16", ot(6e6, 2, 16)),
                       ("Efficiency incentive", "1,200 units × 1,500", 1_800_000),
                       ("Attendance bonus", "", 300_000), ("Travel allowance", "", 200_000)],
     exempt=b01_ex, si_base=6_000_000,
     notes=[f"OT pay {f(otp)}; exempt share {f(otp)} × 40/52 = {f(b01_ex)}; taxable OT {f(otp - b01_ex)}"])
case("B02", [("Salary", "4,500,000 × 25/26", prorate(W, 25)), ("Skill allowance", "1,500,000 × 25/26", prorate(S3, 25)),
             ("OT workday 20 h", "6,000,000 ÷ 208 × 150% × 20", ot(6e6, 1.5, 20)),
             ("Efficiency incentive", "900 units × 1,500", 1_350_000), ("Attendance bonus", "Forfeited", 0),
             ("Travel allowance", "", 200_000)], exempt=ot(6e6, 1.5, 20), si_base=6_000_000)
case("B03", [("Salary", "26 paid days, full month", W), ("Skill allowance", "Full month", S3),
             ("OT workday 20 h", "6,000,000 ÷ 208 × 150% × 20", ot(6e6, 1.5, 20)),
             ("Efficiency incentive", "950 units × 1,500", 1_425_000), ("Attendance bonus", "Kept", 300_000),
             ("Travel allowance", "", 200_000)], exempt=ot(6e6, 1.5, 20), si_base=6_000_000)
b04 = [("OT workday 20 h", "6,000,000 ÷ 208 × 150% × 20", ot(6e6, 1.5, 20)),
       ("Night premium, normal hours 8 h", "6,000,000 ÷ 208 × 30% × 8", ot(6e6, 0.3, 8)),
       ("Night OT workday after daytime OT 4 h", "6,000,000 ÷ 208 × 210% × 4", ot(6e6, 2.1, 4)),
       ("Night OT holiday 2 h", "6,000,000 ÷ 208 × 390% × 2", ot(6e6, 3.9, 2))]
case("B04", skilled + b04 + [("Efficiency incentive", "1,000 units × 1,500", 1_500_000),
                             ("Attendance bonus", "", 300_000), ("Travel allowance", "", 200_000)],
     exempt=sum(a for _, _, a in b04), si_base=6_000_000)
pd = D(26) - D(45) / D(480)
case("B05", [("Salary", "4,500,000 × 25.90625/26", rnd(D(W) * pd / 26)),
             ("Skill allowance", "1,500,000 × 25.90625/26", rnd(D(S3) * pd / 26)),
             ("OT workday 20 h", "6,000,000 ÷ 208 × 150% × 20", ot(6e6, 1.5, 20)),
             ("Efficiency incentive", "1,000 units × 1,500", 1_500_000),
             ("Attendance bonus", "Forfeited: 3 late arrivals, limit 2", 0), ("Travel allowance", "", 200_000)],
     exempt=ot(6e6, 1.5, 20), si_base=6_000_000,
     notes=["Paid days 26 − 45/480 = 25.90625"])
case("B06", [("Salary", "10,000,000 × 24/26", prorate(10_000_000, 24))], si_base=10_000_000,
     notes=["SI base not prorated"])

# Group C
case("C01", [("Salary", "4,500,000 × 85% × 13/26", rnd(D(W) * D("0.85") * 13 / 26)), ("Travel allowance", "", 200_000)],
     si_base=None, pit="flat10")
case("C02", [("Salary, probation 10 days", "4,500,000 × 85% × 10/26", rnd(D(W) * D("0.85") * 10 / 26)),
             ("Salary, contract 16 days", "4,500,000 × 16/26", prorate(W, 16)),
             ("Efficiency incentive", "300 units × 1,500", 450_000), ("Attendance bonus", "", 300_000),
             ("Travel allowance", "", 200_000)], si_base=W)
leave = prorate(6e6, 5)
case("C03", [("Salary", "4,500,000 × 18/26", prorate(W, 18)), ("Skill allowance", "1,500,000 × 18/26", prorate(S3, 18)),
             ("Efficiency incentive", "600 units × 1,500", 900_000),
             ("Untaken annual leave 5 days", "6,000,000 × 5/26 (contract salary of the previous month)", leave),
             ("Travel allowance", "", 200_000)], exempt=leave, si_base=6_000_000,
     si_note="SI base 6,000,000 (18 working days, so the month is contributed)",
     notes=["Paid within 14 working days of the last day"])
case("C04", [("Salary and skill allowance", "6,000,000 × 0/26", 0)], si_base=None,
     si_note="No contributions: not working and not paid for 14 days or more",
     notes=["The SI fund pays the HI contribution during maternity leave",
            "The employee appears on the SI change report as on maternity leave"])
case("C05", [("Salary", "4,500,000 × 11/26", prorate(W, 11)), ("Skill allowance", "1,500,000 × 11/26", prorate(S3, 11)),
             ("Efficiency incentive", "300 units × 1,500", 450_000), ("Attendance bonus", "Kept", 300_000),
             ("Travel allowance", "", 200_000)], si_base=None,
     si_note="No contributions: 15 working days not worked and not paid by the company",
     notes=["The SI fund pays the sick-leave benefit separately"])
case("C06", [("Salary, probation clause 6 days", "4,500,000 × 85% × 6/26", rnd(D(W) * D("0.85") * 6 / 26)),
             ("Salary, after probation 20 days", "4,500,000 × 20/26", prorate(W, 20)),
             ("Attendance bonus", "", 300_000), ("Travel allowance", "", 200_000)], si_base=W,
     si_note="SI base 4,500,000 from the contract's first day, probation days included")

# Group D
case("D01", [("Salary", "Full month", 80_000_000)], si_base=80_000_000)
case("D02", [("Salary", "Full month", 6_000_000)], si_base=6_000_000, pit="flat10")
case("D03", [("Salary", "Full month", 10_000_000),
             ("Cash meal allowance", "PIT-free up to 1,200,000; 300,000 taxable", 1_500_000)],
     exempt=1_200_000, si_base=10_000_000,
     notes=["Taxable income before deductions 10,300,000", "SI base excludes the meal allowance"])
case("D04", [("Salary", "Full month", 10_000_000), ("Annual (Tet) bonus", "Entered", 10_000_000)],
     si_base=10_000_000, notes=["The bonus is outside the SI base and taxed in the month paid"])
case("D05", [("Salary", "Full month", 18_000_000), ("KPI bonus", "Entered", 2_000_000),
             ("Phone lump-sum", "PIT-free", 300_000)], exempt=300_000, si_base=18_000_000, deps=1,
     notes=["Compare TC-A07: the same pay with no dependent withholds 130,500"])
case("D06", [("Salary", "Decided by the owners", 40_000_000)], si_base=10_000_000, funds=("SI", "HI"),
     si_note="Declared SI base 10,000,000; no UI")
case("D07", [("Daily wage", "350,000 × 26 days", 9_100_000)], si_base=9_100_000, pit="flat10",
     si_note="SI base 350,000 × 26 = 9,100,000 (assumption)")

# Group E (skilled worker, normal month)
normal = skilled + [("OT workday 20 h", "6,000,000 ÷ 208 × 150% × 20", ot(6e6, 1.5, 20)),
                    ("Efficiency incentive", "1,000 units × 1,500", 1_500_000),
                    ("Attendance bonus", "", 300_000), ("Travel allowance", "", 200_000)]
adj = ot(6e6, 1.5, 4)
case("E01", normal + [("Adjustment for September 2026: OT workday 4 h", "6,000,000 ÷ 208 × 150% × 4; PIT-free", adj)],
     exempt=ot(6e6, 1.5, 20) + adj, si_base=6_000_000,
     si_note="SI base unchanged at 6,000,000 (OT is outside it)",
     notes=["The adjustment counts towards September's OT hours, not October's"])
g_e02 = sum(a for _, _, a in normal)
dmg = rnd(D("0.3") * (g_e02 - 630_000))
case("E02", normal, exempt=ot(6e6, 1.5, 20), si_base=6_000_000,
     after_tax=[("Damage compensation", f"30% × ({f(g_e02)} − 630,000 − 0) = {D('0.3') * (g_e02 - 630_000):,}", dmg)],
     notes=[f"Carried to next month: 3,000,000 − {f(dmg)} = {f(3_000_000 - dmg)}",
            "The deduction does not change employer cost"])

# D08: the OT supplement as a configuration test on the reference configuration
SUPH = 3_846
case("D08", skilled + [("OT workday 30 h", "6,000,000 ÷ 208 × 150% × 30", ot(6e6, 1.5, 30)),
                       ("OT supplement 30 h", "3,846 × 150% × 30", rnd(D(SUPH) * D("1.5") * 30)),
                       ("Efficiency incentive", "1,000 units × 1,500", 1_500_000),
                       ("Attendance bonus", "", 300_000), ("Travel allowance", "", 200_000)],
     exempt=ot(6e6, 1.5, 30) + rnd(D(SUPH) * D("1.5") * 30), si_base=6_000_000,
     exempt_note="OT and OT supplement")

# ---------------------------------------------------------------- current scheme (group G)
BASE = 3_700_000
LEVEL = {"Entry": 800_000, "S1": 1_300_000, "S2": 1_800_000, "S3": 2_300_000, "S4": 2_800_000}


def prod(level, paid_days=26, att=1):
    """Productivity pay line: level amount × paid days / 26 × attainment."""
    amt = LEVEL[level]
    pct = f"{D(str(att)) * 100:.0f}%"
    calc = f"{f(amt)} × {paid_days}/26 × {pct}" if paid_days != 26 else f"{f(amt)} × {pct}"
    return (f"Productivity pay, {level}", calc, rnd(D(amt) * D(paid_days) / 26 * D(str(att))))


def otbase(level, att=1):
    return BASE + rnd(D(LEVEL[level]) * D(str(att)))


def ot_line(level, hours, att=1):
    b = otbase(level, att)
    return (f"OT workday {hours} h", f"({f(BASE)} + {f(b - BASE)}) ÷ 208 × 150% × {hours}", ot(b, 1.5, hours))


SI_NOTE = "SI base 3,700,000 (productivity pay is outside it)"

o = ot_line("Entry", 20)
case("G01", [("Base salary", "Full month", BASE), prod("Entry"), o,
             ("Efficiency bonus", "Entered (shadow mode)", 300_000)],
     exempt=o[2], si_base=BASE, si_note=SI_NOTE, hourly=H(otbase("Entry")))
o = ot_line("S4", 30)
case("G02", [("Base salary", "Full month", BASE), prod("S4"), o,
             ("Efficiency bonus", "Entered (shadow mode)", 1_000_000)],
     exempt=o[2], si_base=BASE, si_note=SI_NOTE, hourly=H(otbase("S4")))
o = ot_line("S4", 30, D("0.8"))
case("G03", [("Base salary", "Full month", BASE), prod("S4", att=D("0.8")), o,
             ("Efficiency bonus", "Below the incentive threshold", 0)],
     exempt=o[2], si_base=BASE, si_note=SI_NOTE, hourly=H(otbase("S4", D("0.8"))))
o = ot_line("Entry", 20)
case("G04", [("Base salary", "3,700,000 × 24/26", prorate(BASE, 24)), prod("Entry", 24), o,
             ("Efficiency bonus", "Entered (shadow mode)", 300_000)],
     exempt=o[2], si_base=BASE, si_note=SI_NOTE, notes=["The OT base is not prorated by paid days"])
case("G05", [("Base salary", "26 paid days, full month", BASE), prod("Entry"), o,
             ("Efficiency bonus", "Entered (shadow mode)", 300_000)],
     exempt=o[2], si_base=BASE, si_note=SI_NOTE,
     notes=["Same payslip as TC-G01: annual leave days are paid days for both lines"])
case("G06", [("Base salary", "Full month", BASE),
             ("Productivity pay, S2", "1,800,000 × 100% (16 measured days; 10 training days excluded)", LEVEL["S2"])],
     si_base=BASE, si_note=SI_NOTE)
o = ot_line("Entry", 20)
case("G07", [("Base salary", "Full month", BASE), prod("Entry"), o,
             ("Efficiency bonus", "Entered (shadow mode)", 300_000),
             ("One-time bonus: project completion", "Entered; approved by the director", 500_000)],
     exempt=o[2], si_base=BASE, si_note=SI_NOTE)
g08 = [("Base salary", "3,700,000 × 20/26", prorate(BASE, 20)), prod("Entry", 20),
       ("Efficiency bonus", "Entered (shadow mode)", 200_000)]
g08_gross = sum(a for _, _, a in g08)
cap = D("0.3") * (g08_gross - 388_500)
case("G08", g08, si_base=BASE, si_note="SI base 3,700,000 (20 working days, so the month is contributed)",
     after_tax=[("Damage compensation: 2 uniform sets not returned",
                 f"300,000 per the work-rules decision; cap 30% × ({f(g08_gross)} − 388,500 − 0) = {cap:,.1f}", 300_000)],
     notes=["The deduction is within the cap, so nothing carries forward"])

# ---------------------------------------------------------------- current scheme, staff (group G)
def perf(cell, score=1, paid_days=26):
    amt = cell - BASE
    pct = f"{D(str(score)) * 100:.0f}%"
    calc = f"({f(cell)} − {f(BASE)}) × {pct}" if paid_days == 26 else f"({f(cell)} − {f(BASE)}) × {paid_days}/26 × {pct}"
    return ("Performance pay", calc, rnd(D(amt) * D(paid_days) / 26 * D(str(score))))


def staff_ot(cell, hours, score=1):
    b = BASE + rnd(D(cell - BASE) * D(str(score)))
    return (f"OT workday {hours} h", f"({f(BASE)} + {f(b - BASE)}) ÷ 208 × 150% × {hours}", ot(b, 1.5, hours)), b


SI_STAFF = "SI base 3,700,000 (performance pay is outside it)"
o, b = staff_ot(8_000_000, 30)
case("G10", [("Base salary", "Full month", BASE), perf(8_000_000), o], exempt=o[2], si_base=BASE, deps=1,
     si_note=SI_STAFF, hourly=H(b))
o, b = staff_ot(8_000_000, 30, D("0.8"))
case("G11", [("Base salary", "Full month", BASE), perf(8_000_000, D("0.8")), o], exempt=o[2], si_base=BASE, deps=1,
     si_note=SI_STAFF, hourly=H(b))
o, b = staff_ot(10_000_000, 16)
case("G12", [("Base salary", "Full month", BASE), perf(10_000_000), o], exempt=o[2], si_base=BASE,
     si_note=SI_STAFF, hourly=H(b))
case("G13", [("Base salary", "Full month", BASE), perf(45_000_000)], si_base=BASE, deps=2,
     si_note=SI_STAFF, notes=["The PIT return declares 45,000,000 of income against an SI base of 3,700,000 (Pay Policy §4.3)"])

# ---------------------------------------------------------------- advances (group G)
o = ot_line("Entry", 20)
case("G14", [("Base salary", "Full month", BASE), prod("Entry"), o,
             ("Efficiency bonus", "Entered (shadow mode)", 300_000)],
     exempt=o[2], si_base=BASE, si_note=SI_NOTE,
     advance=1_500_000, advance_text="Advance paid on the 15th, approved")
case("G15", [("Base salary", "3,700,000 × 10/26", prorate(BASE, 10)), prod("Entry", 10)],
     si_base=None, si_note="No contributions: 16 working days neither worked nor paid",
     advance=2_000_000, advance_text="Advance paid on the 15th; capped at net pay")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        text = open(sys.argv[1], encoding="utf-8").read()
        for cid, c in CASES.items():
            text = text.replace("{{CASE:%s}}" % cid, c["md"])
        left = [l for l in text.splitlines() if "{{CASE:" in l]
        if left:
            sys.exit(f"unfilled placeholders: {left}")
        open(sys.argv[2], "w", encoding="utf-8").write(text)
        print("written", sys.argv[2])
    else:
        for cid, c in CASES.items():
            print(f"{cid}  gross {c['gross']:>12,}  ins {c['ins']:>10,}  dues {c['dues']:>7,}  pit {c['tax']:>10,}  "
                  f"net {c['net']:>12,}  er {c['er']:>11,}  cost {c['cost']:>12,}")
