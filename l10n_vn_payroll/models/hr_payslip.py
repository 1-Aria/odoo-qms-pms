# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from .hr_salary_rule import RULE_TYPE
from .pay_context import PayContext, _dec, _round


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    l10n_vn_input_id = fields.Many2one(
        "l10n_vn.payroll.input",
        string="Monthly Input",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )
    l10n_vn_context = fields.Json(string="Pay Context", readonly=True, copy=False)

    def _l10n_vn_is_vn(self):
        self.ensure_one()
        return bool(self.struct_id.sudo().l10n_vn_payroll)

    # ------------------------------------------------------------------ contract (D30, D31)
    def get_payslip_vals(
        self, date_from, date_to, employee_id=False, contract_id=False, struct_id=False
    ):
        if employee_id and date_from and date_to:
            employee = self.env["hr.employee"].browse(employee_id)
            main = employee._l10n_vn_period_contracts(
                fields.Date.to_date(date_from), fields.Date.to_date(date_to)
            )[-1:]
            if main:
                structure = (
                    self.env["hr.payroll.structure"].sudo().browse(struct_id[0])
                    if struct_id
                    else main.struct_id
                )
                if structure.l10n_vn_payroll:
                    # OCA keeps the given contract under the context key "contract"
                    return super(HrPayslip, self.with_context(contract=True)).get_payslip_vals(
                        date_from, date_to, employee_id, contract_id=main.id, struct_id=struct_id
                    )
        return super().get_payslip_vals(
            date_from, date_to, employee_id, contract_id=contract_id, struct_id=struct_id
        )

    def _get_employee_contracts(self):
        contracts = self.env["hr.contract"]
        for payslip in self:
            if (
                not payslip.contract_id
                and payslip.employee_id
                and payslip.date_from
                and payslip.date_to
            ):
                main = payslip.employee_id._l10n_vn_period_contracts(
                    payslip.date_from, payslip.date_to
                )[-1:]
                if main.struct_id.l10n_vn_payroll:
                    contracts |= main.with_env(self.env)
                    continue
            contracts |= super(HrPayslip, payslip)._get_employee_contracts()
        return contracts

    # ------------------------------------------------------------------ worked days
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        contract = contracts[:1]
        if contract and contract.sudo().struct_id.l10n_vn_payroll:
            inp = self._l10n_vn_find_input(
                contract.employee_id, contract.company_id, fields.Date.to_date(date_from)
            )
            return self._l10n_vn_worked_day_vals(inp, contract) if inp else []
        return super().get_worked_day_lines(contracts, date_from, date_to)

    @api.model
    def _l10n_vn_find_input(self, employee, company, date_from):
        return (
            self.env["l10n_vn.payroll.input"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", employee.id),
                    ("period_id.company_id", "=", company.id),
                    ("period_id.date_from", "=", date_from),
                ],
                limit=1,
            )
        )

    @api.model
    def _l10n_vn_worked_day_vals(self, inp, contract):
        vals = [
            {
                "name": self.env._("Paid days"),
                "code": "PAID",
                "sequence": 1,
                "number_of_days": inp.paid_days,
                "contract_id": contract.id,
            },
            {
                "name": self.env._("Days worked"),
                "code": "WORKED",
                "sequence": 2,
                "number_of_days": inp.days_worked,
                "contract_id": contract.id,
            },
            {
                "name": self.env._("Unpaid days"),
                "code": "UNPAID",
                "sequence": 3,
                "number_of_days": inp.unpaid_days,
                "contract_id": contract.id,
            },
        ]
        for name, days in sorted((inp.leave_days_json or {}).items()):
            vals.append(
                {
                    "name": name,
                    "code": "LEAVE",
                    "sequence": 10,
                    "number_of_days": days,
                    "contract_id": contract.id,
                }
            )
        return vals

    # ------------------------------------------------------------------ calculation (D42)
    def compute_sheet(self):
        self.filtered(lambda payslip: payslip._l10n_vn_is_vn())._l10n_vn_prepare()
        return super().compute_sheet()

    def _l10n_vn_prepare(self):
        if not self:
            return
        for payslip in self:
            if payslip.date_from.day != 1 or payslip.date_to != payslip.date_from + relativedelta(
                day=31
            ):
                raise UserError(
                    self.env._(
                        "A Vietnamese payslip covers one calendar month (%(employee)s).",
                        employee=payslip.employee_id.name,
                    )
                )
        inputs = (
            self.env["l10n_vn.payroll.input"]
            .sudo()
            .search(
                [
                    ("employee_id", "in", self.employee_id.ids),
                    ("period_id.date_from", "in", list(set(self.mapped("date_from")))),
                ]
            )
        )
        by_key = {(i.employee_id.id, i.company_id.id, i.period_id.date_from): i for i in inputs}
        builder = PayContext(self.env(su=True))
        for payslip in self:
            employee = payslip.employee_id
            names = {"employee": employee.name, "month": f"{payslip.date_from:%m/%Y}"}
            main = employee._l10n_vn_period_contracts(payslip.date_from, payslip.date_to)[-1:]
            if not main:
                raise UserError(self.env._("%(employee)s has no contract in %(month)s.", **names))
            inp = by_key.get((employee.id, payslip.company_id.id, payslip.date_from))
            if not inp:
                raise UserError(
                    self.env._("%(employee)s has no monthly input for %(month)s.", **names)
                )
            context = builder.build(payslip.sudo(), main, inp)
            payslip.write(
                {
                    "contract_id": main.id,
                    "l10n_vn_input_id": inp.id,
                    "l10n_vn_context": context,
                    "worked_days_line_ids": [Command.clear()]
                    + [Command.create(v) for v in self._l10n_vn_worked_day_vals(inp, main)],
                }
            )
            payslip._l10n_vn_check_rules(context, names)

    def _l10n_vn_check_rules(self, context, names):
        """Every component with context lines needs a rule that shows them (D44)."""
        self.ensure_one()
        rules = self._get_salary_rules().filtered(lambda rule: rule.amount_select == RULE_TYPE)
        covered = set(rules.l10n_vn_component_id.ids)
        for line in context["lines"]:
            if line["component_id"] not in covered:
                raise UserError(
                    self.env._(
                        "Component %(code)s has amounts for %(employee)s but no rule in "
                        "structure %(structure)s.",
                        code=line["code"],
                        structure=self.struct_id.name,
                        **names,
                    )
                )

    def get_payroll_dict(self, contracts):
        res = super().get_payroll_dict(contracts)
        if self._l10n_vn_is_vn():
            res["vn"] = self.l10n_vn_context or {}
        return res

    def _l10n_vn_context_lines(self, component):
        self.ensure_one()
        return [
            line
            for line in (self.l10n_vn_context or {}).get("lines", [])
            if line["component_id"] == component.id
        ]

    # ------------------------------------------------------------------ exact lines (D43)
    def _get_lines_dict(self, rule, localdict, lines_dict, key, values, previous_amount):
        parts = values.pop("l10n_vn_parts", None)
        if rule.amount_select != RULE_TYPE and self._l10n_vn_is_vn():
            total = _dec(values["quantity"]) * _dec(values["rate"]) * _dec(values["amount"]) / 100
            values.update(quantity=1.0, rate=100.0, amount=float(_round(total)))
        localdict, lines_dict = super()._get_lines_dict(
            rule, localdict, lines_dict, key, values, previous_amount
        )
        if rule.amount_select == RULE_TYPE:
            line = lines_dict[key]
            line["l10n_vn_component_id"] = rule.l10n_vn_component_id.id
            for n, part in enumerate(parts or []):
                part_vals = dict(part, quantity=1.0, rate=100.0, total=part["amount"])
                if n == 0:
                    line.update(part_vals)
                else:
                    lines_dict[f"{key}-{n}"] = dict(line, **part_vals)
        return localdict, lines_dict
