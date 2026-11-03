# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import itertools
import json

from odoo import Command, fields
from odoo.tools.misc import file_path

from .common import D, PayrollCase

OCT_FROM = D(2026, 10, 1)
OCT_TO = D(2026, 10, 31)
CASES_FILE = "l10n_vn_payroll/tests/data/acceptance_earnings.json"


class PayslipCase(PayrollCase):
    """October 2026 payslips on a Vietnamese structure; holds no test methods.

    Expected acceptance figures are never typed: they come from the JSON file that
    payroll_reference_calc.py writes.
    """

    _names = itertools.count(1)
    _cases_data = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company._l10n_vn_payroll_ensure_parameters()
        for code, value in (
            ("vn.policy.std_days", "26"),
            ("vn.policy.probation_rate", "0.85"),
            ("vn.policy.attainment_cap", "1"),
            ("vn.policy.unit_rate", "1500"),
            ("vn.policy.attendance_late_max", "2"),
            ("vn.policy.base_salary", "3700000"),
            ("vn.policy.ot_supplement", "3846"),
            ("vn.policy.ot_min_hours_day", "0.8"),
        ):
            cls._parameter(code, [(D(2026, 1, 1), value)])
        prod_scale = cls._scale(
            "PROD",
            "level",
            {
                D(2026, 1, 1): {
                    "Entry": 800000,
                    "S1": 1300000,
                    "S2": 1800000,
                    "S3": 2300000,
                    "S4": 2800000,
                }
            },
        )
        grade_scale = cls._scale(
            "GRADE", "grade_step", {D(2026, 1, 1): {"G2-2": 8000000, "G3-2": 10000000}}
        )
        C = cls._component
        variable = {"legal_nature": "variable_salary", "variable": True, "in_ot_base": True,
                    "probation_applies": True}
        ot = {"amount_source": "ot", "legal_nature": "overtime", "pit_treatment": "ot",
              "proration": False}
        entered = {"amount_source": "entered", "legal_nature": "bonus", "proration": False}
        # current scheme
        cls.base = C("BASE", amount_source="parameter", amount_parameter="vn.policy.base_salary",
                     in_si_base=True, in_ot_base=True, probation_applies=True, sets_wage=True)
        cls.prod = C("PROD", amount_source="scale", scale_id=prod_scale.id,
                     attainment_source="supervisor", **variable)
        cls.perf = C("PERF", amount_source="scale_remainder", scale_id=grade_scale.id,
                     attainment_source="manager", **variable)
        # reference configuration
        cls.sal = C("SAL", in_si_base=True, in_ot_base=True, probation_applies=True)
        cls.skill = C("SKILL", legal_nature="fixed_allowance", in_si_base=True, in_ot_base=True)
        cls.att = C("ATT", legal_nature="bonus", condition="attendance", proration="none")
        cls.travel = C("TRAVEL", legal_nature="welfare", proration="none")
        cls.daily = C("DAILY", in_si_base=True, in_ot_base=True, proration="per_day")
        cls.inc = C("INC", amount_source="ie_units", legal_nature="bonus", proration=False)
        # both
        cls.eff = C("EFF", **entered)
        cls.one = C("ONE", **entered)
        cls.ot_wd = C("OT_WD", ot_category="WD", **ot)
        cls.ot_rd = C("OT_RD", ot_category="RD", **ot)
        cls.ot_hol = C("OT_HOL", ot_category="HOL", **ot)
        cls.supp = C("SUPP", ot_category="all", amount_parameter="vn.policy.ot_supplement",
                     active=False, **ot)
        cls.gross = C("GROSS", kind="total", legal_nature="total", amount_source="engine",
                      engine_code="GROSS", section="total", pit_treatment=False, proration=False)
        Category = cls.env["hr.salary.rule.category"]
        cls.cat_earn = Category.create({"name": "Test earnings", "code": "TEST_EARN"})
        cls.cat_total = Category.create({"name": "Test totals", "code": "TEST_TOTAL"})
        cls.structure = cls.env["hr.payroll.structure"].create(
            {
                "name": "TEST VN",
                "code": "TEST_VN",
                "company_id": cls.company.id,
                "l10n_vn_payroll": True,
            }
        )
        components = (
            cls.base, cls.prod, cls.perf, cls.sal, cls.skill, cls.daily, cls.ot_wd, cls.ot_rd,
            cls.ot_hol, cls.supp, cls.inc, cls.eff, cls.one, cls.att, cls.travel, cls.gross,
        )
        for sequence, component in enumerate(components, start=1):
            cls._rule(component, sequence * 10)
        cls.contract.struct_id = cls.structure
        cls.period = cls.env["l10n_vn.payroll.period"].create(
            {"date_from": OCT_FROM, "company_id": cls.company.id}
        )

    @classmethod
    def _rule(cls, component, sequence=500):
        rule = cls.env["hr.salary.rule"].create(
            {
                "name": component.name,
                "code": component.code,
                "sequence": sequence,
                "company_id": cls.company.id,
                "category_id": (
                    cls.cat_total if component.kind == "total" else cls.cat_earn
                ).id,
                "amount_select": "l10n_vn_component",
                "condition_select": "l10n_vn_component",
                "l10n_vn_component_id": component.id,
            }
        )
        cls.structure.rule_ids = [Command.link(rule.id)]
        return rule

    # ------------------------------------------------------------------ helpers
    def _hire(self, lines=(), date_start=D(2026, 1, 1), date_end=None, state="open",
              employee=None, **values):
        if not employee:
            employee = self.env["hr.employee"].create(
                {
                    "name": f"Payslip Test Employee {next(self._names)}",
                    "company_id": self.company.id,
                }
            )
        contract = self.env["hr.contract"].create(
            {
                "name": f"{employee.name} {date_start}",
                "employee_id": employee.id,
                "company_id": self.company.id,
                "date_start": date_start,
                "date_end": date_end,
                "wage": 1,
                "resource_calendar_id": self.calendar.id,
                "struct_id": self.structure.id,
                "state": state,
                **values,
            }
        )
        for component, line_values in lines:
            self._line(component, contract=contract, **{"date_from": date_start, **line_values})
        return employee, contract

    def _input(self, employee, segments=(), lines=(), **figures):
        vals = {
            "period_id": self.period.id,
            "employee_id": employee.id,
            "figures_locked": True,
            "scheduled_days": 26,
            "paid_days": 26,
            "days_worked": 26,
        }
        vals.update(figures)
        vals["segment_ids"] = [Command.create(dict(segment)) for segment in segments]
        inp = self.env["l10n_vn.payroll.input"].create(vals)
        for component, line_values in lines:
            line_values = dict(line_values)
            approved = line_values.pop("approved", True)
            line = self.env["l10n_vn.payroll.input.line"].create(
                {"input_id": inp.id, "component_id": component.id, **line_values}
            )
            if approved:
                line.sudo().write(
                    {"approved_by": self.env.uid, "approved_at": fields.Datetime.now()}
                )
        return inp

    def _payslip(self, employee):
        """A payslip made as OCA's batch makes it, then calculated."""
        Payslip = self.env["hr.payslip"]
        vals = Payslip.get_payslip_vals(OCT_FROM, OCT_TO, employee.id)["value"]
        payslip = Payslip.create(
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
        payslip.compute_sheet()
        return payslip

    def _halves(self, first=None, second=None):
        """Segments for a month cut on 15 October."""
        return [
            {"date_from": D(2026, 10, 1), "date_to": D(2026, 10, 14), "paid_days": 12,
             "days_worked": 12, "ot_hours_json": first or {}},
            {"date_from": D(2026, 10, 15), "date_to": OCT_TO, "paid_days": 14,
             "days_worked": 14, "ot_hours_json": second or {}},
        ]

    def _sal_change(self):
        """SAL 4,500,000 until 14 October, 5,000,000 from the 15th."""
        return [
            (self.sal, {"amount": 4500000, "date_to": D(2026, 10, 14)}),
            (self.sal, {"amount": 5000000, "date_from": D(2026, 10, 15)}),
        ]

    @staticmethod
    def _code(code):
        return f"TEST_{code}"

    def _totals(self, payslip, code):
        lines = payslip.line_ids.filtered(lambda line: line.code == self._code(code))
        return lines.sorted("id").mapped("total")

    @classmethod
    def _cases(cls):
        if PayslipCase._cases_data is None:
            with open(file_path(CASES_FILE), encoding="utf-8") as handle:
                PayslipCase._cases_data = json.load(handle)
        return PayslipCase._cases_data

    def _expect(self, payslip, case, codes):
        data = self._cases()[case]
        rows = data["earnings"]
        self.assertEqual(len(rows), len(codes), f"{case}: one code per row")
        expected = {}
        for (label, amount), code in zip(rows, codes):
            if code is None:
                self.assertEqual(amount, 0, f"{case}: {label}")
                continue
            expected.setdefault(code, []).append(amount)
        for code, amounts in expected.items():
            self.assertEqual(self._totals(payslip, code), amounts, f"{case}: {code}")
        shown = set(
            payslip.line_ids.filtered(
                lambda line: line.amount_select == "l10n_vn_component"
            ).mapped("code")
        )
        self.assertEqual(shown - {self._code("GROSS")}, {self._code(c) for c in expected}, case)
        self.assertEqual(self._totals(payslip, "GROSS"), [data["gross"]], f"{case}: gross")
