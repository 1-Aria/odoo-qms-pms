# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The acceptance cases (Payroll Acceptance Test Cases v0.6): every earning line and gross pay,
then insurance, PIT, damage compensation, net pay and the employer's funds."""

from odoo.tests import tagged

from .common import D
from .payslip_common import OCT_TO, PayslipCase

WORKER = ["BASE", "PROD", "OT_WD", "EFF"]
STAFF = ["BASE", "PERF", "OT_WD"]
SKILLED = ["SAL", "SKILL", "OT_WD", "INC", "ATT", "TRAVEL"]
OFFICE = ["SAL", "KPI", "PHONE"]


@tagged("post_install", "-at_install")
class TestAcceptance(PayslipCase):
    # ------------------------------------------------------------------ helpers
    def _worker(self, level, **values):
        return self._hire(
            lines=[(self.base, {"in_cell": True}), (self.prod, {"scale_key": level})], **values
        )

    def _staff(self, perf_values):
        # performance pay = the grade cell less the base, which is part of the cell
        return self._hire(lines=[(self.base, {"in_cell": True}), (self.perf, perf_values)])

    def _skilled_lines(self):
        return [
            (self.sal, {"amount": 4500000}),
            (self.skill, {"amount": 1500000}),
            (self.att, {"amount": 300000}),
            (self.travel, {"amount": 200000}),
        ]

    def _office(self, salary, phone, dependents=0, **values):
        employee, contract = self._hire(
            lines=[(self.sal, {"amount": salary}), (self.phone, {"amount": phone})], **values
        )
        self._dependents(employee, dependents)
        return employee, contract

    def _run(self, case, employee, codes, advances=True, **figures):
        self._input(employee, **figures)
        payslip = self._payslip(employee)
        if codes is not None:
            self._expect(payslip, case, codes)
        self._expect_pay(payslip, case, advances=advances)
        return payslip

    def _supervised(self, attainment=1, **figures):
        return dict(figures, attainment=attainment, attainment_source="supervisor")

    def _managed(self, attainment=1, **figures):
        return dict(figures, attainment=attainment, attainment_source="manager")

    def _row(self, case, index):
        return self._cases()[case]["earnings"][index][1]

    # ------------------------------------------------------------------ group G
    def test_g01(self):
        employee, _c = self._worker("Entry")
        self._run("G01", employee, WORKER, **self._supervised(
            ot_hours_json={"WD": 20}, lines=[(self.eff, {"amount": 300000})]))

    def test_g02(self):
        employee, _c = self._worker("S4")
        self._run("G02", employee, WORKER, **self._supervised(
            ot_hours_json={"WD": 30}, lines=[(self.eff, {"amount": 1000000})]))

    def test_g03(self):
        employee, _c = self._worker("S4")
        self._run("G03", employee, ["BASE", "PROD", "OT_WD", None],
                  **self._supervised(0.8, ot_hours_json={"WD": 30}))

    def test_g04(self):
        employee, _c = self._worker("Entry")
        self._run("G04", employee, WORKER, **self._supervised(
            paid_days=24, days_worked=24, unexcused_absences=2, ot_hours_json={"WD": 20},
            lines=[(self.eff, {"amount": 300000})]))

    def test_g05(self):
        employee, _c = self._worker("Entry")
        self._run("G05", employee, WORKER, **self._supervised(
            days_worked=24, ot_hours_json={"WD": 20}, lines=[(self.eff, {"amount": 300000})]))

    def test_g06(self):
        employee, _c = self._worker("S2")
        self._run("G06", employee, ["BASE", "PROD"], **self._supervised())

    def test_g07(self):
        employee, _c = self._worker("Entry")
        self._run("G07", employee, WORKER + ["ONE"], **self._supervised(
            ot_hours_json={"WD": 20},
            lines=[(self.eff, {"amount": 300000}),
                   (self.one, {"amount": 500000, "description": "Project completion"})]))

    def test_g08(self):
        employee, _c = self._worker("Entry", date_end=D(2026, 10, 24), state="close")
        self._damage(employee, 300000)
        self._run("G08", employee, ["BASE", "PROD", "EFF"], **self._supervised(
            paid_days=20, days_worked=20, lines=[(self.eff, {"amount": 200000})]))

    def test_g10(self):
        employee, _c = self._staff({"scale_key": "G2-2"})
        self._dependents(employee, 1)
        self._run("G10", employee, STAFF, **self._managed(ot_hours_json={"WD": 30}))

    def test_g11(self):
        employee, _c = self._staff({"scale_key": "G2-2"})
        self._dependents(employee, 1)
        self._run("G11", employee, STAFF, **self._managed(0.8, ot_hours_json={"WD": 30}))

    def test_g12(self):
        employee, _c = self._staff({"scale_key": "G3-2"})
        self._run("G12", employee, STAFF, **self._managed(ot_hours_json={"WD": 16}))

    def test_g13(self):
        employee, _c = self._staff({"amount": 45000000})
        self._dependents(employee, 2)
        self._run("G13", employee, ["BASE", "PERF"], **self._managed())

    def test_g14(self):
        # the advance is settled by l10n_vn_payroll_account
        employee, _c = self._worker("Entry")
        self._run("G14", employee, WORKER, advances=False, **self._supervised(
            ot_hours_json={"WD": 20}, lines=[(self.eff, {"amount": 300000})]))

    def test_g15(self):
        employee, _c = self._worker("Entry")
        self._run("G15", employee, ["BASE", "PROD"], advances=False, **self._supervised(
            paid_days=10, days_worked=10, unpaid_days=16))

    # ------------------------------------------------------------------ group A
    def test_a01(self):
        employee, _c = self._hire(lines=[
            (self.sal, {"amount": 4500000}),
            (self.att, {"amount": 300000}),
            (self.travel, {"amount": 200000}),
        ])
        employee.l10n_vn_union_member = True
        self._run("A01", employee, ["SAL", "OT_WD", "INC", "ATT", "TRAVEL"],
                  ot_hours_json={"WD": 20}, ie_units=200)

    def test_a02(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("A02", employee, SKILLED, ot_hours_json={"WD": 30}, ie_units=1000)

    def test_a03(self):
        employee, _c = self._hire(lines=[(self.sal, {"amount": 8000000})])
        self._dependents(employee, 1)
        self._run("A03", employee, ["SAL", "OT_WD"], ot_hours_json={"WD": 30})

    def test_a04(self):
        employee, _c = self._hire(lines=[(self.sal, {"amount": 10000000})])
        self._run("A04", employee, ["SAL", "OT_WD", "KPI"], ot_hours_json={"WD": 16},
                  lines=[(self.kpi, {"amount": 1000000})])

    def test_a05(self):
        employee, _c = self._office(14000000, 200000)
        self._run("A05", employee, ["SAL", "OT_WD", "KPI", "PHONE"], ot_hours_json={"WD": 8},
                  lines=[(self.kpi, {"amount": 1500000})])

    def test_a06(self):
        employee, _c = self._office(17000000, 500000, dependents=1)
        self._run("A06", employee, OFFICE, lines=[(self.kpi, {"amount": 3000000})])

    def test_a07(self):
        employee, _c = self._office(18000000, 300000)
        self._run("A07", employee, OFFICE, lines=[(self.kpi, {"amount": 2000000})])

    def test_a08(self):
        employee, _c = self._office(45000000, 1000000, dependents=2)
        self._run("A08", employee, OFFICE, lines=[(self.kpi, {"amount": 8000000})])

    def test_a09(self):
        employee, _c = self._office(70000000, 2000000, dependents=1)
        self._run("A09", employee, OFFICE, lines=[(self.kpi, {"amount": 15000000})])

    # ------------------------------------------------------------------ group B
    def test_b01(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("B01", employee, ["SAL", "SKILL", "OT_WD", "OT_RD", "INC", "ATT", "TRAVEL"],
                  ot_hours_json={"WD": 36, "RD": 16}, ie_units=1200)

    def test_b02(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("B02", employee, SKILLED, paid_days=25, days_worked=25,
                  unexcused_absences=1, ot_hours_json={"WD": 20}, ie_units=900)

    def test_b06(self):
        employee, _c = self._hire(lines=[(self.sal, {"amount": 10000000})])
        self._run("B06", employee, ["SAL"], paid_days=24, days_worked=24, unpaid_days=2)

    # ------------------------------------------------------------------ group C
    def test_c01(self):
        employee, _c = self._hire(
            date_start=D(2026, 10, 15),
            date_end=D(2026, 11, 13),
            l10n_vn_probation_form="contract",
            l10n_vn_participant_type_id=self.env.ref("l10n_vn_payroll.participant_probation").id,
            lines=[(self.sal, {"amount": 4500000}), (self.travel, {"amount": 200000})],
        )
        self._run("C01", employee, ["SAL", "TRAVEL"], scheduled_days=13, paid_days=13,
                  days_worked=13)

    def test_c02(self):
        employee, _probation = self._hire(
            date_start=D(2026, 9, 21),
            date_end=D(2026, 10, 12),
            state="close",
            l10n_vn_probation_form="contract",
            l10n_vn_participant_type_id=self.env.ref("l10n_vn_payroll.participant_probation").id,
            lines=[(self.sal, {"amount": 4500000})],
        )
        self._hire(
            employee=employee,
            date_start=D(2026, 10, 13),
            lines=[
                (self.sal, {"amount": 4500000}),
                (self.att, {"amount": 300000}),
                (self.travel, {"amount": 200000}),
            ],
        )
        self._run("C02", employee, ["SAL", "SAL", "INC", "ATT", "TRAVEL"], ie_units=300,
                  segments=[
                      {"date_from": D(2026, 10, 1), "date_to": D(2026, 10, 12),
                       "paid_days": 10, "days_worked": 10},
                      {"date_from": D(2026, 10, 13), "date_to": OCT_TO,
                       "paid_days": 16, "days_worked": 16},
                  ])

    def test_c03(self):
        employee, _c = self._hire(
            date_end=D(2026, 10, 22),
            state="close",
            lines=[
                (self.sal, {"amount": 4500000}),
                (self.skill, {"amount": 1500000}),
                (self.travel, {"amount": 200000}),
            ],
        )
        self._run("C03", employee, ["SAL", "SKILL", "INC", "LEAVE", "TRAVEL"],
                  scheduled_days=18, paid_days=18, days_worked=18, ie_units=600,
                  lines=[(self.leave, {"amount": self._row("C03", 3),
                                       "description": "Untaken annual leave 5 days"})])

    def test_c04(self):
        employee, _c = self._hire(lines=[
            (self.sal, {"amount": 4500000}),
            (self.skill, {"amount": 1500000}),
        ])
        # one row in the case for two lines of 0: earnings not compared
        self._run("C04", employee, None, paid_days=0, days_worked=0, si_leave_days=26,
                  si_absence_days=26, unpaid_days=26)

    def test_c05(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("C05", employee, ["SAL", "SKILL", "INC", "ATT", "TRAVEL"], paid_days=11,
                  days_worked=11, si_leave_days=15, si_absence_days=15, unpaid_days=15,
                  ie_units=300)

    def test_c06(self):
        employee, _c = self._hire(
            date_start=D(2026, 10, 1),
            l10n_vn_probation_form="clause",
            trial_date_end=D(2026, 10, 7),
            lines=[
                (self.sal, {"amount": 4500000}),
                (self.att, {"amount": 300000}),
                (self.travel, {"amount": 200000}),
            ],
        )
        self._run("C06", employee, ["SAL", "SAL", "ATT", "TRAVEL"], segments=[
            {"date_from": D(2026, 10, 1), "date_to": D(2026, 10, 7),
             "paid_days": 6, "days_worked": 6},
            {"date_from": D(2026, 10, 8), "date_to": OCT_TO,
             "paid_days": 20, "days_worked": 20},
        ])

    # ------------------------------------------------------------------ group D
    def test_d01(self):
        employee, _c = self._hire(lines=[(self.sal, {"amount": 80000000})])
        self._run("D01", employee, ["SAL"])

    def test_d02(self):
        employee, _c = self._hire(
            date_start=D(2026, 10, 1),
            date_end=D(2026, 11, 30),
            lines=[(self.sal, {"amount": 6000000})],
        )
        self._run("D02", employee, ["SAL"])

    def test_d03(self):
        employee, _c = self._hire(lines=[
            (self.sal, {"amount": 10000000}),
            (self.meal, {"amount": 1500000}),
        ])
        self._run("D03", employee, ["SAL", "MEAL"])

    def test_d04(self):
        employee, _c = self._hire(lines=[(self.sal, {"amount": 10000000})])
        self._run("D04", employee, ["SAL", "ANNUAL"],
                  lines=[(self.annual, {"amount": 10000000})])

    def test_d05(self):
        employee, _c = self._office(18000000, 300000)
        self._dependents(employee, 1, date_from=D(2026, 10, 1))
        self._run("D05", employee, OFFICE, lines=[(self.kpi, {"amount": 2000000})])

    def test_d06(self):
        employee, _c = self._hire(
            l10n_vn_participant_type_id=self.env.ref("l10n_vn_payroll.participant_manager").id,
            l10n_vn_declared_si_base=10000000,
            lines=[(self.sal, {"amount": 40000000})],
        )
        self._run("D06", employee, ["SAL"])

    def test_d07(self):
        employee, _c = self._hire(
            date_start=D(2026, 10, 1),
            date_end=D(2026, 11, 30),
            lines=[(self.daily, {"amount": 350000})],
        )
        self._run("D07", employee, ["DAILY"])

    def test_d08(self):
        self.supp.active = True
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("D08", employee, ["SAL", "SKILL", "OT_WD", "SUPP", "INC", "ATT", "TRAVEL"],
                  ot_hours_json={"WD": 30}, ie_units=1000)

    # ------------------------------------------------------------------ group E
    def test_e01(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("E01", employee, SKILLED + ["OT_WD"], ot_hours_json={"WD": 20},
                  ie_units=1000, lines=[(self.ot_wd, {
                      "amount": self._row("E01", -1),
                      "hours": 4,
                      "period_ref": D(2026, 9, 1),
                      "description": "OT workday 4 h",
                  })])

    def test_e02(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._damage(employee, 3000000)
        self._run("E02", employee, SKILLED, ot_hours_json={"WD": 20}, ie_units=1000)
