# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from ..models.res_company import STATUTORY_PARAMETERS
from .common import D, PayrollCase


@tagged("post_install", "-at_install")
class TestStatutoryParameters(PayrollCase):
    def _params(self, company):
        return self.env["base.time.parameter"].search(
            [("company_id", "=", company.id), ("code", "=like", "vn.%")]
        )

    def _get(self, code, date):
        return self.env["base.time.parameter"]._strict_get(code, date, company=self.company)

    def test_created_for_vietnamese_company(self):
        self.company._l10n_vn_payroll_ensure_parameters()
        params = self._params(self.company)
        for code, _name, _kind, versions in STATUTORY_PARAMETERS:
            param = params.filtered(lambda p, code=code: p.code == code)
            self.assertEqual(len(param), 1, code)
            self.assertEqual(
                sorted(str(d) for d in param.version_ids.mapped("date_from")),
                sorted(date for date, _value in versions),
                code,
            )
        self.assertEqual(self._get("vn.si.reference_level", D(2026, 6, 30)), 2340000)
        self.assertEqual(self._get("vn.si.reference_level", D(2026, 7, 1)), 2530000)
        brackets = self._get("vn.pit.brackets", D(2026, 6, 1))
        self.assertEqual(len(brackets), 5)
        self.assertIsNone(brackets[-1][0])

    def test_idempotent_and_keeps_edits(self):
        self.company._l10n_vn_payroll_ensure_parameters()
        params = self._params(self.company)
        version_count = len(params.version_ids)
        rate = params.filtered(lambda p: p.code == "vn.rate.ee.si").version_ids
        rate.value = "0.09"
        self.company._l10n_vn_payroll_ensure_parameters()
        params_after = self._params(self.company)
        self.assertEqual(params_after, params)
        self.assertEqual(len(params_after.version_ids), version_count)
        self.assertEqual(self._get("vn.rate.ee.si", D(2026, 6, 1)), 0.09)

    def test_missing_version_added(self):
        self.company._l10n_vn_payroll_ensure_parameters()
        reference = self._params(self.company).filtered(lambda p: p.code == "vn.si.reference_level")
        reference.version_ids.filtered(lambda v: v.date_from == D(2026, 7, 1)).unlink()
        self.assertEqual(self._get("vn.si.reference_level", D(2026, 7, 1)), 2340000)
        self.company._l10n_vn_payroll_ensure_parameters()
        self.assertEqual(self._get("vn.si.reference_level", D(2026, 7, 1)), 2530000)

    def test_not_for_other_countries(self):
        french = self.env["res.company"].create(
            {"name": "Payroll Test Company FR", "country_id": self.env.ref("base.fr").id}
        )
        french._l10n_vn_payroll_ensure_parameters()
        self.assertFalse(self._params(french))
