# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

import pytz
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

from .pay_context import HOURS_PER_DAY

LEVELS = [("error", "Error"), ("warning", "Warning"), ("note", "Note"), ("off", "Off")]
LEVEL_CODES = {code for code, _label in LEVELS}
LEVEL_ORDER = {"error": 1, "warning": 2, "note": 3}
LAWFUL_DEDUCTIONS = ("statutory", "union", "damage")


class L10nVnPayrollCheck(models.Model):
    _name = "l10n_vn.payroll.check"
    _description = "Payroll Check"
    _order = "sequence, code"

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    kind = fields.Selection(
        [("integrity", "Integrity"), ("legal", "Legal"), ("policy", "Policy")], required=True
    )
    default_level = fields.Selection(LEVELS, required=True)
    per_component = fields.Boolean(string="Level per component")
    description = fields.Text(translate=True)

    _sql_constraints = [("code_unique", "unique(code)", "A check code is unique.")]

    # ------------------------------------------------------------------ levels (D60)
    def _l10n_vn_level(self, payslip, component):
        self.ensure_one()
        if self.kind == "integrity":
            return "error"
        codes = []
        if self.per_component and component:
            codes.append(f"vn.check.{self.code}.{component.code}")
        codes.append(f"vn.check.{self.code}")
        Parameter = self.env["base.time.parameter"].sudo()
        for code in codes:
            try:
                value = Parameter._strict_get(code, payslip.date_to, company=payslip.company_id)
            except UserError:
                continue  # not set
            value = str(value or "").strip().lower()
            if value in LEVEL_CODES:
                return value
        return self.default_level

    # ------------------------------------------------------------------ helpers
    def _param(self, payslip, code):
        return self.env["base.time.parameter"].sudo()._strict_get(
            code, payslip.date_to, company=payslip.company_id
        )

    def _components(self, ids):
        return self.env["l10n_vn.payroll.component"].sudo().browse(ids).exists()

    def _line_components(self, context, kind=None):
        ids = []
        for line in context.get("lines", []):
            if (kind is None or line["kind"] == kind) and line["component_id"] not in ids:
                ids.append(line["component_id"])
        return self._components(ids)

    def _last_pay_lines(self, context):
        pieces = context.get("pieces", [])
        last = len(pieces) - 1
        return [p for p in context.get("pay_lines", []) if p["piece"] == last]

    def _l10n_vn_earlier(self, payslip, months):
        """Snapshots of the employee's done payslips for the months before (D67)."""
        Payslip = self.env["hr.payslip"].sudo()
        found = {}
        for back in range(1, months + 1):
            month = payslip.date_from - relativedelta(months=back)
            earlier = Payslip.search(
                [
                    ("employee_id", "=", payslip.employee_id.id),
                    ("company_id", "=", payslip.company_id.id),
                    ("date_from", "=", month),
                    ("state", "=", "done"),
                ],
                order="id desc",
                limit=1,
            )
            if earlier.l10n_vn_context:
                found[month] = earlier.l10n_vn_context
        return found

    @staticmethod
    def _scheduled_dates(contract, start, end):
        calendar = contract.resource_calendar_id
        employee = contract.employee_id
        tz = pytz.timezone(calendar.tz or employee.tz or "UTC")
        begin = tz.localize(datetime.datetime.combine(start, datetime.time.min))
        after = tz.localize(
            datetime.datetime.combine(end + datetime.timedelta(days=1), datetime.time.min)
        )
        resource = employee.resource_id
        intervals = calendar._attendance_intervals_batch(begin, after, resources=resource)
        return len({b.astimezone(tz).date() for b, e, _a in intervals[resource.id] if e > b})

    # ------------------------------------------------------------------ finders (D66)
    def _l10n_vn_find_period_open(self, payslip, context):
        period = self.env["l10n_vn.payroll.period"].sudo().search(
            [("company_id", "=", payslip.company_id.id), ("date_from", "=", payslip.date_from)],
            limit=1,
        )
        findings = []
        if period and not period.attendance_closed:
            findings.append(
                (False, self.env._("Attendance of %(period)s is not closed.", period=period.name))
            )
        if period and period.ie_required and not period.ie_closed:
            findings.append(
                (False, self.env._("IE figures of %(period)s are not closed.", period=period.name))
            )
        incomplete = payslip.l10n_vn_input_id.sudo().incomplete_days
        if incomplete:
            findings.append(
                (
                    False,
                    self.env._(
                        "%(days)s days with an attendance without check-out.", days=incomplete
                    ),
                )
            )
        return findings

    def _l10n_vn_find_negative_net(self, payslip, context):
        net = context.get("net", 0)
        if net < 0:
            return [(False, self.env._("Net pay is negative: %(net)s.", net=f"{net:,}"))]
        return []

    def _l10n_vn_find_missing_ids(self, payslip, context):
        if context.get("to_pay", 0) <= 0:
            return []
        employee = payslip.employee_id.sudo()
        missing = []
        if not employee.bank_account_id:
            missing.append(self.env._("bank account"))
        if not employee.l10n_vn_personal_id:
            missing.append(self.env._("personal ID number"))
        if not employee.ssnid:
            missing.append(self.env._("SI number"))
        if not missing:
            return []
        return [
            (
                False,
                self.env._(
                    "%(employee)s has no %(missing)s.",
                    employee=employee.name,
                    missing=", ".join(missing),
                ),
            )
        ]

    def _l10n_vn_find_unapproved_entry(self, payslip, context):
        findings = []
        lines = self.env["l10n_vn.payroll.input.line"].sudo().browse(
            context.get("unapproved", [])
        ).exists()
        for line in lines:
            findings.append(
                (
                    line.component_id,
                    self.env._(
                        "%(entry)s of %(amount)s has no approver and is not paid.",
                        entry=line.description or line.component_id.name,
                        amount=f"{line.amount:,.0f}",
                    ),
                )
            )
        return findings

    def _l10n_vn_find_min_wage(self, payslip, context):
        kind = payslip.contract_id.sudo().l10n_vn_participant_type_id
        region = payslip.employee_id.sudo().l10n_vn_region
        if kind.floor != "min_wage" or not region:
            return []
        total = 0
        for pay_line in self._last_pay_lines(context):
            component = self._components(pay_line["component_id"])
            if component.in_si_base and component.proration != "per_day":
                total += pay_line["amount"]
        minimum = self._param(payslip, "vn.min_wage.month")[region]
        if 0 < total < minimum:
            return [
                (
                    False,
                    self.env._(
                        "Salary in the SI base %(total)s is below the region %(region)s "
                        "minimum wage %(minimum)s.",
                        total=f"{total:,.0f}",
                        region=region,
                        minimum=f"{minimum:,.0f}",
                    ),
                )
            ]
        return []

    def _l10n_vn_find_daily_min(self, payslip, context):
        region = payslip.employee_id.sudo().l10n_vn_region
        if not region:
            return []
        findings = []
        for pay_line in self._last_pay_lines(context):
            component = self._components(pay_line["component_id"])
            if component.proration != "per_day":
                continue
            minimum = self._param(payslip, "vn.min_wage.hour")[region] * HOURS_PER_DAY
            if pay_line["amount"] < minimum:
                findings.append(
                    (
                        component,
                        self.env._(
                            "Daily rate %(rate)s is below the hourly minimum × %(hours)s = "
                            "%(minimum)s.",
                            rate=f"{pay_line['amount']:,.0f}",
                            hours=HOURS_PER_DAY,
                            minimum=f"{minimum:,.0f}",
                        ),
                    )
                )
        return findings

    def _l10n_vn_find_nature(self, payslip, context):
        findings = []
        for component in self._line_components(context, "earning"):
            nature = component.legal_nature
            if nature == "welfare" and component.in_ot_base:
                findings.append((component, self.env._("A welfare item counts in the OT base.")))
            elif nature == "fixed_allowance" and not component.in_si_base:
                findings.append(
                    (component, self.env._("A fixed allowance is outside the SI base."))
                )
            elif nature == "variable_salary" and not component.variable:
                findings.append(
                    (component, self.env._("A variable salary does not vary with attainment."))
                )
        return findings

    def _l10n_vn_find_probation_length(self, payslip, context):
        Contract = self.env["hr.contract"].sudo()
        contracts = Contract.browse(
            sorted({p["contract_id"] for p in context.get("pieces", []) if p["probation"]})
        )
        if not contracts:
            return []
        findings = []
        limits = None
        for contract in contracts.filtered("l10n_vn_probation_job"):
            if contract.l10n_vn_probation_form == "clause":
                end = contract.trial_date_end
            else:
                end = contract.date_end
            if not end:
                continue
            limits = limits or self._param(payslip, "vn.probation.max_days")
            job = contract.l10n_vn_probation_job
            if job == "other":
                length = self._scheduled_dates(contract, contract.date_start, end)
            else:
                length = (end - contract.date_start).days + 1
            if length > limits[job]:
                findings.append(
                    (
                        False,
                        self.env._(
                            "Probation of %(length)s days on contract %(contract)s is longer "
                            "than the %(limit)s allowed for this job.",
                            length=length,
                            contract=contract.name,
                            limit=limits[job],
                        ),
                    )
                )
        rate = self._param(payslip, "vn.policy.probation_rate")
        minimum = self._param(payslip, "vn.probation.min_rate")
        if rate < minimum:
            findings.append(
                (
                    False,
                    self.env._(
                        "The probation rate %(rate)s is below the legal minimum %(minimum)s.",
                        rate=rate,
                        minimum=minimum,
                    ),
                )
            )
        return findings

    def _l10n_vn_find_deduction_kind(self, payslip, context):
        return [
            (
                component,
                self.env._("A deduction of a kind the law does not allow (Labor Code Art. 102)."),
            )
            for component in self._line_components(context, "deduction")
            if component.legal_nature not in LAWFUL_DEDUCTIONS
        ]

    def _l10n_vn_find_ot_limit(self, payslip, context):
        inp = payslip.l10n_vn_input_id.sudo()
        hours = inp.ot_hours
        if not hours:
            return []
        findings = []
        if inp.ot_over_daily_hours > 0:
            findings.append(
                (
                    False,
                    self.env._(
                        "%(hours)s OT hours above the daily limit.",
                        hours=f"{inp.ot_over_daily_hours:g}",
                    ),
                )
            )
        month_limit = self._param(payslip, "vn.ot.limit.month")
        year_limit = self._param(payslip, "vn.ot.limit.year")
        if hours > month_limit:
            findings.append(
                (
                    False,
                    self.env._(
                        "%(hours)s OT hours in the month, above the limit of %(limit)s.",
                        hours=f"{hours:g}",
                        limit=month_limit,
                    ),
                )
            )
        if inp.ot_hours_ytd + hours > year_limit:
            findings.append(
                (
                    False,
                    self.env._(
                        "%(hours)s OT hours in the year, above the limit of %(limit)s.",
                        hours=f"{inp.ot_hours_ytd + hours:g}",
                        limit=year_limit,
                    ),
                )
            )
        return findings

    @staticmethod
    def _at_full(line):
        return (line["attainment"] is not None and line["attainment"] >= 1) or line.get(
            "condition"
        ) is True

    def _l10n_vn_find_variable_constant(self, payslip, context):
        candidates = []
        for line in context.get("lines", []):
            if self._at_full(line) and line["component_id"] not in candidates:
                candidates.append(line["component_id"])
        if not candidates:
            return []
        months = int(self._param(payslip, "vn.policy.constant_months"))
        earlier = self._l10n_vn_earlier(payslip, months - 1)
        if len(earlier) < months - 1:
            return []
        findings = []
        for component in self._components(candidates):
            if all(
                any(
                    line["component_id"] == component.id and self._at_full(line)
                    for line in snapshot.get("lines", [])
                )
                for snapshot in earlier.values()
            ):
                findings.append(
                    (
                        component,
                        self.env._(
                            "%(component)s has been paid in full for %(months)s months running.",
                            component=component.name,
                            months=months,
                        ),
                    )
                )
        return findings

    def _l10n_vn_find_net_change(self, payslip, context):
        earlier = self._l10n_vn_earlier(payslip, 1)
        if not earlier:
            return []
        previous = next(iter(earlier.values())).get("net") or 0
        if previous <= 0:
            return []
        net = context.get("net", 0)
        share = self._param(payslip, "vn.policy.net_change")
        change = abs(net - previous) / previous
        if change > share:
            return [
                (
                    False,
                    self.env._(
                        "Net pay %(net)s changed by %(change)s%% from last month's %(previous)s.",
                        net=f"{net:,}",
                        change=round(change * 100),
                        previous=f"{previous:,}",
                    ),
                )
            ]
        return []

    def _l10n_vn_find_ie_scope(self, payslip, context):
        inp = payslip.l10n_vn_input_id.sudo()
        if inp.ie_units and payslip.employee_id.sudo().l10n_vn_pay_group != "worker":
            return [
                (
                    False,
                    self.env._(
                        "%(units)s IE units for an employee outside IE scope.",
                        units=f"{inp.ie_units:g}",
                    ),
                )
            ]
        return []

    def _l10n_vn_find_long_days(self, payslip, context):
        days = payslip.l10n_vn_input_id.sudo().long_days
        if not days:
            return []
        limit = self._param(payslip, "vn.ot.limit.day_total")
        return [
            (
                False,
                self.env._(
                    "%(days)s days with more than %(limit)s hours of work.",
                    days=days,
                    limit=f"{limit:g}",
                ),
            )
        ]

    def _l10n_vn_find_level_review(self, payslip, context):
        findings = []
        for pay_line in self._last_pay_lines(context):
            review = pay_line.get("review_date")
            if review and fields.Date.to_date(review) <= payslip.date_to:
                findings.append(
                    (
                        self._components(pay_line["component_id"]),
                        self.env._("Level due for review on %(date)s.", date=review),
                    )
                )
        return findings

    def _l10n_vn_find_dependent_document(self, payslip, context):
        month_start = payslip.date_from.replace(day=1)
        relatives = payslip.employee_id.sudo().relative_ids.filtered(
            lambda r: r._l10n_vn_counts_in(month_start) and not r.l10n_vn_document
        )
        return [
            (
                False,
                self.env._(
                    "Dependent %(name)s has no registration document.", name=relative.name
                ),
            )
            for relative in relatives
        ]

    def _l10n_vn_find_advance_carried(self, payslip, context):
        advances = sum(a["amount"] for a in context.get("advances", []))
        settled = context.get("settled", 0)
        if advances > settled:
            return [
                (
                    False,
                    self.env._(
                        "Advances of %(advances)s exceed the %(settled)s settled; the rest "
                        "carries to next month.",
                        advances=f"{advances:,.0f}",
                        settled=f"{settled:,}",
                    ),
                )
            ]
        return []


class L10nVnPayrollCheckResult(models.Model):
    _name = "l10n_vn.payroll.check.result"
    _description = "Payroll Check Result"
    _order = "payslip_id, level_order, check_id"

    payslip_id = fields.Many2one("hr.payslip", required=True, ondelete="cascade", index=True)
    run_id = fields.Many2one(related="payslip_id.payslip_run_id", store=True)
    employee_id = fields.Many2one(related="payslip_id.employee_id", store=True)
    company_id = fields.Many2one(related="payslip_id.company_id", store=True)
    check_id = fields.Many2one("l10n_vn.payroll.check", required=True, ondelete="restrict")
    kind = fields.Selection(related="check_id.kind")
    component_id = fields.Many2one("l10n_vn.payroll.component", ondelete="set null")
    level = fields.Selection(LEVELS[:3], required=True)
    level_order = fields.Integer(compute="_compute_level_order", store=True)
    message = fields.Char(required=True)
    note = fields.Text(string="Reviewer's note")
    noted_by = fields.Many2one("res.users", readonly=True)
    noted_at = fields.Datetime(readonly=True)

    @api.depends("level")
    def _compute_level_order(self):
        for result in self:
            result.level_order = LEVEL_ORDER.get(result.level, 9)

    @api.model_create_multi
    def create(self, vals_list):
        self.env["hr.payslip"].browse(
            [v["payslip_id"] for v in vals_list if v.get("payslip_id")]
        )._l10n_vn_raise_if_locked()
        return super().create(vals_list)

    def write(self, vals):
        self.payslip_id._l10n_vn_raise_if_locked()
        if "note" in vals:
            vals = dict(vals, noted_by=self.env.uid, noted_at=fields.Datetime.now())
        return super().write(vals)

    def unlink(self):
        self.payslip_id._l10n_vn_raise_if_locked()
        return super().unlink()
