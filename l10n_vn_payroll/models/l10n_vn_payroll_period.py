# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class L10nVnPayrollPeriod(models.Model):
    _name = "l10n_vn.payroll.period"
    _description = "Payroll Period"
    _order = "date_from desc"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(compute="_compute_date_to", store=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    attendance_closed = fields.Boolean(readonly=True)
    attendance_closed_by = fields.Many2one("res.users", readonly=True)
    attendance_closed_at = fields.Datetime(readonly=True)
    ie_required = fields.Boolean(string="IE figures required")
    ie_closed = fields.Boolean(string="IE closed")
    input_ids = fields.One2many("l10n_vn.payroll.input", "period_id")
    input_count = fields.Integer(compute="_compute_input_count")

    _sql_constraints = [
        (
            "company_month_unique",
            "unique(company_id, date_from)",
            "A company has one payroll period per month.",
        ),
    ]

    @api.depends("date_from")
    def _compute_name(self):
        for period in self:
            period.name = period.date_from.strftime("%Y-%m") if period.date_from else False

    @api.depends("date_from")
    def _compute_date_to(self):
        for period in self:
            period.date_to = (
                period.date_from + relativedelta(day=31) if period.date_from else False
            )

    def _compute_input_count(self):
        for period in self:
            period.input_count = len(period.input_ids)

    @api.constrains("date_from")
    def _check_first_day(self):
        for period in self:
            if period.date_from.day != 1:
                raise ValidationError(self.env._("A payroll period starts on the 1st of a month."))

    def _employees_in_scope(self):
        self.ensure_one()
        contracts = (
            self.env["hr.contract"]
            .sudo()
            .search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("state", "in", ("open", "close")),
                    ("date_start", "<=", self.date_to),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", self.date_from),
                ]
            )
        )
        return contracts.employee_id

    def action_build(self):
        Input = self.env["l10n_vn.payroll.input"]
        for period in self:
            if period.attendance_closed:
                raise UserError(
                    self.env._("Attendance of %(period)s is closed.", period=period.name)
                )
            existing = {i.employee_id.id: i for i in period.input_ids}
            inputs = Input
            for employee in period._employees_in_scope():
                inputs |= existing.get(employee.id) or Input.create(
                    {"period_id": period.id, "employee_id": employee.id}
                )
            inputs._l10n_vn_build()
        return True

    def action_close_attendance(self):
        for period in self:
            if not period.input_ids:
                raise UserError(
                    self.env._("Build the summaries of %(period)s first.", period=period.name)
                )
            period.write(
                {
                    "attendance_closed": True,
                    "attendance_closed_by": self.env.uid,
                    "attendance_closed_at": fields.Datetime.now(),
                }
            )
        return True

    def action_reopen_attendance(self):
        if not self.env.user.has_group("payroll.group_payroll_manager"):
            raise AccessError(self.env._("Only payroll managers reopen attendance."))
        self.write(
            {
                "attendance_closed": False,
                "attendance_closed_by": False,
                "attendance_closed_at": False,
            }
        )
        return True

    def action_open_inputs(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_vn_payroll.l10n_vn_payroll_input_action"
        )
        action["domain"] = [("period_id", "=", self.id)]
        action["context"] = {"default_period_id": self.id}
        return action
