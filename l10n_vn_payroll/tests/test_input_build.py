# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import D
from .input_common import HOLIDAY, InputCase


@tagged("post_install", "-at_install")
class TestInputBuild(InputCase):
    def test_full_month(self):
        self._attend_month()
        inp = self._build()
        self.assertEqual(inp.scheduled_days, 27)
        self.assertAlmostEqual(inp.days_worked, 26)
        self.assertAlmostEqual(inp.company_leave_days, 1)
        self.assertAlmostEqual(inp.paid_days, 27)
        self.assertAlmostEqual(inp.unpaid_days, 0)
        self.assertAlmostEqual(inp.si_absence_days, 0)
        self.assertEqual(inp.ot_hours, 0)

    def test_early_arrival_and_short_overtime(self):
        day = D(2026, 10, 5)
        self._attend_month(skip=(day,))
        attendance = self._attend(day, "06:30", "16:30")
        inp = self._build()
        # each end within Odoo's 48-minute tolerance: no OT (divergence 38)
        self.assertEqual(inp.ot_hours, 0)
        self.assertAlmostEqual(inp.days_worked, 26)
        attendance.write(
            {"check_in": self._utc(day, "07:00"), "check_out": self._utc(day, "17:00")}
        )
        inp = self._build()
        self.assertEqual(inp.ot_hours_json, {"WD": 1.0})
        self.assertAlmostEqual(inp.days_worked, 26)

    def test_overtime_categories(self):
        workday = D(2026, 10, 6)
        self._attend_month(skip=(workday,))
        self._attend(workday, "07:00", "18:00")
        self._attend(D(2026, 10, 11), "07:00", "11:00")
        self._attend(HOLIDAY, "07:00", "10:00")
        inp = self._build()
        self.assertEqual(inp.ot_hours_json, {"WD": 2.0, "RD": 4.0, "HOL": 3.0})

    def test_absence_and_unpaid_leave(self):
        absent = (D(2026, 10, 7), D(2026, 10, 8))
        unpaid_day = D(2026, 10, 9)
        self._attend_month(skip=absent + (unpaid_day,))
        self._leave(self._leave_type("Payroll Test Unpaid", unpaid=True), unpaid_day, unpaid_day)
        inp = self._build()
        self.assertEqual(inp.unexcused_absences, 2)
        self.assertAlmostEqual(inp.unpaid_days, 3)
        self.assertAlmostEqual(inp.unpaid_leave_days, 1)
        self.assertAlmostEqual(inp.paid_days, 24)

    def test_si_paid_leave(self):
        workdays = [d for d in self._october_workdays()]
        sick = workdays[:15]
        self._attend_month(skip=tuple(sick))
        self._leave(self._leave_type("Payroll Test Sick", l10n_vn_si_paid=True), sick[0], sick[-1])
        inp = self._build()
        self.assertAlmostEqual(inp.si_leave_days, 15)
        self.assertAlmostEqual(inp.days_worked, 11)
        self.assertAlmostEqual(inp.paid_days, 12)
        self.assertAlmostEqual(inp.si_absence_days, 15)

    def test_paid_leave(self):
        days = (D(2026, 10, 12), D(2026, 10, 13))
        self._attend_month(skip=days)
        self._leave(self._leave_type("Payroll Test Annual"), days[0], days[1])
        inp = self._build()
        self.assertAlmostEqual(inp.company_leave_days, 3)
        self.assertAlmostEqual(inp.paid_days, 27)

    def _child(self, born):
        self.env["hr.employee.relative"].create(
            {
                "employee_id": self.employee.id,
                "relation_id": self.env.ref("hr_employee_relative.relation_child").id,
                "name": "Payroll Test Child",
                "date_of_birth": born,
            }
        )

    def test_nursing_break(self):
        self.employee.l10n_vn_nursing_break = True
        self._child(D(2026, 3, 10))
        self._attend_month(end="15:00")
        inp = self._build()
        self.assertAlmostEqual(inp.paid_break_hours, 26)
        self.assertAlmostEqual(inp.paid_days, 27)

    def test_nursing_break_child_over_one(self):
        self.employee.l10n_vn_nursing_break = True
        self._child(D(2025, 9, 1))
        self._attend_month(end="15:00")
        inp = self._build()
        self.assertEqual(inp.paid_break_hours, 0)
        self.assertAlmostEqual(inp.paid_days, 23.75)

    def test_menstruation_days(self):
        short = (D(2026, 10, 1), D(2026, 10, 2), D(2026, 10, 3))
        self._attend_month(skip=short)
        for day in short:
            self._attend(day, "07:00", "15:30")
        self.period.action_build()
        inp = self.period.input_ids.filtered(lambda i: i.employee_id == self.employee)
        inp.menstruation_days = 3
        inp._l10n_vn_build()
        self.assertAlmostEqual(inp.paid_break_hours, 1.5)
        inp.menstruation_days = 5
        inp._l10n_vn_build()
        self.assertAlmostEqual(inp.paid_break_hours, 1.5)

    def test_segments(self):
        self.contract.date_end = D(2026, 10, 14)
        self.env["hr.contract"].create(
            {
                "name": "Payroll Test Contract 2",
                "employee_id": self.employee.id,
                "company_id": self.company.id,
                "date_start": D(2026, 10, 15),
                "wage": 1,
                "resource_calendar_id": self.cal.id,
                "state": "open",
            }
        )
        self._attend_month()
        inp = self._build()
        self.assertEqual(len(inp.segment_ids), 2)
        self.assertEqual(inp.segment_ids[0].date_to, D(2026, 10, 14))
        self.assertAlmostEqual(sum(inp.segment_ids.mapped("paid_days")), inp.paid_days)

    def test_locked_kept(self):
        self._attend_month()
        inp = self._build()
        inp.write({"figures_locked": True, "paid_days": 20})
        self.period.action_build()
        self.assertEqual(inp.paid_days, 20)

    def test_calendar_hours_per_day_ignored(self):
        self._attend_month()
        self.cal.hours_per_day = 16
        inp = self._build()
        self.assertAlmostEqual(inp.days_worked, 26)

    def test_ot_hours_ytd(self):
        september = self.env["l10n_vn.payroll.period"].create(
            {"date_from": D(2026, 9, 1), "company_id": self.company.id}
        )
        self.env["l10n_vn.payroll.input"].create(
            {
                "period_id": september.id,
                "employee_id": self.employee.id,
                "ot_hours_json": {"WD": 12.0},
            }
        )
        self._attend_month()
        inp = self._build()
        self.assertEqual(inp.ot_hours_ytd, 12)

    def test_zero_figures_stored(self):
        inp = self._build()
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT days_worked, unpaid_leave_days, paid_break_hours, unexcused_absences "
            "FROM l10n_vn_payroll_input WHERE id = %s",
            (inp.id,),
        )
        self.assertEqual(self.env.cr.fetchone(), (0.0, 0.0, 0.0, 26))
