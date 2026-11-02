# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nVnPayrollParticipantType(models.Model):
    _name = "l10n_vn.payroll.participant.type"
    _description = "Payroll Participant Type"
    _order = "code"

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    fund_pension = fields.Boolean(string="Pension and survivorship")
    fund_sickness = fields.Boolean(string="Sickness and maternity")
    fund_accident = fields.Boolean(string="Occupational accident")
    fund_hi = fields.Boolean(string="Health insurance")
    fund_ui = fields.Boolean(string="Unemployment insurance")
    fund_union_fee = fields.Boolean(string="Union fee (employer)")
    dues_allowed = fields.Boolean(string="Union dues for members")
    base_source = fields.Selection(
        [
            ("components", "Contract components in the SI base"),
            ("declared", "Declared on the contract"),
        ],
        required=True,
        default="components",
    )
    floor = fields.Selection(
        [
            ("min_wage", "Regional minimum wage"),
            ("reference_level", "SI reference level"),
            ("none", "None"),
        ],
        required=True,
        default="min_wage",
    )
    pit_method = fields.Selection(
        [
            ("progressive", "Progressive"),
            ("flat_short", "Flat 10%, short contracts"),
            ("flat_nonresident", "Flat 20%, non-residents"),
        ],
        string="PIT method",
        required=True,
        default="progressive",
    )
    note = fields.Text()

    _sql_constraints = [
        ("code_unique", "unique(code)", "A participant type code must be unique."),
    ]
