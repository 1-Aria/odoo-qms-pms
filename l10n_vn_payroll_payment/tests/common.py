# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

import pytz

from odoo import Command

from odoo.addons.l10n_vn_payroll.tests.common import D
from odoo.addons.l10n_vn_payroll.tests.run_common import RunCase

TZ = "Asia/Ho_Chi_Minh"


class AdvanceMixin:
    """Advances made as the fixtures' superuser; mixed into a payroll test case."""

    def _advance(self, employee, amount, date=D(2026, 10, 16), **values):
        return self.env["l10n_vn.payroll.advance"].create(
            {
                "employee_id": employee.id,
                "company_id": self.company.id,
                "date": date,
                "amount": amount,
                "reason": "Test advance",
                **values,
            }
        )

    def _paid_advance(self, employee, amount, paid_date=D(2026, 10, 15), **values):
        return self._advance(
            employee, amount, date=paid_date, state="paid", paid_date=paid_date, **values
        )


class AdvanceCase(AdvanceMixin, RunCase):
    """Runs of October with advances; holds no test methods.

    Alice and Bao earn 4,500,000, are workers and attended every scheduled day from
    1 to 15 October, 13 days: for an advance on the 16th the limit is
    0.5 x 4,500,000 x 13 / 26 = 1,125,000.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._parameter("vn.policy.advance_max_share", [(D(2026, 1, 1), "0.5")])
        cls._parameter_text_cls("vn.policy.advance_pay_groups", "worker")
        # the grace period and the OT minimum are Odoo's tolerances, as in the engine
        cls.company.write({"overtime_employee_threshold": 5, "overtime_company_threshold": 48})
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Advance Test 6x8",
                "company_id": cls.company.id,
                "tz": TZ,
                "hours_per_day": 8,
                "attendance_ids": [Command.clear()]
                + [
                    Command.create(
                        {
                            "name": f"{day} {period}",
                            "dayofweek": str(day),
                            "hour_from": hour_from,
                            "hour_to": hour_to,
                            "day_period": period,
                        }
                    )
                    for day in range(6)
                    for period, hour_from, hour_to in (
                        ("morning", 7, 11),
                        ("lunch", 11, 12),
                        ("afternoon", 12, 16),
                    )
                ],
            }
        )

    @classmethod
    def _parameter_text_cls(cls, code, value):
        return cls.env["base.time.parameter"].create(
            {
                "name": code,
                "code": code,
                "type": "string",
                "company_id": cls.company.id,
                "version_ids": [Command.create({"date_from": D(2026, 1, 1), "value": value})],
            }
        )

    def setUp(self):
        super().setUp()
        # the pay group is the contract's (engine step 12)
        (self.alice_contract | self.bao_contract).l10n_vn_pay_group = "worker"
        for employee in (self.alice, self.bao):
            employee.write({"tz": TZ, "resource_calendar_id": self.calendar.id})
            self._attend_until(employee, D(2026, 10, 15))

    @staticmethod
    def _utc(day, hour):
        local = pytz.timezone(TZ).localize(datetime.datetime.combine(day, datetime.time(hour)))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _attend_until(self, employee, last):
        """07:00-16:00 on every day but Sunday from 1 October to last."""
        day = D(2026, 10, 1)
        vals = []
        while day <= last:
            if day.weekday() != 6:
                vals.append(
                    {
                        "employee_id": employee.id,
                        "check_in": self._utc(day, 7),
                        "check_out": self._utc(day, 16),
                    }
                )
            day += datetime.timedelta(days=1)
        self.env["hr.attendance"].create(vals)

    def _advances(self, user):
        return self._as(user)["l10n_vn.payroll.advance"]

    def _pay(self, payment, method, paid_date=D(2026, 10, 16), user=None, lines=None):
        """Marks a payment list's lines of one method as paid through the wizard (step 2)."""
        env = self._as(user or self.officer)
        action = getattr(
            env["l10n_vn.payroll.payment"].browse(payment.id), f"action_open_pay_{method}"
        )()
        wizard = env["l10n_vn.payroll.payment.pay"].with_context(action["context"]).create(
            {"paid_date": paid_date}
        )
        if lines is not None:
            wizard.line_ids = [Command.set(lines.ids)]
        wizard.action_confirm()
        return wizard
