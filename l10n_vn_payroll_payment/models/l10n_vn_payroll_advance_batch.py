# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

from .l10n_vn_payroll_advance import OFFICER


class L10nVnPayrollAdvanceBatch(models.Model):
    _name = "l10n_vn.payroll.advance.batch"
    _description = "Salary Advance Batch"
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        required=True, compute="_compute_name", store=True, readonly=False, precompute=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    date = fields.Date(
        string="Requested Payment Date", required=True, default=fields.Date.context_today
    )
    reason = fields.Char(required=True)
    pay_group = fields.Selection(selection="_l10n_vn_pay_groups", string="Pay Group")
    department_ids = fields.Many2many(
        "hr.department", "l10n_vn_advance_batch_department_rel", string="Departments"
    )
    amount_mode = fields.Selection(
        [("fixed", "Fixed Amount"), ("share", "Share of Monthly Amount")],
        required=True,
        default="fixed",
    )
    fixed_amount = fields.Monetary()
    share = fields.Float(digits=(16, 4))
    round_to = fields.Integer(string="Round Down To", default=1000)
    advance_ids = fields.One2many("l10n_vn.payroll.advance", "batch_id", string="Advances")
    amount_total = fields.Monetary(compute="_compute_totals", store=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        compute="_compute_totals",
        store=True,
    )

    @api.model
    def _l10n_vn_pay_groups(self):
        return self.env["hr.contract"]._fields["l10n_vn_pay_group"].selection

    @api.depends("date")
    def _compute_name(self):
        for batch in self:
            batch.name = batch.name or (
                self.env._("Advances %(date)s", date=fields.Date.to_string(batch.date))
                if batch.date
                else False
            )

    @api.depends("advance_ids.amount", "advance_ids.state")
    def _compute_totals(self):
        for batch in self:
            states = set(batch.advance_ids.mapped("state"))
            batch.amount_total = sum(
                batch.advance_ids.filtered(lambda a: a.state != "cancelled").mapped("amount")
            )
            if not states or "draft" in states:
                batch.state = "draft"
            elif "approved" in states:
                batch.state = "approved"
            elif "paid" in states:
                batch.state = "paid"
            else:
                batch.state = "cancelled"

    def unlink(self):
        if any(advance.state != "draft" for advance in self.advance_ids):
            raise UserError(self.env._("Only a batch of draft advances can be deleted."))
        self.advance_ids.unlink()
        return super().unlink()

    # ------------------------------------------------------------------ generating (D9)
    def _l10n_vn_employees(self):
        """Active employees of the selection with an eligible main contract for the month."""
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id)]
        if self.department_ids:
            domain.append(("department_id", "child_of", self.department_ids.ids))
        first = self.date + relativedelta(day=1)
        last = self.date + relativedelta(day=31)
        # pay groups eligible for advances (D16); raises without the parameter
        groups = self.env["l10n_vn.payroll.advance"]._l10n_vn_pay_groups(
            self.company_id, self.date
        )

        def eligible(employee):
            # the pay group of the month's contract (D18)
            contract = employee._l10n_vn_period_contracts(first, last)[-1:]
            return bool(
                contract.l10n_vn_pay_group in groups
                and (not self.pay_group or contract.l10n_vn_pay_group == self.pay_group)
                and contract
                and contract.struct_id.l10n_vn_payroll
                and (not contract.date_end or contract.date_end >= self.date)
            )

        return self.env["hr.employee"].sudo().search(domain).filtered(eligible)

    def _l10n_vn_amount_for(self, employee):
        self.ensure_one()
        if self.amount_mode == "fixed":
            return self.fixed_amount
        earned = self.env["l10n_vn.payroll.advance"]._l10n_vn_earned_of(
            employee, self.company_id, self.date
        )
        amount = self.currency_id.round(self.share * earned)
        step = self.round_to if self.round_to > 0 else 1
        return int(amount // step) * step

    def action_generate(self):
        self.env["l10n_vn.payroll.advance"]._l10n_vn_require(OFFICER)
        Advance = self.env["l10n_vn.payroll.advance"]
        for batch in self:
            if batch.state != "draft":
                raise UserError(self.env._("Only a draft batch generates advances."))
            if (batch.amount_mode == "fixed" and batch.fixed_amount <= 0) or (
                batch.amount_mode == "share" and batch.share <= 0
            ):
                raise UserError(self.env._("Enter the amount or share of the batch."))
            present = batch.advance_ids.employee_id
            vals_list = []
            for employee in batch._l10n_vn_employees() - present.sudo():
                amount = batch._l10n_vn_amount_for(employee)
                if amount > 0:
                    vals_list.append(
                        {
                            "batch_id": batch.id,
                            "employee_id": employee.id,
                            "company_id": batch.company_id.id,
                            "date": batch.date,
                            "reason": batch.reason,
                            "amount": amount,
                        }
                    )
            Advance.create(vals_list)
        return True

    # ------------------------------------------------------------------ steps on the lines
    def action_approve(self):
        drafts = self.advance_ids.filtered(lambda a: a.state == "draft")
        return drafts.action_approve()

    def action_create_payment(self):
        """A payment list of the batch's approved advances (step 2, D21)."""
        self.ensure_one()
        return self.advance_ids.action_create_payment(name=self.name)

    def action_cancel(self):
        Advance = self.env["l10n_vn.payroll.advance"]
        Advance._l10n_vn_require(OFFICER)
        open_ones = self.advance_ids.filtered(lambda a: a.state in ("draft", "approved"))
        if open_ones:
            open_ones.action_cancel()
        return True
