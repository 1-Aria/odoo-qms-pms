# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class L10nVnPayrollDamage(models.Model):
    _name = "l10n_vn.payroll.damage"
    _description = "Damage Compensation Decision"
    _order = "employee_id, decision_date, id"
    _check_company_auto = True

    employee_id = fields.Many2one(
        "hr.employee", required=True, ondelete="restrict", index=True, check_company=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    decision_ref = fields.Char(string="Decision", required=True)
    decision_date = fields.Date(required=True)
    reason = fields.Char(required=True)
    amount = fields.Monetary(string="Amount decided", required=True)
    allocation_ids = fields.One2many(
        "l10n_vn.payroll.damage.allocation", "damage_id", readonly=True
    )
    deducted = fields.Monetary(compute="_compute_deducted", store=True)
    balance = fields.Monetary(compute="_compute_deducted", store=True)
    state = fields.Selection(
        [("open", "Open"), ("done", "Settled")], compute="_compute_deducted", store=True
    )
    note = fields.Text()

    _sql_constraints = [
        ("amount_positive", "CHECK(amount > 0)", "A damage decision has an amount above 0."),
    ]

    @api.depends("amount", "allocation_ids.amount", "allocation_ids.payslip_id.state")
    def _compute_deducted(self):
        for damage in self:
            damage.deducted = sum(
                damage.allocation_ids.filtered(lambda a: a.payslip_id.state == "done").mapped(
                    "amount"
                )
            )
            damage.balance = damage.amount - damage.deducted
            damage.state = "open" if damage.balance > 0 else "done"

    def unlink(self):
        if any(damage.deducted > 0 for damage in self):
            raise UserError(
                self.env._("A damage decision already deducted on a payslip cannot be deleted.")
            )
        return super().unlink()

    def _l10n_vn_available(self, payslip):
        """What each decision can still give: its amount less allocations elsewhere (D56)."""
        return {
            damage.id: damage.amount
            - sum(
                damage.allocation_ids.filtered(
                    lambda a: a.payslip_id != payslip and a.payslip_id.state != "cancel"
                ).mapped("amount")
            )
            for damage in self
        }


class L10nVnPayrollDamageAllocation(models.Model):
    _name = "l10n_vn.payroll.damage.allocation"
    _description = "Damage Compensation Allocation"
    _order = "damage_id, id"

    damage_id = fields.Many2one(
        "l10n_vn.payroll.damage", required=True, ondelete="restrict", index=True
    )
    payslip_id = fields.Many2one("hr.payslip", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="damage_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    amount = fields.Monetary()
    payslip_state = fields.Selection(related="payslip_id.state", string="Payslip status")
