# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from dateutil.relativedelta import relativedelta

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import D
from .payslip_common import OCT_FROM, OCT_TO, PayslipCase


@tagged("post_install", "-at_install")
class TestChecks(PayslipCase):
    # ------------------------------------------------------------------ helpers
    def _salaried(self, amount=4500000, extra=(), **values):
        employee, contract = self._hire(lines=[(self.sal, {"amount": amount}), *extra], **values)
        self._identify(employee)
        return employee, contract

    def _worker(self, **line_values):
        employee, contract = self._hire(
            lines=[(self.base, {"in_cell": True}), (self.prod, dict({"scale_key": "Entry"},
                                                                    **line_values))]
        )
        self._identify(employee)
        return employee, contract

    def _new_payslip(self, employee):
        """A payslip as OCA's batch makes it, not calculated."""
        Payslip = self.env["hr.payslip"]
        vals = Payslip.get_payslip_vals(OCT_FROM, OCT_TO, employee.id)["value"]
        return Payslip.create(
            {
                "employee_id": employee.id,
                "date_from": OCT_FROM,
                "date_to": OCT_TO,
                "contract_id": vals.get("contract_id"),
                "struct_id": vals.get("struct_id"),
                "worked_days_line_ids": [
                    Command.create(v) for v in vals.get("worked_days_line_ids", [])
                ],
                "company_id": self.company.id,
            }
        )

    def _done_month(self, employee, months_back, lines=(), net=1):
        """A done payslip of an earlier month whose snapshot holds ``lines`` and ``net``."""
        month = OCT_FROM - relativedelta(months=months_back)
        return self.env["hr.payslip"].create(
            {
                "employee_id": employee.id,
                "date_from": month,
                "date_to": month + relativedelta(day=31),
                "company_id": self.company.id,
                "state": "done",
                "l10n_vn_context": {"lines": list(lines), "net": net},
            }
        )

    @staticmethod
    def _full(component, attainment=1.0):
        return {"component_id": component.id, "attainment": attainment, "condition": None}

    def _travel_in_ot_base(self):
        self.travel.in_ot_base = True
        return self._salaried(extra=[(self.travel, {"amount": 200000})])

    # ------------------------------------------------------------------ levels (D60)
    def test_level_default(self):
        employee, _c = self._travel_in_ot_base()
        self._input(employee)
        result = self._results(self._payslip(employee), "nature")
        self.assertEqual(result.level, "warning")
        self.assertEqual(result.component_id, self.travel)

    def test_level_parameter(self):
        self._parameter_text("vn.check.nature", "note")
        employee, _c = self._travel_in_ot_base()
        self._input(employee)
        self.assertEqual(self._results(self._payslip(employee), "nature").level, "note")

    def test_level_per_component(self):
        self._parameter_text("vn.check.nature", "error")
        self._parameter_text("vn.check.nature.TEST_TRAVEL", "off")
        employee, _c = self._travel_in_ot_base()
        self._input(employee)
        self.assertFalse(self._results(self._payslip(employee), "nature"))

    def test_bad_level_value(self):
        self._parameter_text("vn.check.nature", "maybe")
        employee, _c = self._travel_in_ot_base()
        self._input(employee)
        self.assertEqual(self._results(self._payslip(employee), "nature").level, "warning")

    def test_integrity_ignores_level(self):
        self._parameter_text("vn.check.negative_net", "off")
        charge = self._component("CHARGE", kind="deduction", legal_nature="damage",
                                 amount_source="entered", pit_treatment=False, proration=False)
        self._rule(charge)
        employee, _c = self._salaried()
        self._input(employee, lines=[(charge, {"amount": 6000000})])
        self.assertEqual(self._results(self._payslip(employee), "negative_net").level, "error")

    # ------------------------------------------------------------------ integrity
    def test_period_open(self):
        employee, _c = self._salaried()
        self._input(employee)
        payslip = self._payslip(employee)
        result = self._results(payslip, "period_open")
        self.assertEqual(result.level, "error")
        self.assertIn("2026-10", result.message)
        self.period.attendance_closed = True
        payslip.compute_sheet()
        self.assertFalse(self._results(payslip, "period_open"))

    def test_stop_keeps_batch(self):
        stopped_employee, _c = self._worker()
        computed_employee, _c = self._worker()
        self._input(stopped_employee)
        self._input(computed_employee, attainment=1, attainment_source="supervisor")
        stopped = self._new_payslip(stopped_employee)
        computed = self._new_payslip(computed_employee)
        (stopped | computed).compute_sheet()
        self._stopped(stopped, "missing_attainment", "attainment")
        self.assertEqual(stopped.state, "draft")
        self.assertEqual(computed.state, "verify")
        self.assertTrue(self._totals(computed, "NET"))

    def test_unapproved_entry(self):
        employee, _c = self._salaried()
        self._input(employee, lines=[(self.one, {"amount": 500000, "approved": False})])
        result = self._results(self._payslip(employee), "unapproved_entry")
        self.assertEqual(result.level, "error")
        self.assertEqual(result.component_id, self.one)

    def test_missing_ids(self):
        employee, _c = self._hire(lines=[(self.sal, {"amount": 4500000})])
        self._input(employee)
        payslip = self._payslip(employee)
        message = self._results(payslip, "missing_ids").message
        for missing in ("bank account", "personal ID number", "SI number"):
            self.assertIn(missing, message)
        self._identify(employee)
        payslip.compute_sheet()
        self.assertFalse(self._results(payslip, "missing_ids"))

    # ------------------------------------------------------------------ legal
    def test_min_wage(self):
        employee, _c = self._salaried(3500000)
        self._input(employee)
        payslip = self._payslip(employee)
        self.assertEqual(self._results(payslip, "min_wage").level, "error")
        self._parameter_text("vn.check.min_wage", "warning")
        payslip.compute_sheet()
        self.assertEqual(self._results(payslip, "min_wage").level, "warning")

    def test_daily_min(self):
        employee, _c = self._hire(lines=[(self.daily, {"amount": 100000})])
        self._identify(employee)
        self._input(employee)
        result = self._results(self._payslip(employee), "daily_min")
        self.assertEqual(result.level, "error")
        self.assertEqual(result.component_id, self.daily)

    def test_probation_length(self):
        employee, contract = self._salaried(
            date_start=D(2026, 10, 1),
            l10n_vn_probation_form="clause",
            trial_date_end=D(2026, 10, 14),
            l10n_vn_probation_job="vocational",
        )
        self._input(employee, segments=self._halves())
        payslip = self._payslip(employee)
        self.assertFalse(self._results(payslip, "probation_length"))
        contract.l10n_vn_probation_job = "other"
        payslip.compute_sheet()
        self.assertEqual(self._results(payslip, "probation_length").level, "warning")
        contract.l10n_vn_probation_job = "vocational"
        rate = self.env["base.time.parameter"].search(
            [("code", "=", "vn.policy.probation_rate"), ("company_id", "=", self.company.id)]
        )
        rate.version_ids.value = "0.80"
        payslip.compute_sheet()
        self.assertIn("rate", self._results(payslip, "probation_length").message)

    def test_deduction_kind(self):
        charge = self._component("UNIFORM", kind="deduction", legal_nature="adjustment",
                                 amount_source="entered", pit_treatment=False, proration=False)
        self._rule(charge)
        employee, _c = self._salaried()
        self._input(employee, lines=[(charge, {"amount": 100000})])
        result = self._results(self._payslip(employee), "deduction_kind")
        self.assertEqual(result.level, "warning")
        self.assertEqual(result.component_id, charge)

    def test_ot_limit(self):
        employee, _c = self._salaried()
        self._input(employee, ot_hours_json={"WD": 36, "RD": 16})
        self.assertEqual(self._results(self._payslip(employee), "ot_limit").level, "warning")
        employee, _c = self._salaried()
        self._input(employee, ot_hours_json={"WD": 20}, ot_hours_ytd=290)
        self.assertIn("year", self._results(self._payslip(employee), "ot_limit").message)

    # ------------------------------------------------------------------ policy
    def test_variable_constant(self):
        employee, _c = self._worker()
        self._input(employee, attainment=1, attainment_source="supervisor")
        earlier = [self._done_month(employee, n, [self._full(self.prod)]) for n in range(1, 6)]
        payslip = self._payslip(employee)
        result = self._results(payslip, "variable_constant")
        self.assertEqual(result.level, "warning")
        self.assertEqual(result.component_id, self.prod)
        earlier[2].l10n_vn_context = {"lines": [self._full(self.prod, 0.9)], "net": 1}
        payslip.compute_sheet()
        self.assertFalse(self._results(payslip, "variable_constant"))

        self._parameter_text("vn.check.variable_constant.TEST_PERF", "note")
        staff, _c = self._hire(
            lines=[(self.base, {"in_cell": True}), (self.perf, {"scale_key": "G2-2"})]
        )
        self._identify(staff)
        self._input(staff, attainment=1, attainment_source="manager")
        for n in range(1, 6):
            self._done_month(staff, n, [self._full(self.perf)])
        self.assertEqual(
            self._results(self._payslip(staff), "variable_constant").level, "note"
        )

    def test_net_change(self):
        employee, _c = self._salaried()
        self._input(employee)
        september = self._done_month(employee, 1, net=3000000)
        payslip = self._payslip(employee)
        self.assertEqual(payslip.l10n_vn_context["net"], 4027500)
        self.assertEqual(self._results(payslip, "net_change").level, "warning")
        september.l10n_vn_context = {"lines": [], "net": 4000000}
        payslip.compute_sheet()
        self.assertFalse(self._results(payslip, "net_change"))

    def test_ie_scope(self):
        employee, _c = self._salaried()
        employee.l10n_vn_pay_group = "office"
        self._input(employee, ie_units=100)
        payslip = self._payslip(employee)
        self.assertEqual(self._results(payslip, "ie_scope").level, "warning")
        employee.l10n_vn_pay_group = "worker"
        payslip.compute_sheet()
        self.assertFalse(self._results(payslip, "ie_scope"))

    def test_level_review(self):
        employee, _c = self._worker(review_date=D(2026, 10, 15))
        self._input(employee, attainment=1, attainment_source="supervisor")
        result = self._results(self._payslip(employee), "level_review")
        self.assertEqual(result.level, "warning")
        self.assertEqual(result.component_id, self.prod)

    def test_dependent_document(self):
        employee, _c = self._salaried()
        self._dependents(employee, 1)
        self._input(employee)
        payslip = self._payslip(employee)
        self.assertEqual(self._results(payslip, "dependent_document").level, "warning")
        employee.relative_ids.l10n_vn_document = base64.b64encode(b"registration")
        payslip.compute_sheet()
        self.assertFalse(self._results(payslip, "dependent_document"))

    # ------------------------------------------------------------------ runner
    def test_finder_error(self):
        self.env["base.time.parameter"].search(
            [("code", "=", "vn.policy.constant_months"), ("company_id", "=", self.company.id)]
        ).unlink()
        employee, _c = self._worker()
        self._input(employee, attainment=1, attainment_source="supervisor")
        payslip = self._payslip(employee)
        result = self._results(payslip, "variable_constant")
        self.assertEqual(result.level, "error")
        self.assertIn("vn.policy.constant_months", result.message)
        self.assertTrue(self._results(payslip, "period_open"), "the other checks still ran")

    def test_note_by_reviewer(self):
        employee, _c = self._salaried()
        self._input(employee)
        result = self._results(self._payslip(employee), "period_open")
        reviewer = self._user("test.l10n_vn_payroll.check_reviewer",
                              ["l10n_vn_payroll.group_payroll_reviewer"])
        officer = self._user("test.l10n_vn_payroll.check_officer", ["payroll.group_payroll_user"])
        self._as(reviewer)["l10n_vn.payroll.check.result"].browse(result.id).note = "Closing today"
        self.assertEqual(result.noted_by, reviewer)
        as_officer = self._as(officer)["l10n_vn.payroll.check.result"].browse(result.id)
        self.assertTrue(as_officer.message)
        with self.assertRaises(AccessError):
            as_officer.note = "Officer's note"

    def test_results_replaced(self):
        employee, _c = self._travel_in_ot_base()
        self._input(employee)
        payslip = self._payslip(employee)
        payslip.compute_sheet()
        self.assertEqual(len(self._results(payslip, "nature")), 1)
        self.travel.in_ot_base = False
        payslip.compute_sheet()
        self.assertFalse(self._results(payslip, "nature"))

    def test_payslip_level(self):
        self.period.attendance_closed = True
        self._parameter_text("vn.check.ie_scope", "note")
        employee, _c = self._travel_in_ot_base()
        employee.l10n_vn_pay_group = "office"
        inp = self._input(employee, ie_units=100)
        payslip = self._payslip(employee)
        self.assertEqual(set(payslip.l10n_vn_check_result_ids.mapped("level")),
                         {"warning", "note"})
        self.assertEqual(payslip.l10n_vn_check_level, "warning")
        self.travel.in_ot_base = False
        inp.ie_units = 0
        payslip.compute_sheet()
        self.assertFalse(payslip.l10n_vn_check_result_ids)
        self.assertFalse(payslip.l10n_vn_check_level)

    def test_snapshot_checks(self):
        employee, _c = self._travel_in_ot_base()
        self._input(employee)
        payslip = self._payslip(employee)
        listed = {(c["code"], c["level"], c["message"]) for c in payslip.l10n_vn_context["checks"]}
        recorded = {(r.check_id.code, r.level, r.message)
                    for r in payslip.l10n_vn_check_result_ids}
        self.assertEqual(listed, recorded)
        self.assertIn("nature", {c["code"] for c in payslip.l10n_vn_context["checks"]})
