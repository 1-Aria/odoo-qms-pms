# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import ROUND_HALF_UP, Decimal

from odoo import Command, fields
from odoo.tests import tagged

from .common import D
from .payslip_common import OCT_TO, PayslipCase


@tagged("post_install", "-at_install")
class TestPayContext(PayslipCase):
    def _pieces(self, inp):
        return [(p["date_from"], p["date_to"], p["probation"]) for p in inp._l10n_vn_pieces()]

    def test_pieces(self):
        employee, _contract = self._hire(
            lines=self._sal_change(),
            l10n_vn_probation_form="clause",
            trial_date_end=D(2026, 10, 7),
        )
        inp = self._input(employee)
        self.assertEqual(
            self._pieces(inp),
            [
                (D(2026, 10, 1), D(2026, 10, 7), True),
                (D(2026, 10, 8), D(2026, 10, 14), False),
                (D(2026, 10, 15), OCT_TO, False),
            ],
        )

    def test_pieces_gap(self):
        employee, _first = self._hire(date_end=D(2026, 10, 10), state="close")
        self._hire(employee=employee, date_start=D(2026, 10, 20))
        inp = self.env["l10n_vn.payroll.input"].create(
            {"period_id": self.period.id, "employee_id": employee.id}
        )
        expected = [(D(2026, 10, 1), D(2026, 10, 10)), (D(2026, 10, 20), OCT_TO)]
        self.assertEqual([p[:2] for p in self._pieces(inp)], expected)
        inp._l10n_vn_build()
        self.assertEqual([(s.date_from, s.date_to) for s in inp.segment_ids], expected)

    def test_missing_segments(self):
        employee, _contract = self._hire(lines=self._sal_change())
        self._input(employee)
        self._stopped(
            self._payslip(employee), "missing_segments", "2026-10-01–2026-10-14, 2026-10-15–2026-10-31"
        )

    def test_bases(self):
        components = {}
        for proration, amount in (
            ("paid_days", 2600000),
            ("days_worked", 2600000),
            ("none", 300000),
            ("per_day", 100000),
        ):
            component = self._component(f"B_{proration.upper()}", proration=proration)
            self._rule(component)
            components[proration] = (component, {"amount": amount})
        employee, _contract = self._hire(lines=list(components.values()))
        self._input(employee, paid_days=24, days_worked=22)
        payslip = self._payslip(employee)
        self.assertEqual(self._totals(payslip, "B_PAID_DAYS"), [2400000])
        self.assertEqual(self._totals(payslip, "B_DAYS_WORKED"), [2200000])
        self.assertEqual(self._totals(payslip, "B_NONE"), [300000])
        self.assertEqual(self._totals(payslip, "B_PER_DAY"), [2400000])

    def test_none_paid_once(self):
        employee, _contract = self._hire(
            lines=self._sal_change() + [(self.travel, {"amount": 200000})]
        )
        self._input(employee, segments=self._halves())
        payslip = self._payslip(employee)
        travel = payslip.line_ids.filtered(lambda line: line.code == "TEST_TRAVEL")
        self.assertEqual(travel.mapped("total"), [200000])
        self.assertFalse(travel.l10n_vn_date_from)

    def test_missing_attainment(self):
        employee, _contract = self._hire(lines=[(self.prod, {"scale_key": "Entry"})])
        inp = self._input(employee)
        self._stopped(self._payslip(employee), "missing_attainment", "attainment")
        inp.write({"attainment_source": "supervisor", "attainment": 0})
        self.assertEqual(self._totals(self._payslip(employee), "PROD"), [0])

    def test_attainment_cap(self):
        employee, _contract = self._hire(lines=[(self.prod, {"scale_key": "Entry"})])
        self._input(employee, attainment=1.2, attainment_source="supervisor")
        self.assertEqual(self._totals(self._payslip(employee), "PROD"), [800000])

    def test_attendance_condition(self):
        employee, _contract = self._hire(lines=[(self.att, {"amount": 300000})])
        inp = self._input(employee, late_arrivals=3)
        self.assertEqual(self._totals(self._payslip(employee), "ATT"), [0])
        inp.late_arrivals = 2
        self.assertEqual(self._totals(self._payslip(employee), "ATT"), [300000])
        inp.unexcused_absences = 1
        self.assertEqual(self._totals(self._payslip(employee), "ATT"), [0])

    def test_unapproved_not_paid(self):
        employee, _contract = self._hire()
        inp = self._input(employee, lines=[(self.eff, {"amount": 300000, "approved": False})])
        payslip = self._payslip(employee)
        self.assertFalse(self._totals(payslip, "EFF"))
        self.assertEqual(payslip.l10n_vn_context["unapproved"], inp.line_ids.ids)
        inp.line_ids.sudo().write(
            {"approved_by": self.env.uid, "approved_at": fields.Datetime.now()}
        )
        payslip.compute_sheet()
        self.assertEqual(self._totals(payslip, "EFF"), [300000])

    def test_ot_without_component(self):
        self.ot_hol.active = False
        employee, _contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        self._input(employee, ot_hours_json={"HOL": 4})
        self._stopped(self._payslip(employee), "calculation", "HOL")

    def test_ot_last_piece(self):
        employee, _contract = self._hire(lines=self._sal_change())
        self._input(employee, ot_hours_json={"WD": 10}, segments=self._halves())
        expected = (Decimal(5000000) / Decimal(208) * Decimal("1.5") * Decimal(10)).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
        self.assertEqual(self._totals(self._payslip(employee), "OT_WD"), [int(expected)])

    def test_component_without_rule(self):
        extra = self._component(
            "EXTRA", amount_source="entered", legal_nature="bonus", proration=False
        )
        employee, _contract = self._hire()
        self._input(employee, lines=[(extra, {"amount": 100000})])
        self._stopped(self._payslip(employee), "calculation", "TEST_EXTRA")

    def test_snapshot_replaced(self):
        employee, _contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        inp = self._input(employee)
        payslip = self._payslip(employee)
        inp.paid_days = 13
        payslip.compute_sheet()
        self.assertEqual(payslip.l10n_vn_context["input"]["paid_days"], 13)
        self.assertEqual(self._totals(payslip, "SAL"), [2250000])

    def test_exact_lines(self):
        employee, _contract = self._hire(
            lines=[(self.base, {}), (self.prod, {"scale_key": "Entry"})]
        )
        self._input(
            employee,
            ot_hours_json={"WD": 20},
            attainment=1,
            attainment_source="supervisor",
            lines=[(self.eff, {"amount": 300000})],
        )
        payslip = self._payslip(employee)
        lines = payslip.line_ids.filtered(lambda line: line.amount_select == "l10n_vn_component")
        for line in lines:
            self.assertEqual((line.quantity, line.rate), (1, 100), line.code)
            self.assertEqual(line.total, line.amount, line.code)
            self.assertEqual(line.total, round(line.total), line.code)
        earnings = lines.filtered(lambda line: line.l10n_vn_component_id.kind == "earning")
        self.assertEqual(self._totals(payslip, "GROSS"), [sum(earnings.mapped("total"))])

    def test_split_names(self):
        employee, _contract = self._hire(
            date_start=D(2026, 10, 1),
            l10n_vn_probation_form="clause",
            trial_date_end=D(2026, 10, 7),
            lines=[(self.sal, {"amount": 4500000})],
        )
        self._input(
            employee,
            segments=[
                {"date_from": D(2026, 10, 1), "date_to": D(2026, 10, 7), "paid_days": 6,
                 "days_worked": 6},
                {"date_from": D(2026, 10, 8), "date_to": OCT_TO, "paid_days": 20,
                 "days_worked": 20},
            ],
        )
        sal = self._payslip(employee).line_ids.filtered(lambda l: l.code == "TEST_SAL")
        sal = sal.sorted("id")
        self.assertEqual(sal.mapped("name"), ["SAL (01/10–07/10, probation)", "SAL (08/10–31/10)"])
        self.assertEqual(sal.mapped("l10n_vn_days"), [6, 20])
        self.assertEqual(sal[0].l10n_vn_date_from, D(2026, 10, 1))
        self.assertEqual(sal[1].l10n_vn_date_to, OCT_TO)

    def test_other_rule_rounded(self):
        rule = self.env["hr.salary.rule"].create(
            {
                "name": "TEST_PY",
                "code": "TEST_PY",
                "sequence": 1000,
                "company_id": self.company.id,
                "category_id": self.cat_total.id,
                "amount_select": "code",
                "amount_python_compute": 'result = payroll.vn["gross"] + 0.5',
            }
        )
        self.structure.rule_ids = [Command.link(rule.id)]
        employee, _contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        self._input(employee)
        line = self._payslip(employee).line_ids.filtered(lambda l: l.code == "TEST_PY")
        self.assertEqual((line.quantity, line.rate, line.total), (1, 100, 4500001))
