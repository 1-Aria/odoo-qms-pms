# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Loading the garment pay scheme into a company."""

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D, PayrollCase

TOTAL = 9 + 2 + 4 + 35 + 1 + 35  # parameters, scales, categories, components, structure, rules
CATEGORY_OF_KIND = {
    "earning": "EARN",
    "deduction": "DED",
    "employer": "ER",
    "total": "TOTAL",
    "info": "TOTAL",
}


@tagged("post_install", "-at_install")
class TestLoad(PayrollCase):
    # ------------------------------------------------------------------ helpers
    def _components(self, company=None):
        return (
            self.env["l10n_vn.payroll.component"]
            .with_context(active_test=False)
            .search([("company_id", "=", (company or self.company).id)])
        )

    def _component(self, code):
        return self._components().filtered(lambda c: c.code == code)

    def _structure(self):
        return self.env["hr.payroll.structure"].search(
            [("code", "=", "VN_GARMENT"), ("company_id", "=", self.company.id)]
        )

    def _rules(self):
        return self._structure().with_context(active_test=False).rule_ids

    def _scale(self, code):
        return self.env["l10n_vn.payroll.scale"].search(
            [("code", "=", code), ("company_id", "=", self.company.id)]
        )

    def _param(self, code):
        return self.env["base.time.parameter"].search(
            [("code", "=", code), ("company_id", "=", self.company.id)]
        )

    # ------------------------------------------------------------------ tests
    def test_load_creates(self):
        result = self.company._l10n_vn_garment_load()
        Param = self.env["base.time.parameter"]
        for code, value in (
            ("vn.policy.region", "IV"),
            ("vn.policy.std_days", 26),
            ("vn.policy.base_salary", 3700000),
            ("vn.policy.probation_rate", 0.85),
            ("vn.policy.attainment_cap", 1),
            ("vn.policy.ot_min_hours_day", 0.8),
            ("vn.policy.constant_months", 6),
            ("vn.policy.net_change", 0.30),
            ("vn.check.variable_constant.PERF", "note"),
        ):
            self.assertEqual(
                Param._strict_get(code, D(2026, 10, 31), company=self.company), value, code
            )
        self.assertEqual(len(self._scale("PROD").version_ids.cell_ids), 5)
        grade_cells = self._scale("GRADE").version_ids.cell_ids
        self.assertEqual(len(grade_cells), 15)
        g22 = grade_cells.filtered(lambda c: c.key == "G2-2")
        self.assertEqual((g22.amount, g22.grade, g22.step), (8000000, "G2", 2))
        components = self._components()
        self.assertEqual(len(components), 35)
        self.assertEqual(
            set(components.filtered(lambda c: not c.active).mapped("code")),
            {"ATT", "DUTY", "PHONE"},
        )
        structure = self._structure()
        self.assertTrue(structure.l10n_vn_payroll)
        rules = self._rules()
        self.assertEqual(len(rules), 35)
        self.assertEqual(set(rules.mapped("code")), set(components.mapped("code")))
        for rule in rules:
            self.assertEqual(rule.l10n_vn_component_id.code, rule.code)
            self.assertEqual(rule.amount_select, "l10n_vn_component")
            self.assertEqual(
                rule.category_id.code, CATEGORY_OF_KIND[rule.l10n_vn_component_id.kind], rule.code
            )
        self.assertEqual(len(result["created"]), TOTAL)
        self.assertEqual(result["kept"], [])

    def test_component_settings(self):
        self.company._l10n_vn_garment_load()
        base = self._component("BASE")
        self.assertEqual(
            (base.amount_source, base.amount_parameter), ("parameter", "vn.policy.base_salary")
        )
        self.assertTrue(base.in_si_base and base.in_ot_base and base.sets_wage)
        prod = self._component("PROD")
        self.assertEqual(prod.scale_id, self._scale("PROD"))
        self.assertTrue(prod.variable and prod.in_ot_base)
        self.assertFalse(prod.in_si_base)
        self.assertEqual(prod.attainment_source, "supervisor")
        perf = self._component("PERF")
        self.assertEqual(
            (perf.amount_source, perf.scale_id, perf.attainment_source),
            ("scale_remainder", self._scale("GRADE"), "manager"),
        )
        self.assertEqual(self._component("LEAVE").pit_treatment, "exempt")
        att = self._component("ATT")
        self.assertFalse(att.active)
        self.assertEqual(
            (att.amount_source, att.amount_parameter, att.condition),
            ("parameter", "vn.policy.attendance_bonus", "attendance"),
        )
        night = self._component("OT_NWD_AFTER")
        self.assertEqual((night.ot_category, night.pit_treatment), ("NWD_AFTER", "ot"))

    def test_vietnamese_names(self):
        self.env["res.lang"]._activate_lang("vi_VN")
        self.company._l10n_vn_garment_load()
        base = self._component("BASE")
        self.assertEqual(base.with_context(lang="vi_VN").name, "Lương cơ bản")
        self.assertEqual(base.with_context(lang="en_US").name, "Base salary")
        rule = self._rules().filtered(lambda r: r.code == "BASE")
        self.assertEqual(rule.with_context(lang="vi_VN").name, "Lương cơ bản")
        self.assertEqual(rule.with_context(lang="en_US").name, "Base salary")

    def test_load_again(self):
        self.company._l10n_vn_garment_load()
        result = self.company._l10n_vn_garment_load()
        self.assertEqual(result["created"], [])
        self.assertEqual(len(result["kept"]), TOTAL)
        self.assertEqual(len(self._components()), 35)
        self.assertEqual(len(self._rules()), 35)

    def test_existing_kept(self):
        base = self.env["l10n_vn.payroll.component"].create(
            {
                "code": "BASE",
                "name": "Trial base",
                "company_id": self.company.id,
                "kind": "earning",
                "legal_nature": "job_salary",
                "pit_treatment": "taxable",
                "proration": "paid_days",
                "amount_source": "line",
                "section": "other",
            }
        )
        self.env["base.time.parameter"].create(
            {
                "name": "vn.policy.std_days",
                "code": "vn.policy.std_days",
                "type": "integer",
                "company_id": self.company.id,
                "version_ids": [Command.create({"date_from": D(2026, 5, 1), "value": "24"})],
            }
        )
        self.env["l10n_vn.payroll.scale"].create(
            {
                "code": "PROD",
                "name": "Trial levels",
                "kind": "level",
                "company_id": self.company.id,
                "version_ids": [
                    Command.create(
                        {
                            "date_from": D(2026, 1, 1),
                            "cell_ids": [Command.create({"key": "Entry", "amount": 800000})],
                        }
                    )
                ],
            }
        )
        result = self.company._l10n_vn_garment_load()
        self.assertEqual(
            (base.name, base.section, base.amount_source), ("Trial base", "other", "line")
        )
        std_days = self._param("vn.policy.std_days")
        self.assertEqual(std_days.version_ids.mapped("date_from"), [D(2026, 5, 1)])
        self.assertEqual(std_days.version_ids.mapped("value"), ["24"])
        self.assertEqual(self._scale("PROD").version_ids.cell_ids.mapped("key"), ["Entry"])
        for label in ("component BASE", "parameter vn.policy.std_days", "scale PROD"):
            self.assertIn(label, result["kept"])
            self.assertNotIn(label, result["created"])
        rule = self._rules().filtered(lambda r: r.code == "BASE")
        self.assertEqual(rule.l10n_vn_component_id, base)
        self.assertEqual(self._component("PROD").scale_id, self._scale("PROD"))

    def test_category_shared(self):
        self.env["hr.salary.rule.category"].create(
            {"name": "Shared deductions", "code": "DED", "company_id": False}
        )
        self.company._l10n_vn_garment_load()
        deductions = self._rules().filtered(
            lambda r: r.l10n_vn_component_id.kind == "deduction"
        )
        self.assertTrue(deductions)
        for rule in deductions:
            self.assertEqual(rule.category_id.code, "DED")
            self.assertFalse(rule.category_id.company_id, rule.code)
        self.assertFalse(
            self.env["hr.salary.rule.category"].search(
                [("code", "=", "DED"), ("company_id", "=", self.company.id)]
            )
        )

    def test_not_vietnamese(self):
        company = self.env["res.company"].create(
            {"name": "Payroll Test Company FR", "country_id": self.env.ref("base.fr").id}
        )
        with self.assertRaises(UserError):
            company._l10n_vn_garment_load()
        self.assertFalse(self._components(company))

    def test_access(self):
        officer = self._user("l10n_vn_garment_officer", ["payroll.group_payroll_user"])
        manager = self._user("l10n_vn_garment_manager", ["payroll.group_payroll_manager"])
        with self.assertRaises(AccessError):
            self.company.with_env(self._as(officer))._l10n_vn_garment_load()
        self.assertFalse(self._components())
        result = self.company.with_env(self._as(manager))._l10n_vn_garment_load()
        self.assertEqual(len(result["created"]), TOTAL)

    def test_settings_button(self):
        settings = self.env["res.config.settings"].with_company(self.company).create({})
        self.assertEqual(settings.company_id, self.company)
        action = settings.action_l10n_vn_garment_load()
        self.assertEqual(action["tag"], "display_notification")
        message = action["params"]["message"]
        self.assertIn(self.company.name, message)
        self.assertIn(f"created {TOTAL} (", message)
