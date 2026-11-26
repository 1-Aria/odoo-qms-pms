# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import D, ContractDocumentCase

CONTRACT_REPORT = "l10n_vn_hr_contract_document.action_report_contract"
ANNEX_REPORT = "l10n_vn_hr_contract_document.action_report_contract_annex"
EFFECTIVE = D(2027, 1, 1)


@tagged("post_install", "-at_install")
class TestDocumentAmendment(ContractDocumentCase):
    def _html(self, report, records):
        html, _kind = self.env["ir.actions.report"]._render_qweb_html(report, records.ids)
        return html.decode()

    def _approved(self, **values):
        contract = self._doc_contract("labour", **values)
        contract.action_l10n_vn_approve()
        return contract

    def _line(self, contract, component):
        return contract.l10n_vn_line_ids.filtered(lambda line: line.component_id == component)

    def _raise_base(self, contract):
        """End BASE on 2026-12-31 and pay 5,000,000 from 2027-01-01."""
        self._line(contract, self.base).date_to = D(2026, 12, 31)
        self.env["l10n_vn.payroll.contract.line"].create(
            {
                "contract_id": contract.id,
                "component_id": self.base.id,
                "amount": 5000000,
                "date_from": EFFECTIVE,
            }
        )

    def _other_job(self):
        return self.env["hr.job"].create({"name": "Line Leader", "company_id": self.company.id})

    def test_amend_opens(self):
        contract = self._approved(date_end=D(2027, 11, 1))
        version = contract._l10n_vn_amend(EFFECTIVE, "Điều chỉnh tiền lương")
        self.assertEqual(contract.l10n_vn_amendment_id, version)
        self.assertEqual((version.sequence, version.kind, version.state), (1, "annex", "draft"))
        self.assertEqual(version.terms["raw_before"]["job_id"], self.job.id)
        other_job = self._other_job()
        contract.job_id = other_job
        self.assertEqual(contract.job_id, other_job)
        with self.assertRaises(ValidationError):
            contract.date_end = D(2027, 12, 31)
        with self.assertRaises(ValidationError):
            contract.contract_type_id = self.types["probation"]
        with self.assertRaises(ValidationError):
            contract.date_start = D(2026, 11, 3)

    def test_amend_dates(self):
        contract = self._approved(date_end=D(2027, 11, 1))
        with self.assertRaises(UserError):
            contract._l10n_vn_amend(D(2026, 10, 1), "before the start")
        with self.assertRaises(UserError):
            contract._l10n_vn_amend(D(2027, 12, 1), "after the end")
        with patch.object(
            type(self.env["hr.contract"]), "_l10n_vn_paid_until", return_value=D(2026, 12, 31)
        ):
            with self.assertRaisesRegex(UserError, "paid until"):
                contract._l10n_vn_amend(D(2026, 12, 15), "in a paid month")
            contract._l10n_vn_amend(EFFECTIVE, "after the paid months")
        self.assertTrue(contract.l10n_vn_amendment_id)

    def test_amend_needs_manager(self):
        # the line manager reads the contract (positive control) but cannot amend it
        contract = self._approved()
        line_manager = self._user(
            "doc_amend_line_manager", ["hr_contract.group_hr_contract_employee_manager"]
        )
        self.employee.parent_id = self.env["hr.employee"].create(
            {"name": "Line Manager", "user_id": line_manager.id, "company_id": self.company.id}
        )
        as_manager = self._as(line_manager)["hr.contract"].browse(contract.id)
        self.assertEqual(as_manager.name, contract.name)
        with self.assertRaises(AccessError):
            as_manager._l10n_vn_amend(EFFECTIVE, "Điều chỉnh tiền lương")
        self.assertFalse(contract.l10n_vn_amendment_id)

    def test_amendment_pay_lines(self):
        contract = self._approved()
        contract._l10n_vn_amend(EFFECTIVE, "Điều chỉnh tiền lương")
        base_line = self._line(contract, self.base)
        Line = self.env["l10n_vn.payroll.contract.line"]
        with self.assertRaisesRegex(ValidationError, "can only be ended"):
            base_line.amount = 5000000
        with self.assertRaisesRegex(ValidationError, "day before"):
            base_line.date_to = D(2026, 12, 30)
        base_line.date_to = D(2026, 12, 31)
        with self.assertRaisesRegex(ValidationError, "starts on or after"):
            Line.create(
                {
                    "contract_id": contract.id,
                    "component_id": self.base.id,
                    "amount": 5000000,
                    "date_from": D(2026, 12, 15),
                }
            )
        Line.create(
            {
                "contract_id": contract.id,
                "component_id": self.base.id,
                "amount": 5000000,
                "date_from": EFFECTIVE,
            }
        )
        with self.assertRaisesRegex(ValidationError, "not deleted"):
            self._line(contract, self.prod).unlink()

    def test_approve_amendment(self):
        contract = self._approved()
        version = contract._l10n_vn_amend(EFFECTIVE, "Điều chỉnh tiền lương")
        self._raise_base(contract)
        contract.action_l10n_vn_approve_amendment()
        self.assertEqual(version.state, "approved")
        self.assertEqual(version.number, "01/0001/2026/HĐLĐ-TC")
        self.assertEqual(
            [(change["group"], change["number"]) for change in version.terms["changes"]],
            [("salary", 3)],
        )
        self.assertEqual(contract.l10n_vn_version_id, version)
        self.assertFalse(contract.l10n_vn_amendment_id)
        with self.assertRaises(ValidationError):
            contract.job_id = self._other_job()

    def test_approve_amendment_without_change(self):
        contract = self._approved()
        contract._l10n_vn_amend(EFFECTIVE, "Không thay đổi")
        with self.assertRaisesRegex(UserError, "Nothing printed"):
            contract.action_l10n_vn_approve_amendment()

    def test_cancel_amendment(self):
        contract = self._approved()
        contract._l10n_vn_amend(EFFECTIVE, "Điều chỉnh tiền lương")
        contract.job_id = self._other_job()
        self._raise_base(contract)
        contract.action_l10n_vn_cancel_amendment()
        self.assertEqual(contract.job_id, self.job)
        self.assertFalse(self._line(contract, self.base).date_to)
        self.assertEqual(len(contract.l10n_vn_line_ids), 2)
        self.assertEqual(
            self.env["l10n_vn.contract.version"].search_count([("contract_id", "=", contract.id)]),
            1,
        )
        self.assertFalse(contract.l10n_vn_amendment_id)
        with self.assertRaises(ValidationError):
            contract.job_id = self._other_job()

    def test_prints_after_annex(self):
        contract = self._approved()
        version = contract._l10n_vn_amend(EFFECTIVE, "Điều chỉnh tiền lương")
        self._raise_base(contract)
        contract.action_l10n_vn_approve_amendment()
        html = self._html(CONTRACT_REPORT, contract)
        self.assertIn("4.500.000", html)
        self.assertNotIn("5.000.000", html)
        self.assertIn("0001/2026/HĐLĐ-TC", html)
        self.assertEqual(contract.l10n_vn_number, "0001/2026/HĐLĐ-TC")
        annex = self._html(ANNEX_REPORT, version)
        for text in (
            "PHỤ LỤC HỢP ĐỒNG LAO ĐỘNG",
            "01/0001/2026/HĐLĐ-TC",
            "Sửa đổi Điều 3",
            "5.000.000",
            "có hiệu lực kể từ ngày 01/01/2027",
        ):
            self.assertIn(text, annex)
        self.assertNotIn("Sửa đổi Điều 2", annex)

    def test_annex_individual_terms_and_job(self):
        contract = self._approved()
        version = contract._l10n_vn_amend(EFFECTIVE, "Điều chỉnh công việc")
        contract.write(
            {"job_id": self._other_job().id, "l10n_vn_individual_terms": "<p>Xe đưa đón.</p>"}
        )
        contract.action_l10n_vn_approve_amendment()
        annex = self._html(ANNEX_REPORT, version)
        self.assertIn("Sửa đổi Điều 2", annex)
        self.assertIn("Line Leader", annex)
        self.assertIn("Bổ sung Điều 12. Thỏa thuận khác", annex)
        self.assertIn("Xe đưa đón.", annex)

    def test_annex_needs_payroll_group(self):
        contract = self._approved()
        version = contract._l10n_vn_amend(EFFECTIVE, "Điều chỉnh tiền lương")
        self._raise_base(contract)
        contract.action_l10n_vn_approve_amendment()
        # a contract administrator without payroll rights reads the contract (positive
        # control), but neither its versions nor an annex: they hold pay (D53)
        administrator = self._user("doc_annex_admin", ["hr_contract.group_hr_contract_manager"])
        env = self._as(administrator)
        self.assertEqual(env["hr.contract"].browse(contract.id).name, contract.name)
        with self.assertRaises(AccessError):
            env["l10n_vn.contract.version"].browse(version.id).number  # noqa: B018
        with self.assertRaises(AccessError):
            env["l10n_vn.contract.version"].browse(version.id)._l10n_vn_annex_values()
        with self.assertRaises(AccessError):
            env["hr.contract"].browse(contract.id)._l10n_vn_amend(D(2027, 2, 1), "no rights")
