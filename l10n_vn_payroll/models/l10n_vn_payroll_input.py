# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
from collections import defaultdict

import pytz

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .hr_payslip_run import LOCKED_STATES

DAY_FIGURES = (
    "scheduled_days",
    "month_scheduled_days",
    "days_worked",
    "company_leave_days",
    "si_leave_days",
    "unpaid_leave_days",
    "paid_days",
    "unpaid_days",
    "si_absence_days",
)
FIGURES = frozenset(
    DAY_FIGURES
    + (
        "unexcused_absences",
        "leave_days_json",
        "ot_hours_json",
        "ot_hours_ytd",
        "paid_break_hours",
        "segment_ids",
        "figures_locked",
    )
)
DIGITS = (16, 4)


def _utc_naive(dt):
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def _ot_text(values):
    return " · ".join(f"{key} {hours:g}" for key, hours in sorted((values or {}).items()))


class L10nVnPayrollInput(models.Model):
    _name = "l10n_vn.payroll.input"
    _description = "Monthly Payroll Input"
    _order = "period_id desc, employee_id"
    _check_company_auto = True

    period_id = fields.Many2one(
        "l10n_vn.payroll.period", required=True, ondelete="cascade", index=True
    )
    employee_id = fields.Many2one("hr.employee", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="period_id.company_id", store=True)
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    scheduled_days = fields.Float(digits=DIGITS)
    month_scheduled_days = fields.Float(string="Scheduled days in the month", digits=DIGITS)
    days_worked = fields.Float(digits=DIGITS)
    company_leave_days = fields.Float(digits=DIGITS)
    si_leave_days = fields.Float(string="SI leave days", digits=DIGITS)
    unpaid_leave_days = fields.Float(digits=DIGITS)
    paid_days = fields.Float(digits=DIGITS)
    unpaid_days = fields.Float(digits=DIGITS)
    si_absence_days = fields.Float(string="SI absence days", digits=DIGITS)
    unexcused_absences = fields.Integer()
    leave_days_json = fields.Json()
    leave_days_display = fields.Char(string="Leave", compute="_compute_displays")
    ot_hours_json = fields.Json()
    ot_display = fields.Char(string="OT by category", compute="_compute_displays")
    ot_hours = fields.Float(string="OT hours", compute="_compute_ot_hours", store=True)
    ot_hours_ytd = fields.Float(string="OT hours earlier this year")
    paid_break_hours = fields.Float()
    menstruation_days = fields.Integer()
    late_arrivals = fields.Integer()
    attainment = fields.Float(digits=DIGITS)
    attainment_source = fields.Selection(
        [
            ("supervisor", "Supervisor"),
            ("manager", "Manager"),
            ("ie", "IE"),
            ("override", "Override"),
        ]
    )
    attainment_note = fields.Char()
    attainment_by = fields.Many2one("res.users", readonly=True)
    ie_units = fields.Float(string="IE units")
    figures_locked = fields.Boolean(string="Corrected by hand")
    built_at = fields.Datetime(readonly=True)
    segment_ids = fields.One2many("l10n_vn.payroll.input.segment", "input_id")
    line_ids = fields.One2many("l10n_vn.payroll.input.line", "input_id")

    _sql_constraints = [
        (
            "period_employee_unique",
            "unique(period_id, employee_id)",
            "An employee has one summary per period.",
        ),
    ]

    ot_wd_hours = fields.Float(string="OT workday", digits=DIGITS, compute="_compute_ot_hours", store=True)
    ot_rd_hours = fields.Float(string="OT rest day", digits=DIGITS, compute="_compute_ot_hours", store=True)
    ot_hol_hours = fields.Float(string="OT holiday", digits=DIGITS, compute="_compute_ot_hours", store=True)

    @api.depends("ot_hours_json")
    def _compute_ot_hours(self):
        for record in self:
            hours = record.ot_hours_json or {}
            record.ot_hours = sum(hours.values())
            record.ot_wd_hours = hours.get("WD", 0)
            record.ot_rd_hours = hours.get("RD", 0)
            record.ot_hol_hours = hours.get("HOL", 0)

    @api.depends("ot_hours_json", "leave_days_json")
    def _compute_displays(self):
        for record in self:
            record.ot_display = _ot_text(record.ot_hours_json)
            record.leave_days_display = _ot_text(record.leave_days_json)

    @api.constrains("attainment_source", "attainment_note")
    def _check_override_note(self):
        for record in self:
            if record.attainment_source == "override" and not record.attainment_note:
                raise ValidationError(
                    self.env._("An attainment override needs a note (%(employee)s).",
                               employee=record.employee_id.name)
                )

    # ------------------------------------------------------------------ the lock (D76)
    def _l10n_vn_locked_inputs(self):
        """The inputs of ``self`` read by a payslip of an approved or paid run."""
        if not self.ids:
            return self.browse()
        payslips = self.env["hr.payslip"].sudo().search(
            [
                ("l10n_vn_input_id", "in", self.ids),
                ("payslip_run_id.l10n_vn_period_id", "!=", False),
                ("payslip_run_id.state", "in", LOCKED_STATES),
            ]
        )
        return payslips.l10n_vn_input_id

    def _l10n_vn_raise_if_locked(self):
        if self.env.su:
            return
        locked = self._l10n_vn_locked_inputs()
        if locked:
            raise UserError(
                self.env._(
                    "The monthly input of %(employee)s for %(period)s was paid in an approved run.",
                    employee=locked[0].employee_id.name,
                    period=locked[0].period_id.name,
                )
            )

    def unlink(self):
        self._l10n_vn_raise_if_locked()
        return super().unlink()

    def write(self, vals):
        self._l10n_vn_raise_if_locked()
        if FIGURES.intersection(vals) and any(r.period_id.attendance_closed for r in self):
            raise UserError(
                self.env._("Attendance is closed: the summary's figures cannot change.")
            )
        if "attainment" in vals:
            vals = dict(vals, attainment_by=self.env.uid)
        return super().write(vals)

    # ------------------------------------------------------------------ building
    def _l10n_vn_build(self):
        for record in self:
            if record.figures_locked:
                continue
            vals, segments = record._l10n_vn_compute_figures()
            # A figure never written is cached as 0.0 while its column is NULL, and
            # writing 0.0 over that cache is skipped: drop the cache so 0 is stored.
            record.invalidate_recordset([f for f in vals if f in FIGURES])
            vals["segment_ids"] = [Command.clear()] + [Command.create(s) for s in segments]
            vals["built_at"] = fields.Datetime.now()
            record.write(vals)

    def _l10n_vn_days(self):
        """Per local date: scheduled hours, holiday, leave hours by payer, attendance."""
        self.ensure_one()
        period = self.period_id
        employee = self.employee_id.sudo()
        contracts = employee._l10n_vn_period_contracts(period.date_from, period.date_to)
        days = {}
        for contract in contracts:
            start = max(contract.date_start, period.date_from)
            end = min(contract.date_end or period.date_to, period.date_to)
            calendar = contract.resource_calendar_id
            tz = pytz.timezone(calendar.tz or employee.tz or "UTC")
            start_dt = tz.localize(datetime.datetime.combine(start, datetime.time.min))
            end_dt = tz.localize(
                datetime.datetime.combine(end + datetime.timedelta(days=1), datetime.time.min)
            )
            day = start
            while day <= end:
                days[day] = {
                    "scheduled": 0.0,
                    "holiday": False,
                    "leave_company": 0.0,
                    "leave_si": 0.0,
                    "leave_unpaid": 0.0,
                    "leave_types": defaultdict(float),
                    "worked": 0.0,
                    "ot_raw": 0.0,
                    "ot_valid": 0.0,
                    "attended": False,
                    "contract": contract,
                }
                day += datetime.timedelta(days=1)
            resource = employee.resource_id
            intervals = calendar._attendance_intervals_batch(start_dt, end_dt, resources=resource)
            for begin, stop, _line in intervals[resource.id]:
                local_day = begin.astimezone(tz).date()
                if local_day in days:
                    days[local_day]["scheduled"] += (stop - begin).total_seconds() / 3600
            holidays = self.env["resource.calendar.leaves"].sudo().search(
                [
                    ("resource_id", "=", False),
                    ("calendar_id", "in", (calendar.id, False)),
                    ("company_id", "in", (contract.company_id.id, False)),
                    ("date_from", "<", _utc_naive(end_dt)),
                    ("date_to", ">", _utc_naive(start_dt)),
                ]
            )
            for holiday in holidays:
                h_from = pytz.utc.localize(holiday.date_from).astimezone(tz).date()
                h_to = pytz.utc.localize(holiday.date_to).astimezone(tz).date()
                for local_day in days:
                    if h_from <= local_day <= h_to and days[local_day]["contract"] == contract:
                        days[local_day]["holiday"] = True
            for local_day, hours, leave in employee.list_leaves(start_dt, end_dt, calendar=calendar):
                if local_day not in days:
                    continue
                info = days[local_day]
                leave_type = leave.holiday_id.holiday_status_id
                if not leave.holiday_id:
                    info["leave_company"] += hours
                    name = self.env._("Public holiday")
                elif leave_type.unpaid:
                    info["leave_unpaid"] += hours
                    name = leave_type.name
                elif leave_type.l10n_vn_si_paid:
                    info["leave_si"] += hours
                    name = leave_type.name
                else:
                    info["leave_company"] += hours
                    name = leave_type.name
                info["leave_types"][name] += hours
            attendances = self.env["hr.attendance"].sudo().search(
                [
                    ("employee_id", "=", employee.id),
                    ("check_in", ">=", _utc_naive(start_dt)),
                    ("check_in", "<", _utc_naive(end_dt)),
                ]
            )
            for attendance in attendances:
                local_day = pytz.utc.localize(attendance.check_in).astimezone(tz).date()
                if local_day in days:
                    info = days[local_day]
                    info["attended"] = True
                    info["worked"] += attendance.worked_hours
                    # core reports missing hours as negative overtime; only extra time counts
                    info["ot_raw"] += max(0.0, attendance.overtime_hours)
                    info["ot_valid"] += max(0.0, attendance.validated_overtime_hours)
        return days

    def _l10n_vn_month_scheduled_days(self):
        """Dates of the whole month with scheduled hours in the main contract's calendar (D46)."""
        self.ensure_one()
        period = self.period_id
        employee = self.employee_id.sudo()
        contract = employee._l10n_vn_period_contracts(period.date_from, period.date_to)[-1:]
        if not contract:
            return 0
        calendar = contract.resource_calendar_id
        tz = pytz.timezone(calendar.tz or employee.tz or "UTC")
        start = tz.localize(datetime.datetime.combine(period.date_from, datetime.time.min))
        end = tz.localize(
            datetime.datetime.combine(period.date_to + datetime.timedelta(days=1), datetime.time.min)
        )
        resource = employee.resource_id
        intervals = calendar._attendance_intervals_batch(start, end, resources=resource)
        return len(
            {begin.astimezone(tz).date() for begin, stop, _line in intervals[resource.id] if stop > begin}
        )

    def _l10n_vn_pieces(self):
        """The pieces the month splits into (D33).

        Each contract's span inside the month is cut at its pay lines' start and end
        and at the end of a probation clause. Days between contracts are no piece.
        """
        self.ensure_one()
        one_day = datetime.timedelta(days=1)
        period = self.period_id
        pieces = []
        contracts = self.employee_id.sudo()._l10n_vn_period_contracts(
            period.date_from, period.date_to
        )
        for contract in contracts:
            start = max(contract.date_start, period.date_from)
            end = min(contract.date_end or period.date_to, period.date_to)
            cuts = set()
            for line in contract.l10n_vn_line_ids:
                cuts.add(line.date_from)
                if line.date_to:
                    cuts.add(line.date_to + one_day)
            clause = contract.l10n_vn_probation_form == "clause" and contract.trial_date_end
            if clause:
                cuts.add(contract.trial_date_end + one_day)
            bounds = [start] + sorted(c for c in cuts if start < c <= end) + [end + one_day]
            for begin, after in zip(bounds, bounds[1:]):
                last = after - one_day
                if contract.l10n_vn_probation_form == "contract":
                    probation = True
                else:
                    probation = bool(clause) and last <= contract.trial_date_end
                pieces.append(
                    {"date_from": begin, "date_to": last, "contract": contract,
                     "probation": probation}
                )
        return pieces

    def _l10n_vn_compute_figures(self):
        self.ensure_one()
        period = self.period_id
        days = self._l10n_vn_days()
        minimum = self.env["base.time.parameter"]._strict_get(
            "vn.policy.ot_min_hours_day", period.date_to, company=period.company_id
        )
        nursing_until = self.employee_id.sudo()._l10n_vn_nursing_until()
        per_day = {}
        absences = 0
        leave_days = defaultdict(float)
        for day in sorted(days):
            info = days[day]
            row = {"worked": 0.0, "company": 0.0, "si": 0.0, "unpaid": 0.0, "credit_days": 0.0,
                   "remaining": 0.0, "scheduled": info["scheduled"], "ot": {}}
            scheduled = info["scheduled"]
            if scheduled > 0:
                normal = max(0.0, info["worked"] - info["ot_raw"])
                worked = min(1.0, normal / scheduled)
                company = min(1.0 - worked, info["leave_company"] / scheduled)
                si = min(1.0 - worked - company, info["leave_si"] / scheduled)
                unpaid = min(1.0 - worked - company - si, info["leave_unpaid"] / scheduled)
                shortfall = max(
                    0.0,
                    scheduled - normal - info["leave_company"] - info["leave_si"]
                    - info["leave_unpaid"],
                )
                credit = 0.0
                if normal > 0 and nursing_until and day < nursing_until:
                    credit = min(1.0, shortfall)
                row.update(worked=worked, company=company, si=si, unpaid=unpaid,
                           credit_hours=credit,
                           remaining=shortfall - credit if normal > 0 else 0.0)
                if not info["attended"] and not (
                    info["leave_company"] or info["leave_si"] or info["leave_unpaid"]
                ):
                    absences += 1
                for name, hours in info["leave_types"].items():
                    leave_days[name] += hours / scheduled
            if info["ot_valid"] and info["ot_valid"] >= minimum:
                if info["holiday"]:
                    category = "HOL"
                elif scheduled <= 0:
                    category = "RD"
                else:
                    category = "WD"
                row["ot"] = {category: info["ot_valid"]}
            per_day[day] = row
        pool = (self.menstruation_days or 0) * 0.5
        for day in sorted(per_day):
            row = per_day[day]
            if pool <= 0:
                break
            if row["remaining"] > 0:
                extra = min(pool, row["remaining"])
                row["credit_hours"] = row.get("credit_hours", 0.0) + extra
                row["remaining"] -= extra
                pool -= extra
        break_hours = 0.0
        for row in per_day.values():
            if row["scheduled"] > 0:
                row["credit_days"] = row.get("credit_hours", 0.0) / row["scheduled"]
                break_hours += row.get("credit_hours", 0.0)

        def total(rows, key):
            return sum(r[key] for r in rows)

        def ot_sum(rows):
            result = defaultdict(float)
            for r in rows:
                for key, hours in r["ot"].items():
                    result[key] += hours
            return {key: round(hours, 4) for key, hours in result.items()}

        rows = list(per_day.values())
        scheduled_days = sum(1 for r in rows if r["scheduled"] > 0)
        paid_days = total(rows, "worked") + total(rows, "company") + total(rows, "credit_days")
        earlier = self.search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("company_id", "=", period.company_id.id),
                ("period_id.date_from", ">=", period.date_from.replace(month=1, day=1)),
                ("period_id.date_from", "<", period.date_from),
            ]
        )
        vals = {
            "scheduled_days": scheduled_days,
            "month_scheduled_days": self._l10n_vn_month_scheduled_days(),
            "days_worked": round(total(rows, "worked"), 4),
            "company_leave_days": round(total(rows, "company"), 4),
            "si_leave_days": round(total(rows, "si"), 4),
            "unpaid_leave_days": round(total(rows, "unpaid"), 4),
            "paid_days": round(paid_days, 4),
            "unpaid_days": round(max(0.0, scheduled_days - paid_days), 4),
            "si_absence_days": round(max(0.0, scheduled_days - paid_days), 4),
            "unexcused_absences": absences,
            "leave_days_json": {k: round(v, 4) for k, v in leave_days.items()},
            "ot_hours_json": ot_sum(rows),
            "ot_hours_ytd": sum(earlier.mapped("ot_hours")) + sum(
                self.env["l10n_vn.payroll.opening"].sudo().search(
                    [
                        ("company_id", "=", period.company_id.id),
                        ("employee_id", "=", self.employee_id.id),
                        ("year", "=", period.date_from.year),
                    ]
                ).mapped("ot_hours")
            ),
            "paid_break_hours": round(break_hours, 4),
        }
        segments = []
        pieces = self._l10n_vn_pieces()
        if len(pieces) > 1:
            for item in pieces:
                piece = [
                    per_day[d] for d in per_day if item["date_from"] <= d <= item["date_to"]
                ]
                segments.append(
                    {
                        "date_from": item["date_from"],
                        "date_to": item["date_to"],
                        "contract_id": item["contract"].id,
                        "paid_days": round(
                            total(piece, "worked") + total(piece, "company")
                            + total(piece, "credit_days"),
                            4,
                        ),
                        "days_worked": round(total(piece, "worked"), 4),
                        "ot_hours_json": ot_sum(piece),
                    }
                )
        return vals, segments


class L10nVnPayrollInputSegment(models.Model):
    _name = "l10n_vn.payroll.input.segment"
    _description = "Monthly Payroll Input Segment"
    _order = "input_id, date_from"

    input_id = fields.Many2one(
        "l10n_vn.payroll.input", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="input_id.company_id", store=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    contract_id = fields.Many2one("hr.contract")
    paid_days = fields.Float(digits=DIGITS)
    days_worked = fields.Float(digits=DIGITS)
    ot_hours_json = fields.Json()
    ot_display = fields.Char(string="OT by category", compute="_compute_ot_display")

    @api.depends("ot_hours_json")
    def _compute_ot_display(self):
        for record in self:
            record.ot_display = _ot_text(record.ot_hours_json)

    @api.model_create_multi
    def create(self, vals_list):
        self.env["l10n_vn.payroll.input"].browse(
            [v["input_id"] for v in vals_list if v.get("input_id")]
        )._l10n_vn_raise_if_locked()
        return super().create(vals_list)

    def write(self, vals):
        self.input_id._l10n_vn_raise_if_locked()
        return super().write(vals)

    def unlink(self):
        self.input_id._l10n_vn_raise_if_locked()
        return super().unlink()


class L10nVnPayrollInputLine(models.Model):
    _name = "l10n_vn.payroll.input.line"
    _description = "Monthly Payroll Input Line"
    _order = "input_id, id"
    _check_company_auto = True

    input_id = fields.Many2one(
        "l10n_vn.payroll.input", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="input_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    component_id = fields.Many2one(
        "l10n_vn.payroll.component", required=True, ondelete="restrict", check_company=True
    )
    amount = fields.Monetary()
    hours = fields.Float()
    period_ref = fields.Date(string="Belongs to month")
    description = fields.Char()
    approved_by = fields.Many2one("res.users", readonly=True)
    approved_at = fields.Datetime(readonly=True)

    @api.constrains("component_id", "period_ref")
    def _check_line(self):
        for line in self:
            component = line.component_id
            if not line.period_ref:
                if component.amount_source != "entered":
                    raise ValidationError(
                        self.env._(
                            "Component %(code)s is not entered each month; "
                            "only an adjustment to an earlier month may use it.",
                            code=component.code,
                        )
                    )
                continue
            if component.kind not in ("earning", "deduction"):
                raise ValidationError(
                    self.env._("An adjustment corrects an earning or a deduction.")
                )
            if line.period_ref.day != 1 or line.period_ref >= line.input_id.period_id.date_from:
                raise ValidationError(
                    self.env._(
                        "An adjustment belongs to an earlier month, given by its first day."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        self.env["l10n_vn.payroll.input"].browse(
            [v["input_id"] for v in vals_list if v.get("input_id")]
        )._l10n_vn_raise_if_locked()
        return super().create(vals_list)

    def write(self, vals):
        self.input_id._l10n_vn_raise_if_locked()
        if {"component_id", "amount", "hours", "period_ref"}.intersection(vals):
            vals = dict(vals, approved_by=False, approved_at=False)
        return super().write(vals)

    def unlink(self):
        self.input_id._l10n_vn_raise_if_locked()
        return super().unlink()

    def _check_approver(self):
        if not self.env.user.has_group("l10n_vn_payroll.group_payroll_approver"):
            raise AccessError(self.env._("Only approvers approve entered amounts."))

    def action_approve(self):
        self._check_approver()
        self.sudo().write({"approved_by": self.env.uid, "approved_at": fields.Datetime.now()})
        return True

    def action_reset_approval(self):
        self._check_approver()
        self.sudo().write({"approved_by": False, "approved_at": False})
        return True
