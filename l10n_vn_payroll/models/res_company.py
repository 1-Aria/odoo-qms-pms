# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# (code, name, type, [(date_from, value as stored text), ...])
# Values from the Vietnam Payroll Regulation Reference v0.2.
STATUTORY_PARAMETERS = [
    (
        "vn.min_wage.month",
        "Regional minimum wage, monthly",
        "json",
        [("2026-01-01", '{"I": 5310000, "II": 4730000, "III": 4140000, "IV": 3700000}')],
    ),
    (
        "vn.min_wage.hour",
        "Regional minimum wage, hourly",
        "json",
        [("2026-01-01", '{"I": 25500, "II": 22700, "III": 19900, "IV": 17800}')],
    ),
    (
        "vn.si.reference_level",
        "SI reference level",
        "float",
        [("2024-07-01", "2340000"), ("2026-07-01", "2530000")],
    ),
    (
        "vn.si.cap_multiple",
        "SI and HI cap, multiple of the reference level",
        "float",
        [("2026-01-01", "20")],
    ),
    (
        "vn.ui.cap_multiple",
        "UI cap, multiple of the regional minimum wage",
        "float",
        [("2026-01-01", "20")],
    ),
    ("vn.rate.ee.si", "Employee SI rate", "float", [("2026-01-01", "0.08")]),
    ("vn.rate.ee.hi", "Employee HI rate", "float", [("2026-01-01", "0.015")]),
    ("vn.rate.ee.ui", "Employee UI rate", "float", [("2026-01-01", "0.01")]),
    (
        "vn.rate.er.pension",
        "Employer pension and survivorship rate",
        "float",
        [("2026-01-01", "0.14")],
    ),
    (
        "vn.rate.er.sickness",
        "Employer sickness and maternity rate",
        "float",
        [("2026-01-01", "0.03")],
    ),
    (
        "vn.rate.er.accident",
        "Employer occupational accident rate",
        "float",
        [("2026-01-01", "0.005")],
    ),
    ("vn.rate.er.hi", "Employer HI rate", "float", [("2026-01-01", "0.03")]),
    ("vn.rate.er.ui", "Employer UI rate", "float", [("2026-01-01", "0.01")]),
    ("vn.rate.union_fee", "Employer union fee rate", "float", [("2026-01-01", "0.02")]),
    ("vn.rate.union_dues", "Union dues rate, members", "float", [("2026-01-01", "0.005")]),
    ("vn.union_dues.cap", "Union dues cap", "float", [("2026-01-01", "253000")]),
    (
        "vn.si.absence_days",
        "Working days without work or pay that suspend contributions",
        "integer",
        [("2026-01-01", "14")],
    ),
    ("vn.pit.self", "PIT personal deduction", "float", [("2026-01-01", "15500000")]),
    ("vn.pit.dependent", "PIT deduction per dependent", "float", [("2026-01-01", "6200000")]),
    (
        "vn.pit.brackets",
        "PIT monthly brackets",
        "json",
        [
            (
                "2026-01-01",
                "[[10000000, 0.05], [30000000, 0.10], [60000000, 0.20], "
                "[100000000, 0.30], [null, 0.35]]",
            )
        ],
    ),
    (
        "vn.pit.flat_short",
        "PIT flat rate, contracts under 3 months",
        "float",
        [("2026-01-01", "0.10")],
    ),
    (
        "vn.pit.flat_short_threshold",
        "PIT flat rate threshold per payment",
        "float",
        [("2026-01-01", "5000000")],
    ),
    ("vn.pit.nonresident", "PIT rate, non-residents", "float", [("2026-01-01", "0.20")]),
    (
        "vn.pit.meal_cap",
        "PIT-free cash meal allowance",
        "float",
        [("2026-01-01", "730000"), ("2026-07-01", "1200000")],
    ),
    (
        "vn.ot.factors",
        "OT and night factors",
        "json",
        [
            (
                "2026-01-01",
                '{"WD": 1.5, "RD": 2.0, "HOL": 3.0, "NIGHT": 0.3, "NWD": 2.0, '
                '"NWD_AFTER": 2.1, "NRD": 2.7, "NHOL": 3.9}',
            )
        ],
    ),
    ("vn.ot.limit.month", "OT hours limit per month", "integer", [("2026-01-01", "40")]),
    (
        "vn.ot.limit.year",
        "OT hours limit per year, textile and garment",
        "integer",
        [("2026-01-01", "300")],
    ),
    (
        "vn.ot.limit.day_share",
        "OT limit per day, share of the day's normal hours",
        "float",
        [("2026-01-01", "0.5")],
    ),
    (
        "vn.ot.limit.day_total",
        "Hours of work per day, normal and OT together",
        "float",
        [("2026-01-01", "12")],
    ),
    (
        "vn.damage.cap",
        "Damage compensation cap, share of pay after insurance and PIT",
        "float",
        [("2026-01-01", "0.30")],
    ),
    ("vn.probation.min_rate", "Minimum probation pay rate", "float", [("2026-01-01", "0.85")]),
    (
        "vn.probation.max_days",
        "Maximum probation by job (other: working days)",
        "json",
        [("2026-01-01", '{"manager": 180, "college": 60, "vocational": 30, "other": 6}')],
    ),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    def _l10n_vn_payroll_ensure_parameters(self):
        """Create the missing statutory parameters and versions of Vietnamese companies.

        Existing versions are never changed, so values edited in the UI stay.
        A failure is logged and the next company continues.
        """
        Param = self.env["base.time.parameter"].sudo()
        Version = self.env["base.time.parameter.version"].sudo()
        for company in self.sudo():
            if company.country_id.code != "VN":
                continue
            code = None
            try:
                with self.env.cr.savepoint():
                    for code, name, kind, versions in STATUTORY_PARAMETERS:
                        param = Param.search(
                            [("code", "=", code), ("company_id", "=", company.id)], limit=1
                        )
                        if not param:
                            param = Param.create(
                                {
                                    "name": name,
                                    "code": code,
                                    "type": kind,
                                    "company_id": company.id,
                                    "country_id": company.country_id.id,
                                }
                            )
                        present = {str(date) for date in param.version_ids.mapped("date_from")}
                        for date_from, value in versions:
                            if date_from not in present:
                                Version.create(
                                    {
                                        "parameter_id": param.id,
                                        "date_from": date_from,
                                        "value": value,
                                    }
                                )
            except Exception as error:  # noqa: BLE001 - seeding must not stop an install
                _logger.warning(
                    "Statutory payroll parameters not created for company %s (at %s): %s",
                    company.name,
                    code,
                    error,
                )

    @api.model
    def _l10n_vn_payroll_ensure_parameters_all(self):
        self.env["res.company"].sudo().search([])._l10n_vn_payroll_ensure_parameters()
