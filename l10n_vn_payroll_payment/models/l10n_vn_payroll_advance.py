# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from types import SimpleNamespace

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import format_date

OFFICER = "payroll.group_payroll_user"
REVIEWER = "l10n_vn_payroll.group_payroll_reviewer"
# written only by the module's steps or as superuser (D10)
CONTROLLED = {"state", "approved_by", "approved_at", "paid_date", "limit_at_approval"}
# fixed once an advance leaves draft (D10)
FROZEN = {"employee_id", "company_id", "date", "amount", "reason", "limit_note"}


def _employee_names(advances, limit=3):
    return ", ".join(advances.mapped("employee_id.name")[:limit])


class L10nVnPayrollAdvance(models.Model):
    _name = "l10n_vn.payroll.advance"
    _description = "Salary Advance"
    _order = "date desc, id desc"
    _check_company_auto = True

    employee_id = fields.Many2one(
        "hr.employee", required=True, ondelete="restrict", index=True, check_company=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    batch_id = fields.Many2one(
        "l10n_vn.payroll.advance.batch",
        string="Batch",
        ondelete="restrict",
        index=True,
        check_company=True,
        copy=False,
    )
    date = fields.Date(
        string="Requested Payment Date", required=True, default=fields.Date.context_today
    )
    amount = fields.Monetary(required=True)
    reason = fields.Char(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        readonly=True,
        copy=False,
        index=True,
    )
    eligible = fields.Boolean(string="Eligible", compute="_compute_limit", compute_sudo=True)
    days_worked = fields.Float(
        string="Days Worked to Date",
        digits=(16, 4),
        compute="_compute_limit",
        compute_sudo=True,
    )
    earned_amount = fields.Monetary(
        string="Earned to Date", compute="_compute_limit", compute_sudo=True
    )
    monthly_amount = fields.Monetary(
        string="Monthly Amount", compute="_compute_limit", compute_sudo=True
    )
    limit_left = fields.Monetary(
        string="Limit Left", compute="_compute_limit", compute_sudo=True
    )
    over_limit = fields.Boolean(
        string="Above Limit", compute="_compute_limit", compute_sudo=True
    )
    limit_note = fields.Char(string="Limit Note", copy=False)
    approved_by = fields.Many2one("res.users", readonly=True, copy=False)
    approved_at = fields.Datetime(readonly=True, copy=False)
    limit_at_approval = fields.Monetary(string="Limit at Approval", readonly=True, copy=False)
    paid_date = fields.Date(string="Payment Date", readonly=True, copy=False)
    settlement_ids = fields.One2many(
        "l10n_vn.payroll.advance.settlement", "advance_id", readonly=True
    )
    payment_line_ids = fields.One2many(
        "l10n_vn.payroll.payment.line", "advance_id", readonly=True
    )
    payment_id = fields.Many2one(
        "l10n_vn.payroll.payment", string="Payment List", compute="_compute_payment_id"
    )
    settled_amount = fields.Monetary(string="Settled", compute="_compute_settled", store=True)
    balance = fields.Monetary(compute="_compute_settled", store=True)

    _sql_constraints = [
        ("amount_positive", "CHECK(amount > 0)", "An advance has an amount above 0."),
    ]

    @api.depends("employee_id", "date")
    def _compute_display_name(self):
        for advance in self:
            advance.display_name = self.env._(
                "%(employee)s, %(date)s",
                employee=advance.employee_id.name or "",
                date=format_date(self.env, advance.date) if advance.date else "",
            )

    @api.depends("employee_id", "company_id", "date", "amount")
    def _compute_limit(self):
        for advance in self:
            values = dict.fromkeys(
                ("monthly_amount", "days_worked", "earned_amount", "limit_left"), 0.0
            )
            values.update(eligible=False, over_limit=False)
            employee, company, date = advance.employee_id, advance.company_id, advance.date
            if employee and company and date:
                try:
                    monthly = self._l10n_vn_monthly_amount_of(employee, company, date)
                    days = self._l10n_vn_days_worked_of(employee, date)
                    earned = self._l10n_vn_earned_from(monthly, days, company, date)
                    left = advance._l10n_vn_left_from(earned)
                    eligible = self._l10n_vn_eligible_of(employee, company, date)
                    values.update(
                        monthly_amount=monthly,
                        days_worked=days,
                        earned_amount=earned,
                        limit_left=left,
                        eligible=eligible,
                        over_limit=eligible
                        and advance.amount > left
                        and advance._l10n_vn_limit_level() != "off",
                    )
                except UserError:
                    pass  # a missing parameter or scale cell: the figures stay 0
            advance.update(values)

    @api.depends("payment_line_ids.payment_id")
    def _compute_payment_id(self):
        for advance in self:
            advance.payment_id = advance.payment_line_ids[:1].payment_id

    @api.depends("amount", "settlement_ids.amount", "settlement_ids.payslip_id.state")
    def _compute_settled(self):
        for advance in self:
            advance.settled_amount = sum(
                advance.settlement_ids.filtered(lambda s: s.payslip_id.state == "done").mapped(
                    "amount"
                )
            )
            advance.balance = advance.amount - advance.settled_amount

    # ------------------------------------------------------------------ CRUD (D10, D11)
    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(CONTROLLED & set(vals) for vals in vals_list):
            raise AccessError(self.env._("An advance's status changes through its buttons."))
        Batch = self.env["l10n_vn.payroll.advance.batch"]
        for vals in vals_list:
            if vals.get("batch_id"):
                batch = Batch.browse(vals["batch_id"])
                vals.setdefault("company_id", batch.company_id.id)
                vals.setdefault("date", batch.date)
                vals.setdefault("reason", batch.reason)
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su:
            if CONTROLLED & set(vals):
                raise AccessError(self.env._("An advance's status changes through its buttons."))
            if FROZEN & set(vals) and any(advance.state != "draft" for advance in self):
                raise UserError(self.env._("Only a draft advance can change."))
        return super().write(vals)

    def unlink(self):
        if any(advance.state != "draft" for advance in self):
            raise UserError(self.env._("Only a draft advance can be deleted."))
        return super().unlink()

    # ------------------------------------------------------------------ the limit (D2, D3)
    def _l10n_vn_require(self, *groups):
        if self.env.su:
            return
        if not any(self.env.user.has_group(group) for group in groups):
            raise AccessError(self.env._("Your payroll role does not allow this step."))

    @api.model
    def _l10n_vn_monthly_amount_of(self, employee, company, date):
        """Salary-section pay lines at 100% of the main contract for the month of date."""
        first = date + relativedelta(day=1)
        last = date + relativedelta(day=31)
        contract = employee.sudo()._l10n_vn_period_contracts(first, last)[-1:]
        if not contract:
            return 0.0
        on = min(last, contract.date_end or last)
        lines = contract.l10n_vn_line_ids._l10n_vn_in_force(on).filtered(
            lambda line: line.component_id.active
            and line.component_id.section == "salary"
            and line.component_id.proration != "per_day"
        )
        return company.currency_id.round(sum(float(line._l10n_vn_amount_on(on)) for line in lines))

    def _l10n_vn_monthly_amount(self):
        self.ensure_one()
        return self._l10n_vn_monthly_amount_of(self.employee_id, self.company_id, self.date)

    @api.model
    def _l10n_vn_param(self, code, company, date):
        return self.env["base.time.parameter"].sudo()._strict_get(code, date, company=company)

    @api.model
    def _l10n_vn_days_worked_of(self, employee, date):
        """Days worked from the 1st of the month to the day before date (D14)."""
        first = date + relativedelta(day=1)
        cutoff = date - relativedelta(days=1)
        if cutoff < first:
            return 0.0
        figures = employee.sudo()._attendance_days(first, cutoff)[employee.id]
        return sum(day.get("days_worked") or 0.0 for day in figures.values())

    @api.model
    def _l10n_vn_earned_from(self, monthly, days, company, date):
        if not days:
            return 0.0
        std = float(self._l10n_vn_param("vn.policy.std_days", company, date))
        return company.currency_id.round(monthly * days / std) if std else 0.0

    @api.model
    def _l10n_vn_earned_of(self, employee, company, date):
        """Pay earned to date (D14)."""
        return self._l10n_vn_earned_from(
            self._l10n_vn_monthly_amount_of(employee, company, date),
            self._l10n_vn_days_worked_of(employee, date),
            company,
            date,
        )

    @api.model
    def _l10n_vn_pay_groups(self, company, date):
        """The pay groups eligible for advances (D16)."""
        value = self._l10n_vn_param("vn.policy.advance_pay_groups", company, date)
        return {group.strip() for group in str(value or "").split(",") if group.strip()}

    @api.model
    def _l10n_vn_month_contract(self, employee, date):
        """The employee's main contract for the month of date (engine D31)."""
        first = date + relativedelta(day=1)
        last = date + relativedelta(day=31)
        return employee.sudo()._l10n_vn_period_contracts(first, last)[-1:]

    @api.model
    def _l10n_vn_eligible_of(self, employee, company, date):
        """The pay group of the month's contract is in the eligible list (D16, D18)."""
        group = self._l10n_vn_month_contract(employee, date).l10n_vn_pay_group
        return bool(group) and group in self._l10n_vn_pay_groups(company, date)

    def _l10n_vn_limit_left(self):
        """The share of pay earned to date less the month's other advances, at least 0."""
        self.ensure_one()
        return self._l10n_vn_left_from(
            self._l10n_vn_earned_of(self.employee_id, self.company_id, self.date)
        )

    def _l10n_vn_left_from(self, earned):
        self.ensure_one()
        share = self._l10n_vn_param("vn.policy.advance_max_share", self.company_id, self.date)
        others = self.sudo().search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("company_id", "=", self.company_id.id),
                ("date", ">=", self.date + relativedelta(day=1)),
                ("date", "<=", self.date + relativedelta(day=31)),
                ("state", "in", ("approved", "paid")),
                ("id", "not in", self._origin.ids),
            ]
        )
        left = float(share) * earned - sum(others.mapped("amount"))
        return max(0.0, self.company_id.currency_id.round(left))

    def _l10n_vn_limit_level(self):
        """The level of the check advance_limit on the advance's date (D3, D13)."""
        self.ensure_one()
        check = self.env.ref("l10n_vn_payroll.check_advance_limit", raise_if_not_found=False)
        check = check and check.sudo()
        if not check or not check.active:
            return "off"
        # the engine reads date_to and company_id of what it is given
        return check._l10n_vn_level(
            SimpleNamespace(date_to=self.date, company_id=self.company_id), False
        )

    def _l10n_vn_open_amounts(self, payslip):
        """{id: amount less settlements on other payslips that are not cancelled} (D7)."""
        return {
            advance.id: advance.amount
            - sum(
                advance.settlement_ids.filtered(
                    lambda s: s.payslip_id != payslip and s.payslip_id.state != "cancel"
                ).mapped("amount")
            )
            for advance in self
        }

    # ------------------------------------------------------------------ steps (D1)
    def action_approve(self):
        self._l10n_vn_require(REVIEWER)
        if any(advance.state != "draft" for advance in self):
            raise UserError(self.env._("Only a draft advance is approved."))
        not_eligible = self.sudo().filtered(
            lambda a: not self._l10n_vn_eligible_of(a.employee_id, a.company_id, a.date)
        )
        if not_eligible:
            raise UserError(
                self.env._(
                    "Not in a pay group eligible for advances: %(employees)s.",
                    employees=_employee_names(not_eligible),
                )
            )
        need_note = refused = self.browse()
        now = fields.Datetime.now()
        for advance in self.sudo().sorted(lambda a: (a.date, a.id)):
            left = advance._l10n_vn_limit_left()
            level = advance._l10n_vn_limit_level()
            if level != "off" and advance.amount > left:
                if level == "error":
                    refused |= advance
                    continue
                if level == "warning" and not advance.limit_note:
                    need_note |= advance
                    continue
            advance.write(
                {
                    "state": "approved",
                    "approved_by": self.env.uid,
                    "approved_at": now,
                    "limit_at_approval": left,
                }
            )
        messages = []
        if need_note:
            messages.append(
                self.env._(
                    "Above the limit, a note is needed: %(employees)s.",
                    employees=_employee_names(need_note),
                )
            )
        if refused:
            messages.append(
                self.env._("Above the limit: %(employees)s.", employees=_employee_names(refused))
            )
        if messages:
            raise UserError("\n".join(messages))
        return True

    def action_create_payment(self, name=None):
        """A payment list of the approved advances not yet on one (step 2, D21)."""
        self._l10n_vn_require(OFFICER)
        name = name or self.env._(
            "Advances %(date)s", date=fields.Date.to_string(fields.Date.context_today(self))
        )
        payment = self.env["l10n_vn.payroll.payment"]._l10n_vn_from_advances(self, name)
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_vn.payroll.payment",
            "res_id": payment.id,
            "view_mode": "form",
        }

    def _l10n_vn_mark_paid(self, paid_date):
        self._l10n_vn_require(OFFICER)
        if any(advance.state != "approved" for advance in self):
            raise UserError(self.env._("Only an approved advance is marked as paid."))
        self.sudo().write({"state": "paid", "paid_date": paid_date})
        return True

    def action_cancel(self):
        self._l10n_vn_require(OFFICER)
        for advance in self:
            if advance.state == "cancelled":
                raise UserError(self.env._("This advance is already cancelled."))
            if advance.state == "paid":
                self._l10n_vn_require(REVIEWER)
                if advance.sudo().settlement_ids.filtered(lambda s: s.payslip_id.state == "done"):
                    raise UserError(self.env._("This advance is already settled on a payslip."))
        # an approved advance leaves its payment list (D26)
        self.sudo().payment_line_ids.filtered(lambda l: l.state == "to_pay").unlink()
        self.sudo().write({"state": "cancelled"})
        return True


class L10nVnPayrollAdvanceSettlement(models.Model):
    _name = "l10n_vn.payroll.advance.settlement"
    _description = "Salary Advance Settlement"
    _order = "advance_id, id"

    advance_id = fields.Many2one(
        "l10n_vn.payroll.advance", required=True, ondelete="restrict", index=True
    )
    payslip_id = fields.Many2one("hr.payslip", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="advance_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    amount = fields.Monetary()
    payslip_state = fields.Selection(related="payslip_id.state", string="Payslip status")
