# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The earning lines and gross pay of the acceptance cases (Payroll Acceptance Test Cases)."""

from odoo.tests import tagged

from .common import D
from .payslip_common import OCT_TO, PayslipCase

WORKER = ["BASE", "PROD", "OT_WD", "EFF"]
STAFF = ["BASE", "PERF", "OT_WD"]
SKILLED = ["SAL", "SKILL", "OT_WD", "INC", "ATT", "TRAVEL"]


@tagged("post_install", "-at_install")
class TestAcceptanceEarnings(PayslipCase):
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

    def _run(self, case, employee, codes, **figures):
        self._input(employee, **figures)
        self._expect(self._payslip(employee), case, codes)

    def _supervised(self, attainment=1, **figures):
        return dict(figures, attainment=attainment, attainment_source="supervisor")

    def _managed(self, attainment=1, **figures):
        return dict(figures, attainment=attainment, attainment_source="manager")

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

    def test_g07(self):
        employee, _c = self._worker("Entry")
        self._run("G07", employee, WORKER + ["ONE"], **self._supervised(
            ot_hours_json={"WD": 20},
            lines=[(self.eff, {"amount": 300000}),
                   (self.one, {"amount": 500000, "description": "Project completion"})]))

    def test_g08(self):
        employee, _c = self._worker("Entry", date_end=D(2026, 10, 24), state="close")
        self._run("G08", employee, ["BASE", "PROD", "EFF"], **self._supervised(
            paid_days=20, days_worked=20, lines=[(self.eff, {"amount": 200000})]))

    def test_g10(self):
        employee, _c = self._staff({"scale_key": "G2-2"})
        self._run("G10", employee, STAFF, **self._managed(ot_hours_json={"WD": 30}))

    def test_g11(self):
        employee, _c = self._staff({"scale_key": "G2-2"})
        self._run("G11", employee, STAFF, **self._managed(0.8, ot_hours_json={"WD": 30}))

    def test_g12(self):
        employee, _c = self._staff({"scale_key": "G3-2"})
        self._run("G12", employee, STAFF, **self._managed(ot_hours_json={"WD": 16}))

    def test_g13(self):
        employee, _c = self._staff({"amount": 45000000})
        self._run("G13", employee, ["BASE", "PERF"], **self._managed())

    # ------------------------------------------------------------------ groups A–E
    def test_a01(self):
        employee, _c = self._hire(lines=[
            (self.sal, {"amount": 4500000}),
            (self.att, {"amount": 300000}),
            (self.travel, {"amount": 200000}),
        ])
        self._run("A01", employee, ["SAL", "OT_WD", "INC", "ATT", "TRAVEL"],
                  ot_hours_json={"WD": 20}, ie_units=200)

    def test_a02(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("A02", employee, SKILLED, ot_hours_json={"WD": 30}, ie_units=1000)

    def test_b01(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("B01", employee, ["SAL", "SKILL", "OT_WD", "OT_RD", "INC", "ATT", "TRAVEL"],
                  ot_hours_json={"WD": 36, "RD": 16}, ie_units=1200)

    def test_b02(self):
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("B02", employee, SKILLED, paid_days=25, days_worked=25,
                  unexcused_absences=1, ot_hours_json={"WD": 20}, ie_units=900)

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

    def test_e01(self):
        adjustment = self._cases()["E01"]["earnings"][-1][1]
        employee, _c = self._hire(lines=self._skilled_lines())
        self._run("E01", employee, SKILLED + ["OT_WD"], ot_hours_json={"WD": 20},
                  ie_units=1000, lines=[(self.ot_wd, {
                      "amount": adjustment,
                      "hours": 4,
                      "period_ref": D(2026, 9, 1),
                      "description": "OT workday 4 h",
                  })])
