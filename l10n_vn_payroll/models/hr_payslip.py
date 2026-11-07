# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from .hr_payslip_run import LOCKED_STATES
from .hr_salary_rule import RULE_TYPE
from .pay_context import IntegrityStop, PayContext, _dec, _round


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
    l10n_vn_check_result_ids = fields.One2many(
        "l10n_vn.payroll.check.result", "payslip_id", string="Checks", readonly=True
    )
    l10n_vn_check_level = fields.Selection(
        [("error", "Error"), ("warning", "Warning"), ("note", "Note")],
        string="Check Level",
        compute="_compute_l10n_vn_check_level",
        store=True,
    )
    # ------------------------------------------------------------------ totals (D79, D80)
    l10n_vn_currency_id = fields.Many2one(related="company_id.currency_id")
    l10n_vn_paid_days = fields.Float(string="Paid Days", digits=(16, 4), readonly=True, copy=False)
    l10n_vn_days_worked = fields.Float(string="Days Worked", digits=(16, 4), readonly=True, copy=False)
    l10n_vn_unpaid_days = fields.Float(string="Unpaid Days", digits=(16, 4), readonly=True, copy=False)
    l10n_vn_ot_hours = fields.Float(string="OT Hours", digits=(16, 4), readonly=True, copy=False)
    l10n_vn_ot_wd_hours = fields.Float(string="OT Workday", digits=(16, 4), readonly=True, copy=False)
    l10n_vn_ot_rd_hours = fields.Float(string="OT Rest Day", digits=(16, 4), readonly=True, copy=False)
    l10n_vn_ot_hol_hours = fields.Float(string="OT Holiday", digits=(16, 4), readonly=True, copy=False)
    l10n_vn_salary_pay = fields.Monetary(string="Salary", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_ot_pay = fields.Monetary(string="OT Pay", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_bonus_pay = fields.Monetary(string="Bonus", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_other_pay = fields.Monetary(string="Other Pay", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_gross = fields.Monetary(string="Gross", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_employee_insurance = fields.Monetary(string="Employee Insurance", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_dues = fields.Monetary(string="Union Dues", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_pit = fields.Monetary(string="PIT", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_damage = fields.Monetary(string="Damage Compensation", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_other_deductions = fields.Monetary(string="Other Deductions", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_net = fields.Monetary(string="Net Pay", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_advance = fields.Monetary(string="Advance Settled", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_to_pay = fields.Monetary(string="To Pay", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_employer_cost = fields.Monetary(string="Employer Cost", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_si_base = fields.Monetary(string="SI Base", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_taxable = fields.Monetary(string="Taxable Income", currency_field="l10n_vn_currency_id", readonly=True, copy=False)
    l10n_vn_damage_allocation_ids = fields.One2many(
        "l10n_vn.payroll.damage.allocation",
        "payslip_id",
        string="Damage Deductions",
        readonly=True,
    )

    @api.depends("l10n_vn_check_result_ids.level")
    def _compute_l10n_vn_check_level(self):
        for payslip in self:
            levels = set(payslip.l10n_vn_check_result_ids.mapped("level"))
            payslip.l10n_vn_check_level = next(
                (level for level in ("error", "warning", "note") if level in levels), False
            )

    # ------------------------------------------------------------------ the lock (D76)
    def _l10n_vn_locked(self):
        self.ensure_one()
        run = self.sudo().payslip_run_id
        return bool(run.l10n_vn_period_id) and run.state in LOCKED_STATES

    def _l10n_vn_raise_if_locked(self):
        """Approved payslips do not change; the superuser (the approval itself) excepted."""
        if self.env.su:
            return
        for payslip in self.sudo():
            if payslip._l10n_vn_locked():
                raise UserError(
                    self.env._(
                        "Payslip %(number)s belongs to an approved run and cannot change; "
                        "correct it in a later month.",
                        number=payslip.number or payslip.name,
                    )
                )

    def write(self, vals):
        self._l10n_vn_raise_if_locked()
        return super().write(vals)

    def unlink(self):
        self._l10n_vn_raise_if_locked()
        return super().unlink()

    @api.model
    def _l10n_vn_totals(self, context):
        """The payslip's totals from its snapshot (D80); empty without one."""
        sections = {"salary": "l10n_vn_salary_pay", "ot": "l10n_vn_ot_pay",
                    "bonus": "l10n_vn_bonus_pay", "other": "l10n_vn_other_pay"}
        names = [
            "l10n_vn_paid_days", "l10n_vn_days_worked", "l10n_vn_unpaid_days", "l10n_vn_ot_hours",
            "l10n_vn_ot_wd_hours", "l10n_vn_ot_rd_hours", "l10n_vn_ot_hol_hours",
            *sections.values(), "l10n_vn_gross", "l10n_vn_employee_insurance", "l10n_vn_dues",
            "l10n_vn_pit", "l10n_vn_damage", "l10n_vn_other_deductions", "l10n_vn_net",
            "l10n_vn_advance", "l10n_vn_to_pay", "l10n_vn_employer_cost", "l10n_vn_si_base",
            "l10n_vn_taxable",
        ]
        if not context:
            return dict.fromkeys(names, 0)
        values = dict.fromkeys(names, 0)
        inp = context.get("input", {})
        ot = inp.get("ot_hours_json") or {}
        values.update(
            l10n_vn_paid_days=inp.get("paid_days") or 0,
            l10n_vn_days_worked=inp.get("days_worked") or 0,
            l10n_vn_unpaid_days=inp.get("unpaid_days") or 0,
            l10n_vn_ot_hours=sum(ot.values()),
            l10n_vn_ot_wd_hours=ot.get("WD", 0),
            l10n_vn_ot_rd_hours=ot.get("RD", 0),
            l10n_vn_ot_hol_hours=ot.get("HOL", 0),
        )
        lines = context.get("lines", [])
        components = self.env["l10n_vn.payroll.component"].sudo().browse(
            {line["component_id"] for line in lines}
        )
        section_of = {c.id: c.section for c in components}
        for line in lines:
            if line["kind"] == "earning" and section_of.get(line["component_id"]) in sections:
                values[sections[section_of[line["component_id"]]]] += line["amount"]
            elif line["kind"] == "employer":
                values["l10n_vn_employer_cost"] += line["amount"]
        values.update(
            l10n_vn_gross=context.get("gross", 0),
            l10n_vn_employee_insurance=context.get("employee_insurance", 0),
            l10n_vn_dues=context.get("dues", 0),
            l10n_vn_pit=(context.get("pit") or {}).get("pit", 0),
            l10n_vn_damage=(context.get("damage") or {}).get("total", 0),
            l10n_vn_other_deductions=-sum(
                line["amount"] for line in lines
                if line["kind"] == "deduction" and line.get("input_line_id")
            ),
            l10n_vn_net=context.get("net", 0),
            l10n_vn_advance=context.get("settled", 0),
            l10n_vn_to_pay=context.get("to_pay", 0),
            l10n_vn_si_base=(context.get("contributions") or {}).get("si_capped") or 0,
            l10n_vn_taxable=(context.get("pit") or {}).get("taxable") or 0,
        )
        return values

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
        self._l10n_vn_raise_if_locked()
        # recalculating after review sends the run back (D75)
        self.sudo().payslip_run_id.filtered(
            lambda run: run.l10n_vn_period_id and run.state == "reviewed"
        ).write({"state": "calculated", "l10n_vn_reviewed_by": False, "l10n_vn_reviewed_at": False})
        vn = self.filtered(lambda payslip: payslip._l10n_vn_is_vn())
        stopped = vn._l10n_vn_prepare()
        result = super(HrPayslip, self - stopped).compute_sheet()
        (vn - stopped)._l10n_vn_run_checks()
        return result

    def _l10n_vn_prepare(self):
        """Builds each payslip's context; returns the payslips stopped (D62)."""
        stopped = self.browse()
        if not self:
            return stopped
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
            payslip.sudo().l10n_vn_check_result_ids.unlink()
            try:
                payslip._l10n_vn_prepare_one(builder, by_key)
            except IntegrityStop as stop:
                payslip._l10n_vn_record_stop(stop.code, stop.args[0])
                stopped |= payslip
            except UserError as error:
                # a parameter that cannot be read, for instance
                payslip._l10n_vn_record_stop("calculation", error.args[0])
                stopped |= payslip
        return stopped

    def _l10n_vn_prepare_one(self, builder, by_key):
        self.ensure_one()
        payslip = self
        employee = payslip.employee_id
        names = {"employee": employee.name, "month": f"{payslip.date_from:%m/%Y}"}
        if payslip.date_from.day != 1 or payslip.date_to != payslip.date_from + relativedelta(
            day=31
        ):
            raise IntegrityStop(
                "calculation",
                self.env._(
                    "A Vietnamese payslip covers one calendar month (%(employee)s).", **names
                ),
            )
        main = employee._l10n_vn_period_contracts(payslip.date_from, payslip.date_to)[-1:]
        if not main:
            raise IntegrityStop(
                "calculation", self.env._("%(employee)s has no contract in %(month)s.", **names)
            )
        inp = by_key.get((employee.id, payslip.company_id.id, payslip.date_from))
        if not inp:
            raise IntegrityStop(
                "calculation",
                self.env._("%(employee)s has no monthly input for %(month)s.", **names),
            )
        context = builder.build(payslip.sudo(), main, inp)
        payslip.write(
            {
                "contract_id": main.id,
                "l10n_vn_input_id": inp.id,
                "l10n_vn_context": context,
                **self._l10n_vn_totals(context),
                "worked_days_line_ids": [Command.clear()]
                + [Command.create(v) for v in self._l10n_vn_worked_day_vals(inp, main)],
            }
        )
        payslip._l10n_vn_check_rules(context, names)
        # what this payslip takes from each damage decision (D56)
        payslip.sudo().l10n_vn_damage_allocation_ids.unlink()
        self.env["l10n_vn.payroll.damage.allocation"].sudo().create(
            [
                {"damage_id": a["damage_id"], "payslip_id": payslip.id, "amount": a["amount"]}
                for a in context["damage"]["allocations"]
            ]
        )

    def _l10n_vn_record_stop(self, code, message):
        """An error result for a payslip that cannot be calculated (D62)."""
        self.ensure_one()
        check = self.env["l10n_vn.payroll.check"].sudo().with_context(active_test=False).search(
            [("code", "=", code)], limit=1
        )
        self.env["l10n_vn.payroll.check.result"].sudo().create(
            {"payslip_id": self.id, "check_id": check.id, "level": "error", "message": message}
        )
        self.sudo().line_ids.unlink()
        self.sudo().l10n_vn_damage_allocation_ids.unlink()
        self.write({"l10n_vn_context": False, **self._l10n_vn_totals(False)})

    def _l10n_vn_run_checks(self):
        """Runs every active check on each payslip's snapshot (D59-D61, D63)."""
        checks = self.env["l10n_vn.payroll.check"].sudo().search([])
        Result = self.env["l10n_vn.payroll.check.result"].sudo()
        for payslip in self:
            context = payslip.l10n_vn_context or {}
            results = []
            for check in checks:
                finder = getattr(check, f"_l10n_vn_find_{check.code}", None)
                if not finder:
                    continue
                try:
                    findings = finder(payslip.sudo(), context)
                except UserError as error:
                    findings, forced = [(False, error.args[0])], "error"
                else:
                    forced = None
                for component, message in findings:
                    level = forced or check._l10n_vn_level(payslip, component)
                    if level == "off":
                        continue
                    results.append(
                        {
                            "payslip_id": payslip.id,
                            "check_id": check.id,
                            "component_id": component.id if component else False,
                            "level": level,
                            "message": message,
                        }
                    )
            created = Result.create(results)
            context = dict(
                context,
                checks=[
                    {"code": r.check_id.code, "component": r.component_id.code or None,
                     "level": r.level, "message": r.message}
                    for r in created
                ],
            )
            payslip.write({"l10n_vn_context": context})

    def _l10n_vn_advances(self):
        """Advances this payslip settles, oldest first, as [{"id", "amount"}] (D57).

        None here; l10n_vn_payroll_account overrides it.
        """
        self.ensure_one()
        return []

    def _l10n_vn_check_rules(self, context, names):
        """Every component with context lines needs a rule that shows them (D44)."""
        self.ensure_one()
        rules = self._get_salary_rules().filtered(lambda rule: rule.amount_select == RULE_TYPE)
        covered = set(rules.l10n_vn_component_id.ids)
        for line in context["lines"]:
            if line["component_id"] not in covered:
                raise IntegrityStop(
                    "calculation",
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
