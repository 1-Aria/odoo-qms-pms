# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The garment company's current pay scheme (Pay Policy v0.5 §3–§11) as constants.

Read by ``res.company._l10n_vn_garment_load()``. Names are (English, Vietnamese).
"""

DATE_FROM = "2026-01-01"

# (code, name, type, value as stored text)
PARAMETERS = [
    ("vn.policy.region", "Minimum wage region", "string", "IV"),
    ("vn.policy.std_days", "Standard days per month", "integer", "26"),
    ("vn.policy.base_salary", "Base salary", "float", "3700000"),
    ("vn.policy.probation_rate", "Probation pay rate", "float", "0.85"),
    ("vn.policy.attainment_cap", "Attainment and score cap", "float", "1"),
    ("vn.policy.ot_min_hours_day", "Minimum OT hours counted per day", "float", "0.8"),
    (
        "vn.policy.constant_months",
        "Months of unchanged variable pay before a check",
        "integer",
        "6",
    ),
    (
        "vn.policy.net_change",
        "Net pay change from last month before a check",
        "float",
        "0.30",
    ),
    (
        "vn.check.variable_constant.PERF",
        "Check level: performance pay unchanged",
        "string",
        "note",
    ),
]

# (code, name, kind, {key: amount})
SCALES = [
    (
        "PROD",
        ("Productivity levels", "Bậc năng suất"),
        "level",
        {
            "Entry": 800000,
            "S1": 1300000,
            "S2": 1800000,
            "S3": 2300000,
            "S4": 2800000,
        },
    ),
    (
        "GRADE",
        ("Grades and steps", "Ngạch, bậc lương"),
        "grade_step",
        {
            "G1-1": 5500000,
            "G1-2": 6000000,
            "G1-3": 6500000,
            "G2-1": 7500000,
            "G2-2": 8000000,
            "G2-3": 8500000,
            "G3-1": 9000000,
            "G3-2": 10000000,
            "G3-3": 11000000,
            "G4-1": 13000000,
            "G4-2": 14000000,
            "G4-3": 15000000,
            "G5-1": 16000000,
            "G5-2": 17000000,
            "G5-3": 18000000,
        },
    ),
]

# (code, name, component kinds)
CATEGORIES = [
    ("EARN", ("Earnings", "Thu nhập"), ("earning",)),
    ("DED", ("Deductions", "Khấu trừ"), ("deduction",)),
    ("ER", ("Employer contributions", "Công ty đóng"), ("employer",)),
    ("TOTAL", ("Totals", "Tổng cộng"), ("total", "info")),
]


def _earning(**values):
    return dict({"kind": "earning", "condition": "none"}, **values)


def _ot(category, nature="overtime"):
    return _earning(
        legal_nature=nature,
        amount_source="ot",
        pit_treatment="ot",
        section="ot",
        ot_category=category,
    )


def _entered(nature="bonus", pit="taxable", section="bonus"):
    return _earning(
        legal_nature=nature, amount_source="entered", pit_treatment=pit, section=section
    )


def _engine(kind, nature, section):
    return {
        "kind": kind,
        "legal_nature": nature,
        "amount_source": "engine",
        "section": section,
        "condition": "none",
    }


_SALARY = {"pit_treatment": "taxable", "section": "salary", "probation_applies": True}

# (code, name, field values); sequence in list order, by 10. ``scale`` names a code
# of SCALES; the loader replaces it with the company's scale.
COMPONENTS = [
    (
        "BASE",
        ("Base salary", "Lương cơ bản"),
        _earning(
            legal_nature="job_salary",
            amount_source="parameter",
            amount_parameter="vn.policy.base_salary",
            in_si_base=True,
            in_ot_base=True,
            proration="paid_days",
            sets_wage=True,
            **_SALARY,
        ),
    ),
    (
        "PROD",
        ("Productivity pay", "Lương năng suất"),
        _earning(
            legal_nature="variable_salary",
            amount_source="scale",
            scale="PROD",
            in_ot_base=True,
            proration="paid_days",
            variable=True,
            attainment_source="supervisor",
            **_SALARY,
        ),
    ),
    (
        "PERF",
        ("Performance pay", "Lương hiệu quả công việc"),
        _earning(
            legal_nature="variable_salary",
            amount_source="scale_remainder",
            scale="GRADE",
            in_ot_base=True,
            proration="paid_days",
            variable=True,
            attainment_source="manager",
            **_SALARY,
        ),
    ),
    (
        "DAILY",
        ("Daily wage", "Lương ngày"),
        _earning(
            legal_nature="job_salary",
            amount_source="line",
            in_si_base=True,
            in_ot_base=True,
            proration="per_day",
            **_SALARY,
        ),
    ),
    (
        "DUTY",
        ("Responsibility allowance", "Phụ cấp trách nhiệm"),
        _earning(
            legal_nature="fixed_allowance",
            amount_source="line",
            in_si_base=True,
            in_ot_base=True,
            proration="paid_days",
            active=False,
            **_SALARY,
        ),
    ),
    ("OT_WD", ("Overtime, workday", "Làm thêm giờ ngày thường"), _ot("WD")),
    (
        "OT_RD",
        ("Overtime, weekly rest day", "Làm thêm giờ ngày nghỉ hằng tuần"),
        _ot("RD"),
    ),
    (
        "OT_HOL",
        ("Overtime, public holiday", "Làm thêm giờ ngày lễ, Tết"),
        _ot("HOL"),
    ),
    (
        "OT_NIGHT",
        ("Night work premium", "Phụ cấp làm việc ban đêm"),
        _ot("NIGHT", nature="night"),
    ),
    (
        "OT_NWD",
        ("Night overtime, workday", "Làm thêm giờ ban đêm ngày thường"),
        _ot("NWD"),
    ),
    (
        "OT_NWD_AFTER",
        (
            "Night overtime, workday after daytime overtime",
            "Làm thêm giờ ban đêm ngày thường sau làm thêm ban ngày",
        ),
        _ot("NWD_AFTER"),
    ),
    (
        "OT_NRD",
        ("Night overtime, weekly rest day", "Làm thêm giờ ban đêm ngày nghỉ hằng tuần"),
        _ot("NRD"),
    ),
    (
        "OT_NHOL",
        ("Night overtime, public holiday", "Làm thêm giờ ban đêm ngày lễ, Tết"),
        _ot("NHOL"),
    ),
    (
        "ATT",
        ("Attendance bonus", "Thưởng chuyên cần"),
        _earning(
            legal_nature="bonus",
            amount_source="parameter",
            amount_parameter="vn.policy.attendance_bonus",
            pit_treatment="taxable",
            proration="none",
            condition="attendance",
            section="bonus",
            active=False,
        ),
    ),
    ("EFF", ("Efficiency bonus", "Thưởng hiệu suất"), _entered()),
    ("ONE", ("One-time bonus", "Thưởng đột xuất"), _entered()),
    ("ANNUAL", ("Annual bonus", "Thưởng tháng 13"), _entered()),
    (
        "LEAVE",
        ("Untaken leave pay", "Tiền lương ngày phép chưa nghỉ"),
        _entered(nature="leave_pay", pit="exempt", section="other"),
    ),
    (
        "PHONE",
        ("Phone allowance", "Phụ cấp điện thoại"),
        _earning(
            legal_nature="welfare",
            amount_source="line",
            pit_treatment="exempt",
            proration="none",
            section="other",
            active=False,
        ),
    ),
    ("GROSS", ("Gross pay", "Tổng thu nhập"), _engine("total", "total", "total")),
    (
        "EE_SI",
        ("Social insurance (employee)", "BHXH (người lao động)"),
        _engine("deduction", "statutory", "deduction"),
    ),
    (
        "EE_HI",
        ("Health insurance (employee)", "BHYT (người lao động)"),
        _engine("deduction", "statutory", "deduction"),
    ),
    (
        "EE_UI",
        ("Unemployment insurance (employee)", "BHTN (người lao động)"),
        _engine("deduction", "statutory", "deduction"),
    ),
    (
        "DUES",
        ("Union dues", "Đoàn phí công đoàn"),
        _engine("deduction", "union", "deduction"),
    ),
    (
        "PIT",
        ("Personal income tax", "Thuế TNCN"),
        _engine("deduction", "statutory", "deduction"),
    ),
    (
        "DAMAGE",
        ("Damage compensation", "Bồi thường thiệt hại"),
        _engine("deduction", "damage", "deduction"),
    ),
    ("NET", ("Net pay", "Thực lĩnh"), _engine("total", "total", "total")),
    ("ADVANCE", ("Advance settled", "Đã tạm ứng"), _engine("info", "advance", "total")),
    ("TO_PAY", ("Amount to pay", "Còn được lĩnh"), _engine("total", "total", "total")),
    (
        "ER_PENSION",
        (
            "Pension and survivorship (employer)",
            "BHXH hưu trí, tử tuất (công ty)",
        ),
        _engine("employer", "statutory", "employer"),
    ),
    (
        "ER_SICKNESS",
        ("Sickness and maternity (employer)", "BHXH ốm đau, thai sản (công ty)"),
        _engine("employer", "statutory", "employer"),
    ),
    (
        "ER_ACCIDENT",
        ("Occupational accident (employer)", "BHXH tai nạn lao động (công ty)"),
        _engine("employer", "statutory", "employer"),
    ),
    (
        "ER_HI",
        ("Health insurance (employer)", "BHYT (công ty)"),
        _engine("employer", "statutory", "employer"),
    ),
    (
        "ER_UI",
        ("Unemployment insurance (employer)", "BHTN (công ty)"),
        _engine("employer", "statutory", "employer"),
    ),
    (
        "UNION_FEE",
        ("Union fee", "Kinh phí công đoàn"),
        _engine("employer", "statutory", "employer"),
    ),
]

ENGINE_CODES = {
    "GROSS",
    "EE_SI",
    "EE_HI",
    "EE_UI",
    "DUES",
    "PIT",
    "DAMAGE",
    "NET",
    "ADVANCE",
    "TO_PAY",
    "ER_PENSION",
    "ER_SICKNESS",
    "ER_ACCIDENT",
    "ER_HI",
    "ER_UI",
    "UNION_FEE",
}

STRUCTURE = (
    "VN_GARMENT",
    ("Vietnamese pay — current scheme", "Lương — chế độ hiện hành"),
)
