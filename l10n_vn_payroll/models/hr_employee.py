# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

PAYROLL_GROUPS = "payroll.group_payroll_user"
REGIONS = [("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV")]
SCAN_GROUPS = ("worker", "support", "daily")
EXCEPTION_GROUPS = ("office", "manager")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_vn_pay_group = fields.Selection(
        [
            ("worker", "Worker"),
            ("support", "Production support"),
            ("office", "Office"),
            ("daily", "Daily-paid"),
            ("manager", "Manager without labour contract"),
        ],
        string="Pay Group",
        groups=PAYROLL_GROUPS,
    )
    l10n_vn_attendance_mode = fields.Selection(
        [("scan", "Scans decide time"), ("exception", "Present unless on leave")],
        string="Attendance Mode",
        compute="_compute_l10n_vn_attendance_mode",
        store=True,
        readonly=False,
        groups=PAYROLL_GROUPS,
    )
    l10n_vn_region = fields.Selection(
        REGIONS,
        string="Minimum Wage Region",
        default=lambda self: self._default_l10n_vn_region(),
        groups=PAYROLL_GROUPS,
    )
    l10n_vn_resident = fields.Boolean(string="Tax Resident", default=True, groups=PAYROLL_GROUPS)
    l10n_vn_union_member = fields.Boolean(string="Union Member", groups=PAYROLL_GROUPS)
    l10n_vn_personal_id = fields.Char(
        string="Personal ID No. (CCCD)",
        help="The 12-digit personal identification number on the citizen ID card. "
        "From 1 July 2025 it also serves as the personal tax code.",
        groups="hr.group_hr_user",
    )
    l10n_vn_pit_commitment_year = fields.Integer(
        string="PIT Commitment Form Year", groups=PAYROLL_GROUPS
    )
    l10n_vn_nursing_break = fields.Boolean(string="Nursing Break", groups=PAYROLL_GROUPS)

    @api.depends("l10n_vn_pay_group")
    def _compute_l10n_vn_attendance_mode(self):
        for employee in self:
            if employee.l10n_vn_pay_group in SCAN_GROUPS:
                employee.l10n_vn_attendance_mode = "scan"
            elif employee.l10n_vn_pay_group in EXCEPTION_GROUPS:
                employee.l10n_vn_attendance_mode = "exception"

    def _default_l10n_vn_region(self):
        try:
            value = self.env["base.time.parameter"]._strict_get(
                "vn.policy.region", fields.Date.context_today(self), company=self.env.company
            )
        except UserError:
            return False
        return value if value in dict(REGIONS) else False

    def _l10n_vn_dependent_count(self, date):
        """Number of PIT dependents counted in the month of ``date``."""
        self.ensure_one()
        month_start = date.replace(day=1)
        return len(
            self.sudo().relative_ids.filtered(lambda r: r._l10n_vn_counts_in(month_start))
        )

    def _l10n_vn_period_contracts(self, date_from, date_to):
        """Open or closed contracts overlapping the dates, oldest first (D31).

        Core's ``_get_contracts`` searches open contracts only, and writing a past end
        date closes a contract, so a leaver's contract would be lost.
        """
        self.ensure_one()
        return (
            self.env["hr.contract"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", self.id),
                    ("state", "in", ("open", "close")),
                    ("date_start", "<=", date_to),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", date_from),
                ],
                order="date_start, id",
            )
        )

    def _l10n_vn_nursing_until(self):
        """The latest first birthday of the employee's children, when nursing applies."""
        self.ensure_one()
        if not self.l10n_vn_nursing_break:
            return False
        child = self.env.ref("hr_employee_relative.relation_child", raise_if_not_found=False)
        births = [
            relative.date_of_birth
            for relative in self.sudo().relative_ids
            if relative.relation_id == child and relative.date_of_birth
        ]
        return max(births) + relativedelta(months=12) if births else False
