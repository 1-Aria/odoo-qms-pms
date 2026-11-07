# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

from openpyxl import load_workbook

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .run_common import RunCase


@tagged("post_install", "-at_install")
class TestReport(RunCase):
    def _calculated_run(self):
        run = self._new_run()
        self._calculate(run)
        return run

    def test_totals_from_snapshot(self):
        slip = self._slip(self._calculated_run(), self.alice)
        context = slip.l10n_vn_context
        self.assertEqual(slip.l10n_vn_gross, context["gross"])
        self.assertEqual(slip.l10n_vn_employee_insurance, context["employee_insurance"])
        self.assertEqual(slip.l10n_vn_pit, context["pit"]["pit"])
        self.assertEqual(slip.l10n_vn_net, context["net"])
        self.assertEqual(slip.l10n_vn_to_pay, context["to_pay"])
        sections = (slip.l10n_vn_salary_pay + slip.l10n_vn_ot_pay + slip.l10n_vn_bonus_pay
                    + slip.l10n_vn_other_pay)
        self.assertEqual(sections, slip.l10n_vn_gross)
        employer = slip.line_ids.filtered(lambda l: l.l10n_vn_component_id.kind == "employer")
        self.assertEqual(slip.l10n_vn_employer_cost, sum(employer.mapped("total")))

    def test_time_totals(self):
        employee, _contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        inp = self._input(employee, paid_days=24, days_worked=22, ot_hours_json={"WD": 10, "RD": 4})
        slip = self._payslip(employee)
        self.assertEqual((inp.ot_wd_hours, inp.ot_rd_hours, inp.ot_hol_hours), (10, 4, 0))
        self.assertEqual((slip.l10n_vn_paid_days, slip.l10n_vn_days_worked), (24, 22))
        self.assertEqual((slip.l10n_vn_ot_hours, slip.l10n_vn_ot_wd_hours, slip.l10n_vn_ot_rd_hours),
                         (14, 10, 4))

    def test_totals_cleared_on_stop(self):
        employee, _contract = self._hire(lines=[(self.prod, {"scale_key": "Entry"})])
        self._input(employee)
        slip = self._payslip(employee)
        self._stopped(slip, "missing_attainment", "attainment")
        self.assertFalse(slip.l10n_vn_gross)
        self.assertFalse(slip.l10n_vn_paid_days)

    def test_analysis_matches_payslip(self):
        slip = self._slip(self._calculated_run(), self.alice)
        rows = self.env["l10n_vn.payroll.analysis"].search([("payslip_id", "=", slip.id)])
        earnings = rows.filtered(lambda r: r.kind == "earning")
        self.assertEqual(sum(earnings.mapped("amount")), slip.l10n_vn_gross)
        deductions = slip.line_ids.filtered(lambda l: l.l10n_vn_component_id.kind == "deduction")
        self.assertEqual(sum(rows.filtered(lambda r: r.kind == "deduction").mapped("amount")),
                         sum(deductions.mapped("total")))

    def test_payslip_report_renders(self):
        run = self._approved_run()
        html, _kind = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_vn_payroll.action_report_l10n_vn_payslip", run.slip_ids.ids
        )
        html = html.decode()
        self.assertEqual(html.count('class="page"'), len(run.slip_ids))
        for slip in run.slip_ids:
            self.assertIn(slip.employee_id.name, html)
        self.assertIn("Ngày công", html)
        self.assertIn("Còn được lĩnh", html)

    def _export(self, xmlid, model, ids):
        template = self.env.ref(xmlid)
        out_file, _name = self.env["xlsx.export"].export_xlsx(template, model, ids)
        if isinstance(out_file, str):
            out_file = out_file.encode()
        # an .xlsx file is a zip archive: "PK"; anything else is base64
        content = out_file if out_file[:2] == b"PK" else base64.decodebytes(out_file)
        return load_workbook(io.BytesIO(content)).active

    def test_templates_export(self):
        run = self._calculated_run()
        sheet = self._export("l10n_vn_payroll.xlsx_payroll_register", "hr.payslip.run", run.ids)
        names = [sheet.cell(row=r, column=2).value for r in range(5, 5 + len(run.slip_ids))]
        self.assertEqual(set(names), set(run.slip_ids.employee_id.mapped("name")))
        sheet = self._export(
            "l10n_vn_payroll.xlsx_attendance_signoff", "l10n_vn.payroll.period", self.period.ids
        )
        self.assertEqual(sheet["A2"].value, self.period.name)

    def test_analysis_access(self):
        self._calculated_run()
        self.assertTrue(self._as(self.reader)["l10n_vn.payroll.analysis"].search_count([]))
        outsider = self._user("test.vn_report.outsider", [])
        with self.assertRaises(AccessError):
            self._as(outsider)["l10n_vn.payroll.analysis"].search([])
