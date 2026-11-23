# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import D, ContractDocumentCase

REPORT = "l10n_vn_hr_contract_document.action_report_contract"


@tagged("post_install", "-at_install")
class TestDocumentReport(ContractDocumentCase):
    def _html(self, contract):
        html, _kind = self.env["ir.actions.report"]._render_qweb_html(REPORT, contract.ids)
        return html.decode()

    def test_helpers(self):
        doc = self.env["l10n_vn.contract.document"]
        self.assertEqual(doc._money(4500000), "4.500.000")
        self.assertEqual(doc._words(4500000), "Bốn triệu năm trăm nghìn đồng")
        self.assertEqual(doc._date(D(2026, 11, 2)), "02/11/2026")
        self.assertEqual(doc._date_parts(D(2026, 11, 2)), ("02", "11", "2026"))
        self.assertIsNone(doc._date_parts(False))

    def test_values_labour(self):
        contract = self._doc_contract("labour", date_end=D(2027, 11, 1))
        values = contract._l10n_vn_document_values()
        self.assertEqual(values["title"], "HỢP ĐỒNG LAO ĐỘNG")
        self.assertEqual(values["term"]["length"], "12 tháng")
        self.assertEqual(len(values["salary"]), 1)
        self.assertEqual(values["salary"][0]["amount_text"], "4.500.000")
        self.assertEqual(values["salary"][0]["unit"], "tháng")
        self.assertEqual(values["variable"], [self.prod.name])
        self.assertTrue(values["paid_by_transfer"])
        self.assertTrue(values["insured"])
        self.assertIsNone(values["probation"])
        self.assertEqual(values["employee"]["gender"], "Nữ")
        self.assertEqual(values["employee"]["birthday"], "04/03/1995")
        self.assertEqual(values["company"]["rep_name"], "Test Director")

    def test_values_length_in_days(self):
        contract = self._doc_contract("labour", date_end=D(2026, 12, 15))
        values = contract._l10n_vn_document_values()
        self.assertEqual(values["term"]["length"], "44 ngày")

    def test_values_probation_clause(self):
        # 2 to 9 November 2026, counted on the contract's calendar: a new company's
        # calendar copies the current company's week, so the expected count is
        # taken from its working weekdays
        contract = self._doc_contract(
            "labour",
            l10n_vn_probation_form="clause",
            trial_date_end=D(2026, 11, 9),
            l10n_vn_probation_job="other",
        )
        # lunch periods are not working time (the garment calendar has lunch-only Sundays)
        weekdays = {
            int(a.dayofweek)
            for a in contract.resource_calendar_id.attendance_ids
            if a.day_period != "lunch" and not a.display_type
        }
        expected = sum(
            1 for day in range(2, 10) if D(2026, 11, day).weekday() in weekdays
        )
        self.assertIn(expected, (5, 6, 7))
        probation = contract._l10n_vn_document_values()["probation"]
        self.assertEqual(probation["length"], f"{expected} ngày làm việc")
        self.assertEqual(probation["rate"], 85)
        self.assertEqual(probation["amount"], 3825000)
        self.assertEqual(probation["date_end"], "09/11/2026")

    def test_values_training(self):
        contract = self._doc_contract("training", date_end=D(2027, 1, 31))
        values = contract._l10n_vn_document_values()
        self.assertEqual(values["party_b"], "NGƯỜI TẬP NGHỀ")
        self.assertEqual(values["training"]["commitment_months"], 0)
        contract.write(
            {
                "l10n_vn_commitment_months": 6,
                "l10n_vn_training_cost": 1200000,
                "l10n_vn_training_kind": "apprenticeship",
            }
        )
        values = contract._l10n_vn_document_values()
        self.assertEqual(values["party_b"], "NGƯỜI HỌC NGHỀ")
        self.assertEqual(values["training"]["commitment_months"], 6)
        self.assertEqual(values["training"]["cost_text"], "1.200.000")
        self.assertEqual(values["training"]["cost_words"], "Một triệu hai trăm nghìn đồng")

    def test_values_current_address(self):
        contract = self._doc_contract("labour")
        self.assertEqual(contract._l10n_vn_document_values()["employee"]["current_address"], "")
        self.employee.write({"private_street": "5 Other Street", "private_city": "Long Xuyên"})
        self.assertEqual(
            contract._l10n_vn_document_values()["employee"]["current_address"],
            "5 Other Street, Long Xuyên",
        )

    def test_report_labour_renders(self):
        contract = self._doc_contract("labour", date_end=D(2027, 11, 1))
        html = self._html(contract)
        for text in (
            "BẢN NHÁP",
            "HỢP ĐỒNG LAO ĐỘNG",
            self.employee.name,
            "4.500.000",
            "Bốn triệu năm trăm nghìn đồng",
            "theo Quy chế trả lương của Công ty",
            self.prod.name,
            "Điều 12. Điều khoản thi hành",
        ):
            self.assertIn(text, html)

    def test_report_probation_and_training_render(self):
        probation = self._doc_contract(
            "probation", date_end=D(2026, 12, 1), l10n_vn_probation_job="college"
        )
        html = self._html(probation)
        self.assertIn("HỢP ĐỒNG THỬ VIỆC", html)
        self.assertIn("Điều 7. Điều khoản thi hành", html)
        self.assertIn("3.825.000", html)
        training = self._doc_contract("training", date_end=D(2027, 1, 31))
        html = self._html(training)
        self.assertIn("HỢP ĐỒNG ĐÀO TẠO", html)
        self.assertIn("Điều 7. Điều khoản thi hành", html)
        self.assertNotIn("hoàn trả chi phí đào tạo", html)
        training.l10n_vn_commitment_months = 6
        html = self._html(training)
        self.assertIn("Điều 7. Cam kết làm việc và hoàn trả chi phí đào tạo", html)
        self.assertIn("Điều 8. Điều khoản thi hành", html)

    def test_report_uses_company_wording(self):
        self.env["l10n_vn.contract.wording"].create(
            {"company_id": self.company.id, "payday": "vào ngày 10 của tháng kế tiếp."}
        )
        html = self._html(self._doc_contract("labour"))
        self.assertIn("vào ngày 10 của tháng kế tiếp.", html)

    def test_report_dots_for_missing(self):
        contract = self._doc_contract("labour")
        complete = self._html(contract).count('class="o_dots"')
        self.employee.l10n_vn_id_issue_place = False
        html = self._html(contract)
        self.assertIn("HỢP ĐỒNG LAO ĐỘNG", html)
        self.assertNotIn("Cục Cảnh sát QLHC về TTXH", html)
        self.assertEqual(html.count('class="o_dots"'), complete + 1)

    def test_print_draft_refused_for_none(self):
        with self.assertRaises(UserError):
            self._doc_contract("none").action_l10n_vn_print()
        action = self._doc_contract("labour").action_l10n_vn_print()
        self.assertEqual(
            action["report_name"], "l10n_vn_hr_contract_document.report_contract"
        )

    def test_values_need_payroll_group(self):
        contract = self._doc_contract("labour")
        hr_user = self._user("doc_hr_manager", ["hr_contract.group_hr_contract_manager"])
        payroll_user = self._user(
            "doc_payroll_user",
            ["hr_contract.group_hr_contract_manager", "payroll.group_payroll_user"],
        )
        as_hr = self._as(hr_user)["hr.contract"].browse(contract.id)
        self.assertEqual(as_hr.name, contract.name)
        with self.assertRaises(AccessError):
            as_hr._l10n_vn_document_values()
        as_payroll = self._as(payroll_user)["hr.contract"].browse(contract.id)
        self.assertEqual(as_payroll._l10n_vn_document_values()["kind"], "labour")

    def test_unreadable_amount_prints_blank(self):
        # a parameter-based base salary without a value on the start date (D4)
        base = self._component(
            "PBASE",
            amount_source="parameter",
            amount_parameter="vn.test.no_such_parameter",
            in_si_base=True,
        )
        contract = self._doc_contract(
            "labour",
            l10n_vn_line_ids=[
                Command.create({"component_id": base.id, "date_from": D(2026, 11, 2)})
            ],
        )
        values = contract._l10n_vn_document_values()
        self.assertIsNone(values["salary"][0]["amount"])
        self.assertEqual(values["salary"][0]["amount_text"], "")
        missing = contract._l10n_vn_document_missing()
        self.assertEqual(len(missing), 1)
        self.assertTrue(missing[0].startswith("TEST_PBASE: "))
        self.assertIn("Mức lương theo công việc hoặc chức danh", self._html(contract))

    def test_unreadable_probation_rate_prints_blank(self):
        # vn.policy.probation_rate starts on 2026-01-01 in the fixtures
        contract = self._doc_contract(
            "labour",
            date_start=D(2025, 12, 1),
            l10n_vn_probation_form="clause",
            trial_date_end=D(2025, 12, 6),
            l10n_vn_probation_job="other",
            l10n_vn_line_ids=[
                Command.create(
                    {"component_id": self.base.id, "amount": 4500000, "date_from": D(2025, 12, 1)}
                )
            ],
        )
        probation = contract._l10n_vn_document_values()["probation"]
        self.assertIsNone(probation["rate"])
        self.assertIsNone(probation["amount"])
        missing = contract._l10n_vn_document_missing()
        self.assertEqual(len(missing), 1)
        self.assertIn("vn.policy.probation_rate", missing[0])
        self.assertIn("Thử việc", self._html(contract))
