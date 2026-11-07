# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

LOCKED_STATES = ("approved", "paid")
OFFICER = "payroll.group_payroll_user"
REVIEWER = "l10n_vn_payroll.group_payroll_reviewer"
APPROVER = "l10n_vn_payroll.group_payroll_approver"


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    state = fields.Selection(
        selection_add=[
            ("draft",),
            ("calculated", "Calculated"),
            ("reviewed", "Reviewed"),
            ("approved", "Approved"),
            ("paid", "Paid"),
        ],
        ondelete={
            "calculated": "set default",
            "reviewed": "set default",
            "approved": "set default",
            "paid": "set default",
        },
    )
    l10n_vn_period_id = fields.Many2one(
        "l10n_vn.payroll.period", string="Payroll Period", ondelete="restrict", index=True
    )
    l10n_vn_kind = fields.Selection(
        [("regular", "Regular"), ("off_cycle", "Off-cycle")], string="Kind", default="regular"
    )
    l10n_vn_employee_ids = fields.Many2many(
        "hr.employee", "l10n_vn_payslip_run_employee_rel", string="Employees"
    )
    l10n_vn_calculated_by = fields.Many2one("res.users", readonly=True)
    l10n_vn_calculated_at = fields.Datetime(readonly=True)
    l10n_vn_reviewed_by = fields.Many2one("res.users", readonly=True)
    l10n_vn_reviewed_at = fields.Datetime(readonly=True)
    l10n_vn_approved_by = fields.Many2one("res.users", readonly=True)
    l10n_vn_approved_at = fields.Datetime(readonly=True)
    l10n_vn_check_result_ids = fields.One2many(
        "l10n_vn.payroll.check.result", "run_id", string="Checks", readonly=True
    )
    l10n_vn_error_count = fields.Integer(compute="_compute_l10n_vn_counts")
    l10n_vn_warning_count = fields.Integer(compute="_compute_l10n_vn_counts")

    @api.depends("l10n_vn_check_result_ids.level", "l10n_vn_check_result_ids.note")
    def _compute_l10n_vn_counts(self):
        for run in self:
            results = run.sudo().l10n_vn_check_result_ids
            run.l10n_vn_error_count = len(results.filtered(lambda r: r.level == "error"))
            run.l10n_vn_warning_count = len(
                results.filtered(lambda r: r.level == "warning" and not r.note)
            )

    @api.constrains("l10n_vn_period_id", "l10n_vn_kind")
    def _check_l10n_vn_regular(self):
        for run in self.filtered(lambda r: r.l10n_vn_period_id and r.l10n_vn_kind == "regular"):
            others = self.sudo().search_count(
                [
                    ("id", "!=", run.id),
                    ("l10n_vn_period_id", "=", run.l10n_vn_period_id.id),
                    ("l10n_vn_kind", "=", "regular"),
                ]
            )
            if others:
                raise ValidationError(
                    self.env._(
                        "Payroll period %(period)s already has a regular run.",
                        period=run.l10n_vn_period_id.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        Period = self.env["l10n_vn.payroll.period"].sudo()
        for vals in vals_list:
            if vals.get("l10n_vn_period_id"):
                period = Period.browse(vals["l10n_vn_period_id"])
                vals["date_start"] = period.date_from
                vals["date_end"] = period.date_to
                vals["company_id"] = period.company_id.id
                if not vals.get("name"):
                    name = self.env._("Payroll %(period)s", period=period.name)
                    if vals.get("l10n_vn_kind") == "off_cycle":
                        name = self.env._("%(name)s, off-cycle", name=name)
                    vals["name"] = name
        return super().create(vals_list)

    # ------------------------------------------------------------------ helpers
    def _l10n_vn_require(self, *groups):
        if not any(self.env.user.has_group(group) for group in groups):
            raise AccessError(self.env._("Your payroll role does not allow this step."))

    def _l10n_vn_only(self):
        if not all(run.l10n_vn_period_id for run in self):
            raise UserError(self.env._("This step is for runs of a payroll period."))

    def _l10n_vn_paid_elsewhere(self, employees):
        """Employees with a payslip in another approved or paid run of the period (D74)."""
        self.ensure_one()
        slips = self.env["hr.payslip"].sudo().search(
            [
                ("employee_id", "in", employees.ids),
                ("payslip_run_id", "!=", self.id),
                ("payslip_run_id.l10n_vn_period_id", "=", self.l10n_vn_period_id.id),
                ("payslip_run_id.state", "in", LOCKED_STATES),
            ]
        )
        return slips.employee_id

    def _l10n_vn_employees(self):
        """The run's employees (D73)."""
        self.ensure_one()
        period = self.l10n_vn_period_id
        if self.l10n_vn_kind == "off_cycle":
            employees = self.l10n_vn_employee_ids.sudo()
        else:
            contracts = self.env["hr.contract"].sudo().search(
                [
                    ("company_id", "=", period.company_id.id),
                    ("state", "in", ("open", "close")),
                    ("date_start", "<=", period.date_to),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", period.date_from),
                ]
            )
            employees = contracts.employee_id.filtered(
                lambda e: e._l10n_vn_period_contracts(period.date_from, period.date_to)[
                    -1:
                ].struct_id.l10n_vn_payroll
            )
        return employees - self._l10n_vn_paid_elsewhere(employees)

    def _l10n_vn_generate(self):
        """Missing payslips made as OCA's batch makes them; payslips no longer due removed."""
        self.ensure_one()
        period = self.l10n_vn_period_id
        employees = self._l10n_vn_employees()
        Payslip = self.env["hr.payslip"]
        stale = self.slip_ids.filtered(
            lambda p: p.employee_id not in employees and p.state in ("draft", "verify")
        )
        stale.action_payslip_draft()
        stale.unlink()
        created = Payslip
        for employee in employees - self.slip_ids.employee_id:
            vals = Payslip.get_payslip_vals(period.date_from, period.date_to, employee.id)["value"]
            created |= Payslip.create(
                {
                    "employee_id": employee.id,
                    "date_from": period.date_from,
                    "date_to": period.date_to,
                    "contract_id": vals.get("contract_id"),
                    "struct_id": vals.get("struct_id"),
                    "worked_days_line_ids": [
                        (0, 0, v) for v in vals.get("worked_days_line_ids", [])
                    ],
                    "payslip_run_id": self.id,
                    "company_id": period.company_id.id,
                }
            )
        created._compute_name()

    def _l10n_vn_clear_review(self):
        return {"l10n_vn_reviewed_by": False, "l10n_vn_reviewed_at": False}

    # ------------------------------------------------------------------ transitions (D72)
    def action_l10n_vn_calculate(self):
        self._l10n_vn_require(OFFICER)
        self._l10n_vn_only()
        for run in self.sudo():
            if run.state not in ("draft", "calculated", "reviewed"):
                raise UserError(self.env._("An approved run cannot be calculated again."))
            period = run.l10n_vn_period_id
            if not period.attendance_closed:
                raise UserError(
                    self.env._("Attendance of %(period)s is not closed.", period=period.name)
                )
            if period.ie_required and not period.ie_closed:
                raise UserError(
                    self.env._("IE figures of %(period)s are not closed.", period=period.name)
                )
            run._l10n_vn_generate()
            run.slip_ids.compute_sheet()
            run.write(
                dict(
                    run._l10n_vn_clear_review(),
                    state="calculated",
                    l10n_vn_calculated_by=self.env.uid,
                    l10n_vn_calculated_at=fields.Datetime.now(),
                )
            )
        return True

    def action_l10n_vn_review(self):
        self._l10n_vn_require(REVIEWER)
        self._l10n_vn_only()
        for run in self.sudo():
            if run.state != "calculated":
                raise UserError(self.env._("Only a calculated run is reviewed."))
            blocking = run.l10n_vn_check_result_ids.filtered(
                lambda r: r.level == "error" or (r.level == "warning" and not r.note)
            )
            if blocking:
                names = ", ".join(blocking.payslip_id.employee_id.mapped("name")[:3])
                raise UserError(
                    self.env._(
                        "Errors, or warnings without a note, remain on the payslips of "
                        "%(names)s.",
                        names=names,
                    )
                )
            run.write(
                {
                    "state": "reviewed",
                    "l10n_vn_reviewed_by": self.env.uid,
                    "l10n_vn_reviewed_at": fields.Datetime.now(),
                }
            )
        return True

    def action_l10n_vn_back_to_calculated(self):
        self._l10n_vn_require(OFFICER)
        self._l10n_vn_only()
        for run in self.sudo():
            if run.state != "reviewed":
                raise UserError(self.env._("Only a reviewed run goes back to calculated."))
            run.write(dict(run._l10n_vn_clear_review(), state="calculated"))
        return True

    def action_l10n_vn_approve(self):
        self._l10n_vn_require(APPROVER)
        self._l10n_vn_only()
        for run in self.sudo():
            if run.state != "reviewed":
                raise UserError(self.env._("A run is approved after review."))
            if run.l10n_vn_calculated_by.id == self.env.uid:
                raise UserError(
                    self.env._("The person who calculated the run cannot approve it.")
                )
            if run.l10n_vn_check_result_ids.filtered(lambda r: r.level == "error"):
                raise UserError(self.env._("The run still has errors."))
            paid = run._l10n_vn_paid_elsewhere(run.slip_ids.employee_id)
            if paid:
                raise UserError(
                    self.env._(
                        "%(employees)s already have an approved payslip for %(period)s.",
                        employees=", ".join(paid.mapped("name")),
                        period=run.l10n_vn_period_id.name,
                    )
                )
            run.slip_ids.with_context(without_compute_sheet=True).action_payslip_done()
            run.write(
                {
                    "state": "approved",
                    "l10n_vn_approved_by": self.env.uid,
                    "l10n_vn_approved_at": fields.Datetime.now(),
                }
            )
        return True

    def action_l10n_vn_mark_paid(self):
        self._l10n_vn_require(OFFICER)
        self._l10n_vn_only()
        for run in self.sudo():
            if run.state != "approved":
                raise UserError(self.env._("Only an approved run is marked as paid."))
            run.write({"state": "paid"})
        return True

    def action_print_l10n_vn_payslips(self):
        self.ensure_one()
        return self.env.ref("l10n_vn_payroll.action_report_l10n_vn_payslip").report_action(
            self.slip_ids
        )

    def action_open_l10n_vn_checks(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_vn_payroll.l10n_vn_payroll_check_result_action"
        )
        action["domain"] = [("run_id", "=", self.id)]
        return action

    # ------------------------------------------------------------------ OCA's own steps
    def close_payslip_run(self):
        if any(run.l10n_vn_period_id for run in self):
            raise UserError(self.env._("A run of a payroll period follows its own steps."))
        return super().close_payslip_run()

    def draft_payslip_run(self):
        if any(run.l10n_vn_period_id for run in self):
            raise UserError(self.env._("A run of a payroll period follows its own steps."))
        return super().draft_payslip_run()

    def unlink(self):
        if any(run.l10n_vn_period_id and run.state != "draft" for run in self):
            raise UserError(self.env._("Only a draft run of a payroll period can be deleted."))
        return super().unlink()
