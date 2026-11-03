# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import itertools
import json

from odoo import Command, fields
from odoo.tools.misc import file_path

from .common import D, PayrollCase

OCT_FROM = D(2026, 10, 1)
OCT_TO = D(2026, 10, 31)
CASES_FILE = "l10n_vn_payroll/tests/data/acceptance_cases.json"


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
            ("vn.policy.constant_months", "6"),
            ("vn.policy.net_change", "0.30"),
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
        # step 5
        cls.kpi = C("KPI", **entered)
        cls.annual = C("ANNUAL", **entered)
        cls.leave = C("LEAVE", amount_source="entered", legal_nature="leave_pay",
                      pit_treatment="exempt", proration=False)
        cls.phone = C("PHONE", legal_nature="welfare", pit_treatment="exempt", proration="none")
        cls.meal = C("MEAL", legal_nature="welfare", pit_treatment="exempt_cap",
                     pit_cap_parameter="vn.pit.meal_cap", proration="none")

        def engine(code, kind, nature, section):
            return C(code, kind=kind, legal_nature=nature, amount_source="engine",
                     engine_code=code, section=section, pit_treatment=False, proration=False)

        cls.engine = {}
        for code, kind, nature, section in (
            ("EE_SI", "deduction", "statutory", "deduction"),
            ("EE_HI", "deduction", "statutory", "deduction"),
            ("EE_UI", "deduction", "statutory", "deduction"),
            ("DUES", "deduction", "union", "deduction"),
            ("PIT", "deduction", "statutory", "deduction"),
            ("DAMAGE", "deduction", "damage", "deduction"),
            ("NET", "total", "total", "total"),
            ("ADVANCE", "info", "advance", "total"),
            ("TO_PAY", "total", "total", "total"),
            ("ER_PENSION", "employer", "statutory", "employer"),
            ("ER_SICKNESS", "employer", "statutory", "employer"),
            ("ER_ACCIDENT", "employer", "statutory", "employer"),
            ("ER_HI", "employer", "statutory", "employer"),
            ("ER_UI", "employer", "statutory", "employer"),
            ("UNION_FEE", "employer", "statutory", "employer"),
        ):
            cls.engine[code] = engine(code, kind, nature, section)
        Category = cls.env["hr.salary.rule.category"]
        cls.cat_earn = Category.create({"name": "Test earnings", "code": "TEST_EARN"})
        cls.cat_total = Category.create({"name": "Test totals", "code": "TEST_TOTAL"})
        cls.cat_ded = Category.create({"name": "Test deductions", "code": "TEST_DED"})
        cls.cat_er = Category.create({"name": "Test employer", "code": "TEST_ER"})
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
            cls.ot_hol, cls.supp, cls.inc, cls.eff, cls.one, cls.att, cls.travel, cls.kpi,
            cls.annual, cls.leave, cls.phone, cls.meal, cls.gross, *cls.engine.values(),
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
                "category_id": {
                    "total": cls.cat_total,
                    "info": cls.cat_total,
                    "deduction": cls.cat_ded,
                    "employer": cls.cat_er,
                }.get(component.kind, cls.cat_earn).id,
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
                    "l10n_vn_region": "IV",
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
            "month_scheduled_days": 26,
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
                lambda line: line.l10n_vn_component_id.kind == "earning"
            ).mapped("code")
        )
        self.assertEqual(shown, {self._code(c) for c in expected}, case)
        self.assertEqual(self._totals(payslip, "GROSS"), [data["gross"]], f"{case}: gross")

    # ------------------------------------------------------------------ step 6
    def _results(self, payslip, code):
        return payslip.l10n_vn_check_result_ids.filtered(lambda r: r.check_id.code == code)

    def _stopped(self, payslip, code, text):
        """The payslip was stopped by an integrity check (D62)."""
        results = self._results(payslip, code)
        self.assertEqual(len(results), 1, f"one {code} result")
        self.assertEqual(results.level, "error")
        self.assertIn(text, results.message)
        self.assertFalse(payslip.line_ids, "a stopped payslip keeps no line")
        self.assertFalse(payslip.l10n_vn_context, "a stopped payslip keeps no snapshot")

    def _identify(self, employee):
        bank = self.env["res.partner.bank"].create(
            {"acc_number": f"TEST-{employee.id}", "partner_id": employee.work_contact_id.id}
        )
        employee.write(
            {
                "bank_account_id": bank.id,
                "l10n_vn_personal_id": f"0790{employee.id:08d}",
                "ssnid": f"79{employee.id:08d}",
            }
        )

    def _parameter_text(self, code, value):
        return self.env["base.time.parameter"].create(
            {
                "name": code,
                "code": code,
                "type": "string",
                "company_id": self.company.id,
                "version_ids": [Command.create({"date_from": D(2026, 1, 1), "value": value})],
            }
        )

    # ------------------------------------------------------------------ step 5
    def _dependents(self, employee, count, date_from=D(2026, 1, 1)):
        child = self.env.ref("hr_employee_relative.relation_child")
        for n in range(count):
            self.env["hr.employee.relative"].create(
                {
                    "employee_id": employee.id,
                    "relation_id": child.id,
                    "name": f"Payslip Test Child {n + 1}",
                    "l10n_vn_pit_dependent": True,
                    "l10n_vn_from": date_from,
                }
            )

    def _damage(self, employee, amount, date=D(2026, 10, 1)):
        return self.env["l10n_vn.payroll.damage"].create(
            {
                "employee_id": employee.id,
                "company_id": self.company.id,
                "decision_ref": f"TEST-{employee.id}-{date}",
                "decision_date": date,
                "reason": "Test",
                "amount": amount,
            }
        )

    def _expect_pay(self, payslip, case, advances=True):
        """Insurance, PIT, damage, net and employer funds against the case."""
        data = self._cases()[case]

        def deducted(amount):
            return [-amount] if amount else []

        for code, key in (("EE_SI", "ee_si"), ("EE_HI", "ee_hi"), ("EE_UI", "ee_ui"),
                          ("DUES", "dues"), ("DAMAGE", "damage")):
            self.assertEqual(self._totals(payslip, code), deducted(data[key]), f"{case}: {code}")
        self.assertEqual(self._totals(payslip, "PIT"), [-data["pit"]], f"{case}: PIT")
        self.assertEqual(self._totals(payslip, "NET"), [data["net"]], f"{case}: NET")
        for code, key in (("ER_PENSION", "pension"), ("ER_SICKNESS", "sickness"),
                          ("ER_ACCIDENT", "accident"), ("ER_HI", "hi"), ("ER_UI", "ui"),
                          ("UNION_FEE", "union_fee")):
            amount = data["employer"][key]
            self.assertEqual(self._totals(payslip, code), [amount] if amount else [],
                             f"{case}: {code}")
        context = payslip.l10n_vn_context
        self.assertEqual(context["contributions"]["base"], data["si_base"], f"{case}: SI base")
        self.assertEqual(context["pit"]["method"], data["pit_method"], f"{case}: PIT method")
        if data["pit_method"] == "progressive":
            self.assertEqual(context["pit"]["exempt"], data["exempt"], f"{case}: exempt")
            self.assertEqual(context["pit"]["taxable"], data["taxable"], f"{case}: taxable")
        if advances:
            self.assertEqual(self._totals(payslip, "TO_PAY"), [data["to_pay"]], f"{case}: to pay")
