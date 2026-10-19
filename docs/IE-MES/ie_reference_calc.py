#!/usr/bin/env python3
"""
IE module - reference calculator for the acceptance test cases.

Companion to IE_Acceptance_Test_Cases_v0.3.md, which is based on
IE_Business_Logic_Spec_v0.6.md (rules of record) and IE_Framework_Rationale_v0.6.md.

What it does
  1. Implements the spec's formulas in plain Python (no Odoo), as a readable reference.
  2. Computes every calculated test case from its inputs.
  3. Compares each result with the expected value written in the test case document.

Usage
  python ie_reference_calc.py                                      run all calculated cases
  python ie_reference_calc.py --doc IE_Acceptance_Test_Cases_v0.3.md
                                                                   also check that the document shows
                                                                   the same expected values

Expected values are written as they appear in the document ("76.4%", "1,226.4", "29").
A computed value passes when it rounds to the displayed value (tolerance = half a unit of
the last displayed digit). Percentages are compared on the percent scale.

The Odoo implementation is correct when its results for the same inputs pass the same checks.
"""
import re
import sys
from statistics import median

# --------------------------------------------------------------------------------------
# Parameter set P0: spec placeholders at the baseline (2026-10-18). Spec §14.1, DEC-21.
# --------------------------------------------------------------------------------------
P0 = {
    "theta": 0.70,                      # normal threshold factor (§11.3)
    "theta_floor": 0.30,                # floor on ramp days (§11.3)
    "k_def": 1.0,                       # defect deduction factor (§9.3)
    "pf": {"I": 1.25, "L": 1.10, "U": 1.00, "O": 1.00, "NSE": 1.00},  # §11.2
    "pf_cap": {"A": 2400.0, "B": 2400.0, "C": 2400.0},  # EM per family, by grade; cumulative, no reset (§11.2, DEC-23)
    "m_tier": {"T1": 1.00, "T2": 1.05, "T3": 1.10, "T4": 1.20},       # §11.4
    "iluo_L": (0.55, 0.030),            # (efficiency >=, defect rate <=) (§10.4)
    "iluo_U": (0.80, 0.015),
    "iluo_O_eff": 0.95,
    "min_volume": 600.0,                # EM_g per family in the window (§10.3)
    "dormancy_days": 180,               # §10.4
    # Bootstrap ramp profiles (§7.7.3). R2 day 2 = 55/80 = 0.6875.
    "ramp": {
        "R0": [1.0],
        "R1": [0.75, 0.90, 1.0],
        "R2": [0.500, 0.6875, 0.875, 1.0],
        "R3": [0.40, 0.55, 0.70, 0.85, 0.95, 1.0],
    },
    "f_R0": 0.90, "f_R1": 0.60,         # familiarity bands (§7.7.3)
    "ramp_end": 0.95,                   # profile ends when r(d) >= this (§7.7.3)
    "fit_min_runs": 10,                 # runs before a fitted profile replaces the bootstrap (§7.7.5)
    "plateau_from_day": 6, "plateau_min_days": 5,                     # §7.7.5
    "rt_window": 60, "starved_share": 0.10,                           # §13.2
    "alert_line": 0.85, "alert_os_pending": 30, "alert_bundle_factor": 3,
    "alert_starved": 15, "wip_cap": 3,                                # RT-2
    "min_attendance": 0.80,             # eligibility flag (§11.6)
}

# --------------------------------------------------------------------------------------
# Fixtures: style PS-01 and Line 1 (rationale §2)
# --------------------------------------------------------------------------------------
# op: (name, family, grade, machine class, skill-evaluated, SAM)
PS01 = {
    1: ("Placket attach", "Placket setting", "A", "SNLS", True, 1.60),
    2: ("Shoulder join", "Seam join", "C", "OL", True, 0.60),
    3: ("Collar attach", "Collar setting", "A", "SNLS", True, 1.80),
    4: ("Sleeve attach", "Sleeve setting", "B", "OL", True, 1.40),
    5: ("Side seam", "Seam join", "C", "OL", True, 1.20),
    6: ("Sleeve hem", "Hemming", "C", "FL", True, 0.90),
    7: ("Bottom hem", "Hemming", "C", "FL", True, 0.80),
    8: ("Buttonhole & button sew", "Buttonholing", "C", "BH", False, 1.70),
}
GARMENT_SAM = round(sum(o[5] for o in PS01.values()), 2)  # 10.00
T_DAY = 480          # attended minutes per operator per day
DAYS = 26            # working days in the fixture month
LINE1_OPS = 30
PLATEAU = 0.80       # Line 1 plateau for polos (overall basis)


# --------------------------------------------------------------------------------------
# Formulas
# --------------------------------------------------------------------------------------
def overlap(a_start, a_end, b_start, b_end):
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def os_inside_attendance(os_start, os_end, attendance):
    """Spec §3.3 rule 3: off-standard counts only inside attended time. Times in minutes."""
    return sum(overlap(os_start, os_end, s, e) for s, e in attendance)


def nam(a, os_minutes):
    return a - sum(os_minutes)


def em(pieces, sam):
    return pieces * sam


def dd(defective_qty, sam, p=P0):
    return defective_qty * sam * p["k_def"]


def book_defects(bundle_qty, defect_records):
    """
    Cumulative defective qty per bundle x operation cannot exceed the bundle quantity (§9.3).
    A record that would exceed it is rejected (None) and nothing of it is booked.
    """
    booked, total = [], 0
    for q in defect_records:
        if total + q > bundle_qty:
            booked.append(None)
        else:
            booked.append(q)
            total += q
    return booked


def theta_day(shares, p=P0):
    """shares: list of (s_k, r_k) for ramping styles that day (§11.3)."""
    s_sum = sum(s for s, _ in shares)
    raw = p["theta"] * (sum(s * r for s, r in shares) + (1 - s_sum))
    return max(p["theta_floor"], raw)


def incentive_minutes(records, dd_total, cap_used_before=None, p=P0):
    """
    records: list of (family, grade, level, em_g) in production order. level in I/L/U/O, or NSE
    for not-skill-evaluated families. PF applies to the part of each record that falls within the
    family's remaining PF_cap for its grade (cumulative EM_g in that family, carried across
    periods and levels, no reset: DEC-23).
    Returns (IM, PF bonus).
    """
    used = dict(cap_used_before or {})
    im, bonus = 0.0, 0.0
    for fam, grade, level, e in records:
        pf = p["pf"][level]
        if pf > 1.0:
            remaining = max(0.0, p["pf_cap"][grade] - used.get(fam, 0.0))
            within = min(e, remaining)
            bonus += within * (pf - 1.0)
        used[fam] = used.get(fam, 0.0) + e
        im += e
    return im + bonus - dd_total, bonus


def excess(im, tm):
    return max(0.0, im - tm)


def units(x, tier, p=P0):
    return x * p["m_tier"][tier]


LEVELS = ["I", "L", "U", "O"]


def criteria_level(eff, dr, prev_met_u, p=P0):
    lvl = "I"
    if eff >= p["iluo_L"][0] and dr <= p["iluo_L"][1]:
        lvl = "L"
    if eff >= p["iluo_U"][0] and dr <= p["iluo_U"][1]:
        lvl = "U"
        if prev_met_u and eff >= p["iluo_O_eff"]:
            lvl = "O"
    return lvl


def evaluate_level(prev, eff, dr, volume, prev_met_u, below_count, p=P0):
    """
    One evaluation (§10.3, §10.4). Returns (new level, warning, new below_count).
    - Volume below minimum: level kept, no evaluation.
    - At or above the previous level by criteria: take the criteria level.
    - Below: first time a warning, second consecutive time down one level.
    """
    if volume < p["min_volume"]:
        return prev, False, below_count
    crit = criteria_level(eff, dr, prev_met_u, p)
    if LEVELS.index(crit) >= LEVELS.index(prev):
        return crit, False, 0
    below_count += 1
    if below_count >= 2:
        return LEVELS[LEVELS.index(prev) - 1], False, 0
    return prev, True, below_count


def dormancy(prev, idle_days, ever_reached_u, p=P0):
    if idle_days < p["dormancy_days"] or prev == "I":
        return prev
    new = LEVELS[LEVELS.index(prev) - 1]
    if ever_reached_u and LEVELS.index(new) < LEVELS.index("L"):
        new = "L"
    return new


def tier(families):
    """families: list of (level, grade, machine class, skill-evaluated) (§10.5)."""
    q = [(g, m) for lvl, g, m, se in families if se and lvl in ("U", "O")]
    n = len(q)
    a = sum(1 for g, _ in q if g == "A")
    mc = len({m for _, m in q})
    if n >= 6 and a >= 2 and mc >= 3:
        return "T4"
    if n >= 4 and a >= 1 and mc >= 2:
        return "T3"
    if n >= 2:
        return "T2"
    return "T1"


def familiarity(new_ob_sams, familiar_flags):
    total = sum(new_ob_sams)
    fam = sum(s for s, f in zip(new_ob_sams, familiar_flags) if f)
    return fam / total


def ramp_class(f, p=P0):
    if f >= p["f_R0"]:
        return "R0"
    if f >= p["f_R1"]:
        return "R1"
    return "R2"


def fitted_profile(runs, p=P0):
    """Median observed r(d) per day; profile ends at the first day >= ramp_end (§7.7.5)."""
    prof = []
    for d in range(len(runs[0])):
        m = median(run[d] for run in runs)
        prof.append(m)
        if m >= p["ramp_end"]:
            break
    return prof


def run_plateau(daily_eff, p=P0):
    """daily_eff: on-standard efficiency of U/O operators by production day (index 0 = day 1)."""
    plateau_days = daily_eff[p["plateau_from_day"] - 1:]
    if len(plateau_days) < p["plateau_min_days"]:
        return None  # run excluded from fitting
    return sum(plateau_days) / len(plateau_days)


# --------------------------------------------------------------------------------------
# Test cases: each returns {label: computed value}; EXPECTED holds the document's values.
# --------------------------------------------------------------------------------------
CASES = {}


def case(cid):
    def deco(fn):
        CASES[cid] = fn
        return fn
    return deco


@case("TC-TA-01")
def _():
    os_ = [25, 20]
    return {"OS": sum(os_), "NAM": nam(480, os_)}


@case("TC-TA-02")
def _():
    return {"NAM": nam(480, [480])}


@case("TC-TA-03")
def _():
    approved = []  # the 30-minute pause was never approved
    return {"NAM": nam(480, approved)}


@case("TC-TA-04")
def _():
    # Bundle active 09:00-10:00 scheduled; leader enters OS-03 09:30-09:50 -> bundle paused at 09:30,
    # resumed 09:50. Bundle active minutes 09:00-10:00 minus the off-standard 20 = 40.
    bundle = (540, 600)
    os_rec = (570, 590)
    active = (bundle[1] - bundle[0]) - overlap(*bundle, *os_rec)
    return {"bundle active": active, "OS": os_rec[1] - os_rec[0]}


@case("TC-TA-05")
def _():
    att = [(480, 720), (780, 1020)]  # 08:00-12:00, 13:00-17:00
    a = sum(e - s for s, e in att)
    counted = os_inside_attendance(1000, 1040, att)  # OS-02 entered 16:40-17:20
    return {"A": a, "OS counted": counted, "NAM": nam(a, [counted])}


@case("TC-EM-01")
def _():
    g = em(280, 1.20)
    d = dd(3, 1.20)
    return {"EM_g": g, "DD": d, "EM_n": g - d}


@case("TC-EM-03")
def _():
    first = book_defects(20, [15, 10])
    assert first == [15, None], first
    corrected = book_defects(20, [15, 5])
    assert corrected == [15, 5], corrected
    return {"first": first[0], "DD": dd(15, 1.20), "DD corrected": dd(sum(corrected), 1.20)}


@case("TC-EM-05")
def _():
    return {"DD": dd(5, 1.70)}


@case("TC-EM-07")
def _():
    return {"before": em(100, 1.40), "after": em(100, 1.55)}


@case("TC-MET-01")
def _():
    A, NAM, EMg, EMn, bundle = 480, 435, 336.0, 332.4, 390
    return {
        "M1": EMn / NAM * 100, "M3": EMg / A * 100, "gross": EMg / NAM * 100,
        "M5": 45 / A * 100, "M6": EMg / bundle * 100, "M7": bundle / NAM * 100,
        "identity": (EMg / NAM) * (1 - 45 / A) * 100,
    }


@case("TC-MET-02")
def _():
    return {"M6": 336.0 / 300 * 100, "M7": 300 / 435 * 100, "M1": 332.4 / 435 * 100}


def month_A():
    a = DAYS * T_DAY + 1200
    os_ = [150, 250]
    n = nam(a, os_)
    g_norm, g_ot = em(7800, 1.20), em(950, 1.20)
    d = dd(30, 1.20)
    return dict(A=a, OS=sum(os_), NAM=n, EMg=g_norm + g_ot, EMg_norm=g_norm, EMg_ot=g_ot, DD=d)


def month_B():
    a = DAYS * T_DAY
    os_ = [200, 100]
    n = nam(a, os_)
    g_hem, g_slv = em(7000, 0.90), em(1900, 1.40)
    d = dd(40, 1.40)
    return dict(A=a, OS=sum(os_), NAM=n, EMg=g_hem + g_slv, g_hem=g_hem, g_slv=g_slv, DD=d)


def month_C():
    a = DAYS * T_DAY
    os_ = [150, 100]
    n = nam(a, os_)
    parts = [em(1500, 1.80), em(1600, 1.60), em(1200, 1.70), em(700, 1.40)]
    d = dd(10, 1.80)
    return dict(A=a, OS=sum(os_), NAM=n, EMg=sum(parts), parts=parts, DD=d)


@case("TC-MET-03")
def _():
    ms = [month_A(), month_B(), month_C()]
    A = sum(m["A"] for m in ms)
    OS = sum(m["OS"] for m in ms)
    N = sum(m["NAM"] for m in ms)
    G = sum(m["EMg"] for m in ms)
    D = sum(m["DD"] for m in ms)
    return {
        "A": A, "OS": OS, "NAM": N, "EM_g": G, "DD": D, "EM_n": G - D,
        "M4": G / N * 100, "M1 pooled": (G - D) / N * 100, "M3": G / A * 100,
        "M5": OS / A * 100, "identity": G / N * (1 - OS / A) * 100,
    }


@case("TC-SK-01")
def _():
    m = month_B()
    bmin = {"hem": 6800, "slv": 3800}
    tot = sum(bmin.values())
    sh_h, sh_s = bmin["hem"] / tot, bmin["slv"] / tot
    nam_h, nam_s = m["NAM"] * sh_h, m["NAM"] * sh_s
    emn_h, emn_s = m["g_hem"], m["g_slv"] - m["DD"]
    eff_h, eff_s = emn_h / nam_h, emn_s / nam_s
    dr_h, dr_s = 0 / 7000, 40 / 1900
    lvl_h = evaluate_level("U", eff_h, dr_h, m["g_hem"], True, 0)[0]
    lvl_s = evaluate_level("I", eff_s, dr_s, m["g_slv"], False, 0)[0]
    assert lvl_h == "U" and lvl_s == "L", (lvl_h, lvl_s)
    weighted = (eff_h * nam_h + eff_s * nam_s) / m["NAM"]
    return {
        "share hem": sh_h * 100, "share slv": sh_s * 100, "NAM hem": nam_h, "NAM slv": nam_s,
        "Eff hem": eff_h * 100, "Eff slv": eff_s * 100, "DR slv": dr_s * 100,
        "weighted": weighted * 100,
    }


@case("TC-SK-02")
def _():
    lvl, warn, _ = evaluate_level("L", 0.40, 0.0, 500, False, 0)
    assert lvl == "L" and not warn
    return {"volume": 500}


@case("TC-SK-03")
def _():
    l1, w1, b1 = evaluate_level("U", 0.75, 0.010, 3000, True, 0)
    l2, w2, b2 = evaluate_level(l1, 0.76, 0.010, 3000, False, b1)
    assert (l1, w1) == ("U", True) and (l2, w2) == ("L", False), (l1, w1, l2, w2)
    return {}


@case("TC-SK-04")
def _():
    assert dormancy("U", 180, True) == "L"
    assert dormancy("O", 200, True) == "U"
    assert dormancy("L", 190, True) == "L"
    assert dormancy("L", 190, False) == "I"
    assert dormancy("U", 179, True) == "U"
    return {}


@case("TC-SK-05")
def _():
    assert evaluate_level("U", 0.96, 0.005, 3000, True, 0)[0] == "O"
    assert evaluate_level("L", 0.96, 0.005, 3000, False, 0)[0] == "U"
    assert evaluate_level("U", 0.96, 0.020, 3000, True, 0)[1] is True  # defect rate too high: warning
    return {}


@case("TC-SK-06")
def _():
    A = [("U", "C", "OL", True), ("U", "C", "FL", True)]
    B = [("U", "C", "FL", True), ("I", "B", "OL", True)]
    C = [("U", "A", "SNLS", True), ("U", "A", "SNLS", True), ("U", "B", "OL", True),
         ("U", "B", "SNLS", True), ("U", "B", "SNLS", True), ("U", "C", "FL", True),
         ("U", "C", "BH", False)]
    C5 = [f for f in C if f[2] != "FL"]
    D = [("U", "A", "SNLS", True), ("U", "B", "SNLS", True), ("U", "B", "SNLS", True),
         ("U", "C", "SNLS", True)]
    E = [("U", "C", "BH", False), ("U", "C", "FL", True)]
    got = [tier(x) for x in (A, B, C, C5, D, E)]
    assert got == ["T2", "T1", "T4", "T3", "T2", "T1"], got
    return {}


@case("TC-SK-07")
def _():
    NAM = 12000
    em_collar, bm_collar = em(2500, 1.80), 6000
    em_bh, bm_bh = em(2000, 1.70), 4000
    share = bm_collar / (bm_collar + bm_bh)
    eff = em_collar / (NAM * share)
    return {"EM collar": em_collar, "share": share * 100, "NAM collar": NAM * share, "Eff": eff * 100,
            "EM bh": em_bh}


@case("TC-INC-01")
def _():
    n = 12480 - 600
    g = em(9000, 0.80) + em(1500, 1.20)
    d = dd(50, 0.80)
    # Family grades are not given in spec §11.7; all grades share the same cap in P0.
    im, bonus = incentive_minutes([("X", "C", "U", em(9000, 0.80)), ("Y", "B", "L", em(1500, 1.20))], d)
    tm = P0["theta"] * n
    x = excess(im, tm)
    return {"NAM": n, "EM_g": g, "DD": d, "EM_n": g - d, "M1": (g - d) / n * 100, "M3": g / 12480 * 100,
            "IM": im, "E_inc": im / n * 100, "TM": tm, "X": x, "U": units(x, "T2")}


@case("TC-INC-02")
def _():
    m = month_A()
    im, _ = incentive_minutes([("Seam join", "C", "U", m["EMg"])], m["DD"])
    tm = P0["theta"] * m["NAM"]
    x = excess(im, tm)
    u = units(x, "T2")                       # one total; no time-category split (§11.5)
    return {"A": m["A"], "NAM": m["NAM"], "EM_g": m["EMg"], "DD": m["DD"], "EM_n": m["EMg"] - m["DD"],
            "M1": (m["EMg"] - m["DD"]) / m["NAM"] * 100, "IM": im, "TM": tm, "X": x, "U": u}


@case("TC-INC-03")
def _():
    m = month_B()
    im, bonus = incentive_minutes([("Hemming", "C", "U", m["g_hem"]), ("Sleeve setting", "B", "I", m["g_slv"])],
                                  m["DD"])
    tm = P0["theta"] * m["NAM"]
    x = excess(im, tm)
    x_nopf = excess(m["EMg"] - m["DD"], tm)
    return {"NAM": m["NAM"], "EM_g": m["EMg"], "PF bonus": bonus, "IM": im, "TM": tm, "X": x,
            "U": units(x, "T1"), "X without PF": x_nopf, "M1": (m["EMg"] - m["DD"]) / m["NAM"] * 100}


@case("TC-INC-04")
def _():
    m = month_C()
    fams = [("Collar setting", "A", "U", m["parts"][0]), ("Placket setting", "A", "U", m["parts"][1]),
            ("Buttonholing", "C", "NSE", m["parts"][2]), ("Sleeve setting", "B", "U", m["parts"][3])]
    im, bonus = incentive_minutes(fams, m["DD"])
    tm = P0["theta"] * m["NAM"]
    return {"NAM": m["NAM"], "EM_g": m["EMg"], "IM": im, "TM": tm, "short": tm - im,
            "X": excess(im, tm), "U": units(excess(im, tm), "T4"), "PF bonus": bonus}


@case("TC-INC-05")
def _():
    im, bonus = incentive_minutes([("Sleeve setting", "B", "L", 1500.0)], 0.0, {"Sleeve setting": 2000.0})
    im2, bonus2 = incentive_minutes([("Sleeve setting", "B", "L", 1500.0)], 0.0, {"Sleeve setting": 2400.0})
    return {"bonus": bonus, "IM": im, "bonus after cap": bonus2}


@case("TC-INC-06")
def _():
    th = P0["theta"]
    r1 = P0["ramp"]["R2"][0]
    return {"U normal margin": (0.80 - th) * 100, "learner normal": 0.56 * P0["pf"]["I"] * 100,
            "bar day1": theta_day([(1.0, r1)]) * 100, "U day1 margin": (0.40 - theta_day([(1.0, r1)])) * 100,
            "learner day1": 0.28 * P0["pf"]["I"] * 100}


@case("TC-INC-07")
def _():
    r2 = P0["ramp"]["R2"]
    return {"d1": theta_day([(1.0, r2[0])]) * 100, "d2": theta_day([(1.0, r2[1])]) * 100,
            "d3": theta_day([(1.0, r2[2])]) * 100, "d4": theta_day([(1.0, r2[3])]) * 100,
            "half": theta_day([(0.5, r2[0])]) * 100,
            "R3 raw": P0["theta"] * P0["ramp"]["R3"][0] * 100,
            "R3": theta_day([(1.0, P0["ramp"]["R3"][0])]) * 100,
            "mixed": theta_day([(0.3, r2[0]), (0.2, P0["ramp"]["R1"][1])]) * 100}


@case("TC-INC-08")
def _():
    n_day, days = 465, DAYS
    r2 = P0["ramp"]["R2"][:3]
    perf_ramp = [0.40, 0.55, 0.70]
    im_norm = n_day * days * 0.79
    im_co = n_day * (days - 6) * 0.79 + 2 * n_day * sum(perf_ramp)
    tm_flat = P0["theta"] * n_day * days
    tm_ramp = P0["theta"] * n_day * (days - 6) + 2 * n_day * sum(theta_day([(1.0, r)]) for r in r2)
    x_norm, x_flat, x_ramp = excess(im_norm, tm_flat), excess(im_co, tm_flat), excess(im_co, tm_ramp)
    return {"IM normal": im_norm, "IM changeovers": im_co, "TM flat": tm_flat, "TM ramp": tm_ramp,
            "X normal": x_norm, "X flat": x_flat, "X ramp": x_ramp,
            "flat change": (x_flat / x_norm - 1) * 100, "ramp share": x_ramp / x_norm * 100}


@case("TC-INC-09")
def _():
    im_days, n_days = [250.0, 450.0], [480.0, 480.0]
    tm = sum(P0["theta"] * n for n in n_days)
    monthly = excess(sum(im_days), tm)
    daily = sum(excess(i, P0["theta"] * n) for i, n in zip(im_days, n_days))
    return {"TM": tm, "X": monthly, "daily sum": daily}


@case("TC-INC-10")
def _():
    return {"attendance": 20 / 26 * 100}


@case("TC-INC-11")
def _():
    m = month_A()
    p = dict(P0)
    p["theta"] = 0.72
    im = m["EMg"] - m["DD"]
    tm = p["theta"] * m["NAM"]
    return {"X Nov": excess(im, P0["theta"] * m["NAM"]), "TM Dec": tm, "X Dec": excess(im, tm)}


@case("TC-CO-01")
def _():
    ps01 = [o[5] for o in PS01.values()]
    v1 = ps01[:6] + [0.95, ps01[7]]
    v1_flags = [True] * 6 + [False, True]
    v2 = ps01[:2] + [2.10] + ps01[3:]
    v2_flags = [True, True, False] + [True] * 5
    f1, f2 = familiarity(v1, v1_flags), familiarity(v2, v2_flags)
    f3 = familiarity(ps01, [False] * 8)
    assert (ramp_class(f1), ramp_class(f2), ramp_class(f3)) == ("R0", "R1", "R2")
    return {"SAM V1": sum(v1), "SAM V2": sum(v2), "F V1": f1 * 100, "F V2": f2 * 100, "F new line": f3 * 100}


@case("TC-CO-02")
def _():
    r2 = P0["ramp"]["R2"]
    return {"day3 bar": theta_day([(1.0, r2[2])]) * 100, "new run bar": theta_day([(1.0, 1.0)]) * 100}


@case("TC-CO-04")
def _():
    runs = [[0.45, 0.62, 0.85, 0.95], [0.52, 0.70, 0.90, 0.98],
            [0.48, 0.66, 0.86, 0.97], [0.55, 0.71, 0.92, 1.00]]
    prof = fitted_profile(runs)
    assert len(prof) == 4 and len(runs) < P0["fit_min_runs"]
    return {"d1": prof[0], "d2": prof[1], "d3": prof[2], "d4": prof[3]}


@case("TC-CO-05")
def _():
    run1 = [0.40, 0.55, 0.70, 0.76, 0.78, 0.78, 0.80, 0.79, 0.81, 0.82]
    run2 = [0.40, 0.55, 0.70, 0.76, 0.78, 0.78, 0.80, 0.79]
    p1 = run_plateau(run1)
    assert run_plateau(run2) is None
    return {"plateau": p1 * 100, "r1": run1[0] / p1, "r3": run1[2] / p1}


@case("TC-BAL-01")
def _():
    target, e = 1100, PLATEAU
    takt = T_DAY / target
    hc = target * GARMENT_SAM / (T_DAY * e)
    pitch = GARMENT_SAM / LINE1_OPS
    maxload = takt * e
    layout = [("Placket", 1.60, 5), ("Shoulder", 0.60, 2), ("Collar", 1.80, 5), ("Sleeve", 1.40, 4),
              ("Side", 1.20, 4), ("Hems", 1.70, 5), ("Buttonhole", 1.70, 5)]
    loads = {n: s / k for n, s, k in layout}
    outs = {n: k * T_DAY * e / s for n, s, k in layout}
    mx = max(loads.values())
    bal = GARMENT_SAM / (LINE1_OPS * mx)
    layout31 = [(n, s, (6 if n == "Collar" else k)) for n, s, k in layout]
    loads31 = {n: s / k for n, s, k in layout31}
    out31 = min(k * T_DAY * e / s for n, s, k in layout31)
    bal31 = GARMENT_SAM / (31 * max(loads31.values()))
    assert max(loads, key=loads.get) == "Collar"
    return {"takt": takt, "headcount": hc, "pitch": pitch, "max load": maxload,
            "collar load": loads["Collar"], "line output": min(outs.values()), "balance": bal * 100,
            "output 31": out31, "balance 31": bal31 * 100, "new max 31": max(loads31.values())}


@case("TC-BAL-02")
def _():
    return {"target": 28 * T_DAY * PLATEAU * P0["ramp"]["R2"][1] / GARMENT_SAM}


@case("TC-RT-01")
def _():
    return {"plateau": LINE1_OPS * 60 * PLATEAU / GARMENT_SAM,
            "ramp": 28 * 60 * PLATEAU * P0["ramp"]["R2"][1] / GARMENT_SAM}


RT_TABLE = [  # station, operators, SAM, completed, buffer, starved minutes
    ("Placket attach", 5, 1.60, 148, 5, 0),
    ("Shoulder join", 2, 0.60, 158, 4, 0),
    ("Collar attach", 5, 1.80, 112, 7, 0),
    ("Sleeve attach", 4, 1.40, 118, 1, 12),
    ("Side seam", 4, 1.20, 115, 1, 15),
    ("Sleeve + bottom hem", 5, 1.70, 113, 1, 16),
    ("Buttonhole & button sew", 5, 1.70, 112, 0, 18),
]


@case("TC-RT-02")
def _():
    W = P0["rt_window"]
    out = {}
    ratios = {}
    for name, k, s, done, buf, st in RT_TABLE:
        planned = k * W * PLATEAU / s
        ratios[name] = done / planned
        out["planned " + name] = planned
        out["ratio " + name] = done / planned * 100
    naive = min(ratios, key=ratios.get)
    live_cands = {n: r for (n, k, s, d, b, st), r in zip(RT_TABLE, ratios.values())
                  if st <= P0["starved_share"] * W}
    live = min(live_cands, key=live_cands.get)
    assert naive == "Side seam" and live == "Collar attach", (naive, live)
    target = LINE1_OPS * 60 * PLATEAU / GARMENT_SAM
    out["line"] = RT_TABLE[-1][3] / target * 100
    return out


@case("TC-RT-03")
def _():
    limit = P0["alert_bundle_factor"] * 1.20 * 20
    starved_alerts = [n for n, k, s, d, b, st in RT_TABLE if st > P0["alert_starved"]]
    wip_flags = [n for n, k, s, d, b, st in RT_TABLE if b > P0["wip_cap"]]
    assert starved_alerts == ["Sleeve + bottom hem", "Buttonhole & button sew"], starved_alerts
    assert wip_flags == ["Placket attach", "Shoulder join", "Collar attach"], wip_flags
    return {"bundle limit": limit}


@case("TC-SF-01")
def _():
    rows = [(280e6, 261000), (300e6, 285000), (330e6, 285000)]
    return {"m1": rows[0][0] / rows[0][1], "m2 healthy": rows[1][0] / rows[1][1],
            "m2 unhealthy": rows[2][0] / rows[2][1], "M3 m1": 261000 / 374400 * 100,
            "M3 m2": 285000 / 374400 * 100}


# --------------------------------------------------------------------------------------
# Expected values, as written in IE_Acceptance_Test_Cases_v0.3.md
# --------------------------------------------------------------------------------------
EXPECTED = {
    "TC-TA-01": {"OS": "45", "NAM": "435"},
    "TC-TA-02": {"NAM": "0"},
    "TC-TA-03": {"NAM": "480"},
    "TC-TA-04": {"bundle active": "40", "OS": "20"},
    "TC-TA-05": {"A": "480", "OS counted": "20", "NAM": "460"},
    "TC-EM-01": {"EM_g": "336.0", "DD": "3.6", "EM_n": "332.4"},
    "TC-EM-03": {"first": "15", "DD": "18.0", "DD corrected": "24.0"},
    "TC-EM-05": {"DD": "8.5"},
    "TC-EM-07": {"before": "140.0", "after": "155.0"},
    "TC-MET-01": {"M1": "76.4%", "M3": "70.0%", "gross": "77.2%", "M5": "9.4%", "M6": "86.2%",
                  "M7": "89.7%", "identity": "70.0%"},
    "TC-MET-02": {"M6": "112.0%", "M7": "69.0%", "M1": "76.4%"},
    "TC-MET-03": {"A": "38,640", "OS": "950", "NAM": "37,690", "EM_g": "27,740", "DD": "110",
                  "EM_n": "27,630", "M4": "73.6%", "M1 pooled": "73.3%", "M3": "71.8%", "M5": "2.46%",
                  "identity": "71.8%"},
    "TC-SK-01": {"share hem": "64.15%", "share slv": "35.85%", "NAM hem": "7,813.6", "NAM slv": "4,366.4",
                 "Eff hem": "80.6%", "Eff slv": "59.6%", "DR slv": "2.11%", "weighted": "73.1%"},
    "TC-SK-02": {"volume": "500"},
    "TC-SK-07": {"EM collar": "4,500", "share": "60.0%", "NAM collar": "7,200", "Eff": "62.5%",
                 "EM bh": "3,400"},
    "TC-INC-01": {"NAM": "11,880", "EM_g": "9,000", "DD": "40", "EM_n": "8,960", "M1": "75.4%",
                  "M3": "72.1%", "IM": "9,140", "E_inc": "76.9%", "TM": "8,316", "X": "824", "U": "865.2"},
    "TC-INC-02": {"A": "13,680", "NAM": "13,280", "EM_g": "10,500", "DD": "36", "EM_n": "10,464",
                  "M1": "78.8%", "IM": "10,464", "TM": "9,296", "X": "1,168", "U": "1,226.4"},
    "TC-INC-03": {"NAM": "12,180", "EM_g": "8,960", "PF bonus": "600", "IM": "9,504", "TM": "8,526",
                  "X": "978", "U": "978.0", "X without PF": "378", "M1": "73.1%"},
    "TC-INC-04": {"NAM": "12,230", "EM_g": "8,280", "IM": "8,262", "TM": "8,561", "short": "299",
                  "X": "0", "U": "0", "PF bonus": "0"},
    "TC-INC-05": {"bonus": "40.0", "IM": "1,540.0", "bonus after cap": "0"},
    "TC-INC-06": {"U normal margin": "10.0", "learner normal": "70.0%", "bar day1": "35.0%",
                  "U day1 margin": "5.0", "learner day1": "35.0%"},
    "TC-INC-07": {"d1": "35.0%", "d2": "48.1%", "d3": "61.3%", "d4": "70.0%", "half": "52.5%",
                  "R3 raw": "28.0%", "R3": "30.0%", "mixed": "58.1%"},
    "TC-INC-08": {"IM normal": "9,551.1", "IM changeovers": "8,881.5", "TM flat": "8,463.0",
                  "TM ramp": "7,852.7", "X normal": "1,088.1", "X flat": "418.5", "X ramp": "1,028.8",
                  "flat change": "-61.5%", "ramp share": "94.6%"},
    "TC-INC-09": {"TM": "672", "X": "28", "daily sum": "114"},
    "TC-INC-10": {"attendance": "76.9%"},
    "TC-INC-11": {"X Nov": "1,168", "TM Dec": "9,561.6", "X Dec": "902.4"},
    "TC-CO-01": {"SAM V1": "10.15", "SAM V2": "10.30", "F V1": "90.6%", "F V2": "79.6%", "F new line": "0.0%"},
    "TC-CO-02": {"day3 bar": "61.3%", "new run bar": "70.0%"},
    "TC-CO-04": {"d1": "0.50", "d2": "0.68", "d3": "0.88", "d4": "0.975"},
    "TC-CO-05": {"plateau": "80.0%", "r1": "0.50", "r3": "0.875"},
    "TC-BAL-01": {"takt": "0.436", "headcount": "28.6", "pitch": "0.333", "max load": "0.349",
                  "collar load": "0.360", "line output": "1,067", "balance": "92.6%", "output 31": "1,097",
                  "balance 31": "92.2%", "new max 31": "0.350"},
    "TC-BAL-02": {"target": "739.2"},
    "TC-RT-01": {"plateau": "144", "ramp": "92.4"},
    "TC-RT-02": {"planned Placket attach": "150.0", "planned Shoulder join": "160.0",
                 "planned Collar attach": "133.3", "planned Sleeve attach": "137.1",
                 "planned Side seam": "160.0", "planned Sleeve + bottom hem": "141.2",
                 "planned Buttonhole & button sew": "141.2",
                 "ratio Placket attach": "98.7%", "ratio Shoulder join": "98.8%",
                 "ratio Collar attach": "84.0%", "ratio Sleeve attach": "86.0%", "ratio Side seam": "71.9%",
                 "ratio Sleeve + bottom hem": "80.0%", "ratio Buttonhole & button sew": "79.3%",
                 "line": "77.8%"},
    "TC-RT-03": {"bundle limit": "72"},
    "TC-SF-01": {"m1": "1,072.8", "m2 healthy": "1,052.6", "m2 unhealthy": "1,157.9", "M3 m1": "69.7%",
                 "M3 m2": "76.1%"},
}


# --------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------
def parse(display):
    s = display.replace(",", "").replace("%", "").strip()
    dec = len(s.split(".")[1]) if "." in s else 0
    return float(s), 0.5 * 10 ** (-dec) + 1e-6


def run():
    fails = 0
    for cid, fn in CASES.items():
        try:
            got = fn()
        except AssertionError as e:
            print(f"FAIL {cid}: assertion {e}")
            fails += 1
            continue
        exp = EXPECTED.get(cid, {})
        bad = []
        for k, disp in exp.items():
            if k not in got:
                bad.append(f"{k}: not computed")
                continue
            v, tol = parse(disp)
            if abs(got[k] - v) > tol:
                bad.append(f"{k}: expected {disp}, computed {got[k]:.4f}")
        extra = [k for k in got if k not in exp]
        if extra:
            bad.append(f"no expected value for {extra}")
        if bad:
            fails += 1
            print(f"FAIL {cid}: " + "; ".join(bad))
        else:
            print(f"pass {cid}" + ("" if exp else " (rule checks only)"))
    return fails


def check_doc(path):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"^### (TC-[A-Z]+-\d+)", text, flags=re.M)
    sections = {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}
    fails = 0
    for cid in CASES:
        if cid not in sections:
            print(f"DOC  {cid}: section missing")
            fails += 1
    for cid, exp in EXPECTED.items():
        sec = sections.get(cid, "")
        missing = [d for d in exp.values() if d not in sec]
        if missing:
            fails += 1
            print(f"DOC  {cid}: values not shown in the document: {missing}")
    return fails


if __name__ == "__main__":
    f = run()
    if "--doc" in sys.argv:
        f += check_doc(sys.argv[sys.argv.index("--doc") + 1])
    print(f"\n{len(CASES)} calculated cases, {f} failure(s)")
    sys.exit(1 if f else 0)
