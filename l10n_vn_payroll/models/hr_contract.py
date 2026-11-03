# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

PAYROLL_GROUPS = "payroll.group_payroll_user"


class HrContract(models.Model):
    _inherit = "hr.contract"

    l10n_vn_line_ids = fields.One2many(
        "l10n_vn.payroll.contract.line",
        "contract_id",
        string="Pay Lines",
        groups=PAYROLL_GROUPS,
        copy=True,
    )
    l10n_vn_participant_type_id = fields.Many2one(
        "l10n_vn.payroll.participant.type",
        string="Participant Type",
        ondelete="restrict",
        default=lambda self: self.env.ref(
            "l10n_vn_payroll.participant_labour", raise_if_not_found=False
        ),
        groups=PAYROLL_GROUPS,
    )
    l10n_vn_base_source = fields.Selection(
        related="l10n_vn_participant_type_id.base_source", groups=PAYROLL_GROUPS
    )
    l10n_vn_declared_si_base = fields.Monetary(
        string="Declared SI Base", groups=PAYROLL_GROUPS
    )
    l10n_vn_probation_form = fields.Selection(
        [
            ("none", "No probation"),
            ("clause", "Clause in this contract"),
            ("contract", "Separate probation contract"),
        ],
        string="Probation",
        required=True,
        default="none",
        groups=PAYROLL_GROUPS,
    )
    l10n_vn_probation_job = fields.Selection(
        [
            ("manager", "Enterprise manager"),
            ("college", "College degree or above"),
            ("vocational", "Vocational qualification"),
            ("other", "Other work"),
        ],
        string="Probation Job Category",
        help="Sets the legal probation limit (vn.probation.max_days) the checks compare with.",
        groups=PAYROLL_GROUPS,
    )

    def _l10n_vn_sync_wage(self):
        """Keep ``wage`` equal to the lines in force today that set it.

        Payroll never reads ``wage``; it is kept for the screens that show it.
        A value that cannot be read leaves ``wage`` as it is.
        """
        for contract in self.sudo():
            today = fields.Date.context_today(contract)
            lines = contract.l10n_vn_line_ids._l10n_vn_in_force(today).filtered(
                lambda line: line.component_id.sets_wage
            )
            if not lines:
                continue
            try:
                wage = sum(line._l10n_vn_amount_on(today) for line in lines)
            except UserError as error:
                _logger.info(
                    "Contract %s: wage not updated from pay lines: %s", contract.id, error
                )
                continue
            if contract.currency_id.compare_amounts(contract.wage, wage) != 0:
                contract.wage = wage

    @api.constrains("date_start", "date_end")
    def _check_l10n_vn_line_dates(self):
        self.sudo().l10n_vn_line_ids._check_line()

    @api.constrains(
        "l10n_vn_participant_type_id",
        "l10n_vn_declared_si_base",
        "l10n_vn_probation_form",
        "trial_date_end",
    )
    def _check_l10n_vn_profile(self):
        _ = self.env._
        for contract in self.sudo():
            participant = contract.l10n_vn_participant_type_id
            if participant.base_source == "declared" and contract.l10n_vn_declared_si_base <= 0:
                raise ValidationError(
                    _(
                        "Contract %(contract)s: participant type %(type)s needs a declared SI base.",
                        contract=contract.name,
                        type=participant.name,
                    )
                )
            if contract.l10n_vn_probation_form == "clause" and not contract.trial_date_end:
                raise ValidationError(
                    _(
                        "Contract %(contract)s: a probation clause needs the end of the trial "
                        "period.",
                        contract=contract.name,
                    )
                )

    def _l10n_vn_pit_method(self, date):
        """PIT method of this contract for a payment on ``date`` (design §8.2)."""
        self.ensure_one()
        contract = self.sudo()
        employee = contract.employee_id
        if not employee.l10n_vn_resident:
            return "flat_nonresident"
        method = contract.l10n_vn_participant_type_id.pit_method or "progressive"
        if method != "progressive":
            return method
        if (
            contract.date_end
            and contract.date_start + relativedelta(months=3)
            > contract.date_end + datetime.timedelta(days=1)
            and employee.l10n_vn_pit_commitment_year != date.year
        ):
            return "flat_short"
        return "progressive"
