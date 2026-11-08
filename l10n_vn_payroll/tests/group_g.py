# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Group G of the acceptance cases (Payroll Acceptance Test Cases v0.6): the current scheme.

Shared by l10n_vn_payroll's own acceptance tests and by modules that ship the current
scheme as configuration, which run the same cases on their own data.
"""

from .common import D

WORKER = ["BASE", "PROD", "OT_WD", "EFF"]
STAFF = ["BASE", "PERF", "OT_WD"]


class GroupGCases:
    """Group G tests and the helpers they share; mixed into a PayslipCase.

    Not a TestCase: a class that mixes it in needs ``allow_inherited_tests_method``.
    """

    # ------------------------------------------------------------------ helpers
    def _worker(self, level, **values):
        return self._hire(
            lines=[(self.base, {"in_cell": True}), (self.prod, {"scale_key": level})], **values
        )

    def _staff(self, perf_values):
        # performance pay = the grade cell less the base, which is part of the cell
        return self._hire(lines=[(self.base, {"in_cell": True}), (self.perf, perf_values)])

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
