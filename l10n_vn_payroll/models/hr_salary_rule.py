# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

RULE_TYPE = "l10n_vn_component"


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    amount_select = fields.Selection(
        selection_add=[(RULE_TYPE, "Pay Component")],
        ondelete={RULE_TYPE: "set default"},
    )
    condition_select = fields.Selection(
        selection_add=[(RULE_TYPE, "Pay Component")],
        ondelete={RULE_TYPE: "set default"},
    )
    l10n_vn_component_id = fields.Many2one(
        "l10n_vn.payroll.component", string="Pay Component", ondelete="restrict"
    )

    @api.constrains("amount_select", "condition_select", "l10n_vn_component_id")
    def _check_l10n_vn_component(self):
        if self._name != "hr.salary.rule":
            # payslip lines inherit the rule and this constraint
            return
        for rule in self:
            uses = RULE_TYPE in (rule.amount_select, rule.condition_select)
            if uses and not rule.l10n_vn_component_id:
                raise ValidationError(
                    self.env._("Rule %(rule)s needs its pay component.", rule=rule.name)
                )

    def _satisfy_condition_l10n_vn_component(self, localdict):
        self.ensure_one()
        return bool(localdict["payslip"]._l10n_vn_context_lines(self.l10n_vn_component_id))

    def _compute_rule_l10n_vn_component(self, localdict):
        """The component's context lines; the payslip files one line per part (D43)."""
        self.ensure_one()
        parts = localdict["payslip"]._l10n_vn_context_lines(self.l10n_vn_component_id)
        return {
            "name": parts[0]["name"] if parts else self.name,
            "quantity": 1.0,
            "rate": 100.0,
            "amount": float(sum(part["amount"] for part in parts)),
            "l10n_vn_parts": [
                {
                    "name": part["name"],
                    "amount": float(part["amount"]),
                    "l10n_vn_days": part["days"] or False,
                    "l10n_vn_hours": part["hours"] or False,
                    "l10n_vn_factor": part["factor"] or False,
                    "l10n_vn_unit_amount": part["unit_amount"] or False,
                    "l10n_vn_date_from": part["date_from"] or False,
                    "l10n_vn_date_to": part["date_to"] or False,
                    "l10n_vn_attainment": part["attainment"] or False,
                    "l10n_vn_period_ref": part["period_ref"] or False,
                }
                for part in parts
            ],
        }
