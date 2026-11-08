# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .hr_payslip_run import LOCKED_STATES

KINDS = [
    ("si_monthly", "SI contributions"),
    ("si_changes", "SI changes"),
    ("pit_period", "PIT for a period"),
    ("pit_annual", "Annual PIT finalisation"),
    ("ot_schedule", "OT schedule"),
    ("union", "Union fee and dues"),
]
FUNDS = {
    "EE_SI": "ee_si", "EE_HI": "ee_hi", "EE_UI": "ee_ui", "DUES": "dues",
    "ER_PENSION": "er_pension", "ER_SICKNESS": "er_sickness", "ER_ACCIDENT": "er_accident",
    "ER_HI": "er_hi", "ER_UI": "er_ui", "UNION_FEE": "union_fee",
}


def _months(first, last):
    month = first.replace(day=1)
    while month <= last:
        yield month
        month += relativedelta(months=1)


class L10nVnPayrollStatement(models.Model):
    _name = "l10n_vn.payroll.statement"
    _description = "Payroll Statement"
    _order = "date_from desc, kind"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True)
    kind = fields.Selection(KINDS, required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")], default="draft", required=True, readonly=True
    )
    line_ids = fields.One2many("l10n_vn.payroll.statement.line", "statement_id", readonly=True)
    line_count = fields.Integer(compute="_compute_line_count")
    note = fields.Text()

    @api.depends("kind", "date_from", "date_to")
    def _compute_name(self):
        labels = dict(KINDS)
        for statement in self:
            if not (statement.kind and statement.date_from and statement.date_to):
                statement.name = False
                continue
            first, last = statement.date_from, statement.date_to
            span = (f"{first:%m/%Y}" if first.month == last.month and first.year == last.year
                    else f"{first:%m/%Y}–{last:%m/%Y}")
            statement.name = f"{labels[statement.kind]} {span}"

    def _compute_line_count(self):
        for statement in self:
            statement.line_count = len(statement.line_ids)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for statement in self:
            last_day = statement.date_to + datetime.timedelta(days=1)
            if statement.date_from.day != 1 or last_day.day != 1 or statement.date_to < statement.date_from:
                raise ValidationError(
                    self.env._("A statement runs from the first day of a month to the last day of one.")
                )

    def write(self, vals):
        if not self.env.su and set(vals) - {"state"} and any(s.state == "done" for s in self):
            raise UserError(self.env._("A done statement cannot change; set it back to draft first."))
        return super().write(vals)

    def unlink(self):
        if any(s.state == "done" for s in self):
            raise UserError(self.env._("Only a draft statement can be deleted."))
        return super().unlink()

    # ------------------------------------------------------------------ actions (D89)
    def action_generate(self):
        for statement in self:
            if statement.state != "draft":
                raise UserError(self.env._("Only a draft statement is generated."))
            values = getattr(statement, f"_l10n_vn_lines_{statement.kind}")()
            statement.line_ids.unlink()
            self.env["l10n_vn.payroll.statement.line"].create(
                [dict(v, statement_id=statement.id) for v in values]
            )
        return True

    def action_done(self):
        self.write({"state": "done"})
        return True

    def action_draft(self):
        if not self.env.user.has_group("payroll.group_payroll_manager"):
            raise AccessError(self.env._("Only payroll managers reopen a statement."))
        self.sudo().write({"state": "draft"})
        return True

    def action_open_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "l10n_vn.payroll.statement.line",
            "view_mode": "list",
            "domain": [("statement_id", "=", self.id)],
            "context": {"create": False},
        }

    # ------------------------------------------------------------------ sources (D86)
    def _l10n_vn_payslips(self, first=None, last=None):
        self.ensure_one()
        return self.env["hr.payslip"].sudo().search(
            [
                ("company_id", "=", self.company_id.id),
                ("date_from", ">=", first or self.date_from),
                ("date_from", "<=", last or self.date_to),
                ("payslip_run_id.l10n_vn_period_id", "!=", False),
                ("payslip_run_id.state", "in", LOCKED_STATES),
            ],
            order="employee_id, date_from",
        )

    def _l10n_vn_engine(self, context):
        """The snapshot's amounts by engine code, positive."""
        lines = context.get("lines", [])
        components = self.env["l10n_vn.payroll.component"].sudo().browse(
            {line["component_id"] for line in lines}
        )
        engine = {c.id: c.engine_code for c in components}
        amounts = defaultdict(int)
        for line in lines:
            code = engine.get(line["component_id"])
            if code:
                amounts[code] += abs(line["amount"])
        return amounts

    def _l10n_vn_person(self, employee):
        employee = employee.sudo()
        return {
            "employee_id": employee.id,
            "employee_number": employee.identification_id,
            "personal_id": employee.l10n_vn_personal_id,
            "si_number": employee.ssnid,
        }

    @staticmethod
    def _liable(context):
        return bool((context.get("contributions") or {}).get("liable"))

    def _l10n_vn_pit_figures(self, context):
        pit = context.get("pit") or {}
        gross = context.get("gross", 0)
        insurance = context.get("employee_insurance", 0)
        if pit.get("method") == "progressive":
            exempt, taxable = pit.get("exempt") or 0, pit.get("taxable") or 0
            family = gross - exempt - insurance - taxable
        else:
            exempt, taxable, family = 0, gross, 0
        return {
            "income": gross, "income_exempt": exempt, "insurance": insurance,
            "family_deduction": family, "taxable": max(taxable, 0), "pit": pit.get("pit", 0),
            "dependents": pit.get("dependents") or 0, "pit_method": pit.get("method"),
        }

    # ------------------------------------------------------------------ kinds (D85)
    def _l10n_vn_lines_si_monthly(self):
        values = []
        for slip in self._l10n_vn_payslips():
            context = slip.l10n_vn_context or {}
            if not self._liable(context):
                continue
            contributions = context["contributions"]
            amounts = self._l10n_vn_engine(context)
            line = dict(self._l10n_vn_person(slip.employee_id), date_from=slip.date_from,
                        si_base=contributions.get("si_capped") or 0,
                        ui_base=contributions.get("ui_capped") or 0)
            line.update({field: amounts.get(code, 0) for code, field in FUNDS.items()})
            values.append(line)
        return values

    def _l10n_vn_lines_union(self):
        values = []
        for slip in self._l10n_vn_payslips():
            context = slip.l10n_vn_context or {}
            if not self._liable(context):
                continue
            amounts = self._l10n_vn_engine(context)
            values.append(dict(self._l10n_vn_person(slip.employee_id), date_from=slip.date_from,
                               union_fee=amounts.get("UNION_FEE", 0), dues=amounts.get("DUES", 0)))
        return values

    def _l10n_vn_lines_pit_period(self, opening=False):
        totals = {}
        months = defaultdict(int)
        for slip in self._l10n_vn_payslips():
            figures = self._l10n_vn_pit_figures(slip.l10n_vn_context or {})
            line = totals.setdefault(slip.employee_id, dict.fromkeys(
                ("income", "income_exempt", "insurance", "family_deduction", "taxable", "pit"), 0))
            for key in ("income", "income_exempt", "insurance", "family_deduction", "taxable", "pit"):
                line[key] += figures[key]
            line["dependents"] = figures["dependents"]
            line["pit_method"] = figures["pit_method"]
            months[slip.employee_id] += 1
        if opening:
            for row in self.env["l10n_vn.payroll.opening"].sudo().search(
                [("company_id", "=", self.company_id.id), ("year", "=", self.date_from.year)]
            ):
                line = totals.setdefault(row.employee_id, dict.fromkeys(
                    ("income", "income_exempt", "insurance", "family_deduction", "taxable", "pit"), 0))
                for key in ("income", "income_exempt", "insurance", "family_deduction", "taxable", "pit"):
                    line[key] += row[key]
                months[row.employee_id] += row.months
        return [
            dict(self._l10n_vn_person(employee), months=months[employee], **line)
            for employee, line in totals.items()
        ]

    def _l10n_vn_lines_pit_annual(self):
        return self._l10n_vn_lines_pit_period(opening=True)

    def _l10n_vn_lines_ot_schedule(self):
        values = []
        for slip in self._l10n_vn_payslips():
            context = slip.l10n_vn_context or {}
            lines = context.get("lines", [])
            components = self.env["l10n_vn.payroll.component"].sudo().browse(
                {line["component_id"] for line in lines}
            )
            ot_ids = {c.id for c in components if c.amount_source == "ot"}
            ot_pay = sum(line["amount"] for line in lines if line["component_id"] in ot_ids)
            hours = (context.get("input") or {}).get("ot_hours_json") or {}
            if not ot_pay and not any(hours.values()):
                continue
            values.append(dict(
                self._l10n_vn_person(slip.employee_id), date_from=slip.date_from,
                ot_wd_hours=hours.get("WD", 0), ot_rd_hours=hours.get("RD", 0),
                ot_hol_hours=hours.get("HOL", 0), night_hours=hours.get("NIGHT", 0),
                ot_night_hours=sum(hours.get(k, 0) for k in ("NWD", "NWD_AFTER", "NRD", "NHOL")),
                ot_pay=ot_pay,
                ot_exempt=(context.get("pit") or {}).get("ot_exempt") or 0,
            ))
        return values

    def _l10n_vn_lines_si_changes(self):
        """Each month against the one before (D87)."""
        values = []
        for month in _months(self.date_from, self.date_to):
            last = month + relativedelta(day=31)
            before = month - relativedelta(months=1)
            now = {s.employee_id: s for s in self._l10n_vn_payslips(month, last)}
            prev = {s.employee_id: s for s in self._l10n_vn_payslips(before, month - relativedelta(days=1))}
            for employee in set(now) | set(prev):
                cur_ctx = now[employee].l10n_vn_context if employee in now else {}
                prev_ctx = prev[employee].l10n_vn_context if employee in prev else {}
                cur_ctx, prev_ctx = cur_ctx or {}, prev_ctx or {}
                liable_now, liable_before = self._liable(cur_ctx), self._liable(prev_ctx)
                change, date = None, month
                if liable_now and not liable_before:
                    started = employee._l10n_vn_period_contracts(month, last).filtered(
                        lambda c: c.date_start >= month
                    )
                    change = "join" if started else "return"
                    date = started[:1].date_start or month
                elif liable_before and not liable_now:
                    contract = employee._l10n_vn_period_contracts(before, before + relativedelta(day=31))[-1:]
                    if contract.date_end and contract.date_end <= last:
                        change, date = "leave", contract.date_end
                    else:
                        change = "absence"
                elif liable_now and liable_before:
                    base_now = cur_ctx["contributions"].get("si_capped")
                    base_before = prev_ctx["contributions"].get("si_capped")
                    if base_now != base_before:
                        change = "base"
                if change:
                    values.append(dict(
                        self._l10n_vn_person(employee), date_from=month, change_type=change,
                        change_date=date,
                        si_base=(cur_ctx.get("contributions") or {}).get("si_capped") or 0,
                    ))
        return values


class L10nVnPayrollStatementLine(models.Model):
    _name = "l10n_vn.payroll.statement.line"
    _description = "Payroll Statement Line"
    _order = "statement_id, employee_id, date_from"

    statement_id = fields.Many2one(
        "l10n_vn.payroll.statement", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="statement_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    kind = fields.Selection(related="statement_id.kind", store=True)
    employee_id = fields.Many2one("hr.employee", required=True)
    employee_number = fields.Char()
    personal_id = fields.Char(string="Personal ID")
    si_number = fields.Char(string="SI Number")
    date_from = fields.Date(string="Month")
    change_type = fields.Selection(
        [("join", "Joins"), ("leave", "Leaves"), ("absence", "Long absence"),
         ("return", "Returns"), ("base", "SI base change")]
    )
    change_date = fields.Date()
    si_base = fields.Monetary(string="SI Base")
    ui_base = fields.Monetary(string="UI Base")
    ee_si = fields.Monetary(string="Employee SI")
    ee_hi = fields.Monetary(string="Employee HI")
    ee_ui = fields.Monetary(string="Employee UI")
    er_pension = fields.Monetary(string="Employer Pension")
    er_sickness = fields.Monetary(string="Employer Sickness")
    er_accident = fields.Monetary(string="Employer Accident")
    er_hi = fields.Monetary(string="Employer HI")
    er_ui = fields.Monetary(string="Employer UI")
    union_fee = fields.Monetary()
    dues = fields.Monetary(string="Union Dues")
    income = fields.Monetary()
    income_exempt = fields.Monetary(string="Exempt Income")
    insurance = fields.Monetary()
    family_deduction = fields.Monetary()
    taxable = fields.Monetary(string="Taxable Income")
    pit = fields.Monetary(string="PIT")
    dependents = fields.Integer()
    pit_method = fields.Selection(
        [("progressive", "Progressive"), ("flat_short", "Flat 10%"), ("flat_nonresident", "Flat 20%")]
    )
    months = fields.Integer()
    ot_wd_hours = fields.Float(string="OT workday", digits=(16, 4))
    ot_rd_hours = fields.Float(string="OT rest day", digits=(16, 4))
    ot_hol_hours = fields.Float(string="OT holiday", digits=(16, 4))
    night_hours = fields.Float(string="Night hours (normal)", digits=(16, 4))
    ot_night_hours = fields.Float(string="OT at night", digits=(16, 4))
    ot_pay = fields.Monetary(string="OT Pay")
    ot_exempt = fields.Monetary(string="OT Exempt from PIT")
    note = fields.Char()

    def _l10n_vn_refuse_if_done(self, statements):
        if not self.env.su and any(s.state == "done" for s in statements):
            raise UserError(self.env._("A done statement cannot change; set it back to draft first."))

    @api.model_create_multi
    def create(self, vals_list):
        self._l10n_vn_refuse_if_done(
            self.env["l10n_vn.payroll.statement"].browse(
                [v["statement_id"] for v in vals_list if v.get("statement_id")]
            )
        )
        return super().create(vals_list)

    def write(self, vals):
        self._l10n_vn_refuse_if_done(self.statement_id)
        return super().write(vals)

    def unlink(self):
        self._l10n_vn_refuse_if_done(self.statement_id)
        return super().unlink()
