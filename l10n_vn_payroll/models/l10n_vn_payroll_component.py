# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Sources whose amounts sit on contract pay lines.
LINE_SOURCES = ("line", "parameter", "scale", "scale_remainder")


class L10nVnPayrollComponent(models.Model):
    _name = "l10n_vn.payroll.component"
    _description = "Payroll Component"
    _order = "sequence, code"
    _check_company_auto = True

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    kind = fields.Selection(
        [
            ("earning", "Earning"),
            ("deduction", "Deduction"),
            ("employer", "Employer contribution"),
            ("total", "Total"),
            ("info", "Information"),
        ],
        required=True,
        default="earning",
    )
    legal_nature = fields.Selection(
        [
            ("job_salary", "Salary by job"),
            ("fixed_allowance", "Fixed allowance"),
            ("fixed_supplement", "Fixed supplement"),
            ("variable_salary", "Variable salary"),
            ("bonus", "Bonus (Art. 104)"),
            ("welfare", "Welfare support"),
            ("overtime", "Overtime"),
            ("night", "Night work"),
            ("leave_pay", "Leave pay"),
            ("severance", "Severance"),
            ("statutory", "Statutory contribution or tax"),
            ("union", "Union"),
            ("damage", "Damage compensation"),
            ("advance", "Advance"),
            ("adjustment", "Adjustment"),
            ("total", "Total"),
        ],
        required=True,
    )
    in_si_base = fields.Boolean(string="In SI base")
    in_ot_base = fields.Boolean(string="In OT base")
    pit_treatment = fields.Selection(
        [
            ("taxable", "Taxable"),
            ("exempt", "Exempt"),
            ("exempt_cap", "Exempt up to a cap"),
            ("excluded", "Excluded"),
            ("ot", "Exempt within the OT limits"),
        ],
        string="PIT treatment",
    )
    pit_cap_parameter = fields.Char(string="PIT cap parameter")
    amount_source = fields.Selection(
        [
            ("line", "Amount on the pay line"),
            ("parameter", "Parameter"),
            ("scale", "Scale cell"),
            ("scale_remainder", "Remainder of a scale cell"),
            ("entered", "Entered each month"),
            ("ie_units", "IE units × unit rate"),
            ("ot", "Per OT hour"),
            ("engine", "Calculated"),
        ],
        required=True,
    )
    amount_parameter = fields.Char()
    scale_id = fields.Many2one(
        "l10n_vn.payroll.scale", ondelete="restrict", check_company=True
    )
    proration = fields.Selection(
        [
            ("paid_days", "Paid days"),
            ("days_worked", "Days worked"),
            ("none", "Not prorated"),
            ("per_day", "Daily rate × paid days"),
        ]
    )
    probation_applies = fields.Boolean()
    variable = fields.Boolean()
    attainment_source = fields.Selection(
        [("supervisor", "Supervisor"), ("manager", "Manager"), ("ie", "IE")]
    )
    condition = fields.Selection(
        [("none", "None"), ("attendance", "Attendance")], required=True, default="none"
    )
    ot_category = fields.Selection(
        [
            ("WD", "OT on a workday"),
            ("RD", "OT on a rest day"),
            ("HOL", "OT on a holiday"),
            ("NIGHT", "Night, normal hours"),
            ("NWD", "Night OT, workday"),
            ("NWD_AFTER", "Night OT, workday after daytime OT"),
            ("NRD", "Night OT, rest day"),
            ("NHOL", "Night OT, holiday"),
            ("all", "All categories (supplement)"),
        ],
        string="OT category",
    )
    engine_code = fields.Selection(
        [
            ("GROSS", "Gross pay"),
            ("EE_SI", "Employee SI"),
            ("EE_HI", "Employee HI"),
            ("EE_UI", "Employee UI"),
            ("DUES", "Union dues"),
            ("PIT", "Personal income tax"),
            ("DAMAGE", "Damage compensation"),
            ("NET", "Net pay"),
            ("ADVANCE", "Advance settled"),
            ("TO_PAY", "Remaining to pay"),
            ("ER_PENSION", "Employer pension"),
            ("ER_SICKNESS", "Employer sickness and maternity"),
            ("ER_ACCIDENT", "Employer occupational accident"),
            ("ER_HI", "Employer HI"),
            ("ER_UI", "Employer UI"),
            ("UNION_FEE", "Employer union fee"),
        ]
    )
    section = fields.Selection(
        [
            ("salary", "Salary"),
            ("ot", "Overtime"),
            ("bonus", "Bonuses"),
            ("other", "Other earnings"),
            ("deduction", "Deductions"),
            ("employer", "Employer"),
            ("total", "Totals"),
        ],
        required=True,
        default="salary",
    )
    register_id = fields.Many2one("hr.contribution.register", ondelete="restrict")
    sets_wage = fields.Boolean(string="Sets the contract wage")
    legal_reference = fields.Char()
    note = fields.Text()

    _sql_constraints = [
        (
            "code_company_unique",
            "unique(code, company_id)",
            "A component code must be unique per company.",
        ),
    ]

    @api.constrains(
        "kind",
        "amount_source",
        "scale_id",
        "amount_parameter",
        "engine_code",
        "ot_category",
        "proration",
        "pit_treatment",
        "pit_cap_parameter",
        "variable",
        "attainment_source",
    )
    def _check_configuration(self):
        for component in self:
            problem = component._configuration_problem()
            if problem:
                raise ValidationError(
                    self.env._(
                        "Component %(code)s: %(problem)s",
                        code=component.code,
                        problem=problem,
                    )
                )

    def _configuration_problem(self):
        self.ensure_one()
        _ = self.env._
        source = self.amount_source
        if source in ("scale", "scale_remainder"):
            if not self.scale_id:
                return _("a scale source needs a scale.")
        elif self.scale_id:
            return _("only a scale source has a scale.")
        if source == "parameter" and not self.amount_parameter:
            return _("a parameter source needs a parameter code.")
        if source == "engine":
            if not self.engine_code:
                return _("a calculated component needs an engine code.")
        elif self.engine_code:
            return _("only a calculated component has an engine code.")
        if source == "ot":
            if not self.ot_category:
                return _("an OT component needs an OT category.")
            if self.kind != "earning":
                return _("an OT component is an earning.")
            if self.ot_category == "all" and not self.amount_parameter:
                return _("an OT supplement needs the parameter of its amount per hour.")
        if self.kind == "earning":
            if not self.pit_treatment:
                return _("an earning needs a PIT treatment.")
            if source in LINE_SOURCES and not self.proration:
                return _("an earning on pay lines needs a proration.")
        if self.pit_treatment == "exempt_cap" and not self.pit_cap_parameter:
            return _("an exemption up to a cap needs the cap parameter.")
        if self.variable:
            if self.kind != "earning":
                return _("only an earning can be variable.")
            if not self.attainment_source:
                return _("a variable component needs an attainment source.")
        if self.proration == "per_day" and source != "line":
            return _("a daily rate is an amount on the pay line.")
        return False
