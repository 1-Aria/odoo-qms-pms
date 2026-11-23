# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import D, ContractDocumentCase

REPORT = "l10n_vn_hr_contract_document.action_report_contract"


@tagged("post_install", "-at_install")
class TestDocumentApproval(ContractDocumentCase):
    def _html(self, contract):
        html, _kind = self.env["ir.actions.report"]._render_qweb_html(REPORT, contract.ids)
        return html.decode()

    def test_approve_numbers_and_snapshot(self):
        contract = self._doc_contract("labour")
        contract.action_l10n_vn_approve()
        version = contract.l10n_vn_version_id
        self.assertTrue(contract.l10n_vn_approved)
        self.assertEqual(version.state, "approved")
        self.assertEqual(version.sequence, 0)
        self.assertEqual(version.number, "0001/2026/HĐLĐ-TC")
        self.assertEqual(contract.l10n_vn_number, "0001/2026/HĐLĐ-TC")
        self.assertEqual(version.terms["render"]["salary"][0]["amount"], 4500000)
        self.assertEqual(version.terms["raw"]["job_id"], self.job.id)
        self.assertEqual(len(version.terms["raw"]["pay_lines"]), 2)
        self.assertEqual(contract.state, "open")
        self.assertIn("0001/2026/HĐLĐ-TC", contract.message_ids[0].body)

    def test_approve_future_is_incoming(self):
        start = fields.Date.today() + relativedelta(years=1)
        contract = self._doc_contract(
            "labour",
            date_start=start,
            l10n_vn_line_ids=[
                Command.create({"component_id": self.base.id, "amount": 4500000, "date_from": start})
            ],
        )
        contract.action_l10n_vn_approve()
        self.assertEqual(contract.state, "draft")
        self.assertEqual(contract.kanban_state, "done")
        self.assertTrue(contract.l10n_vn_number.startswith(f"0001/{start.year}/"))

    def test_numbers_per_form_and_year(self):
        first = self._doc_contract("labour")
        first.action_l10n_vn_approve()
        second = self._doc_contract("labour", employee_id=self._new_employee("Second").id)
        second.action_l10n_vn_approve()
        self.assertEqual(second.l10n_vn_number, "0002/2026/HĐLĐ-TC")
        probation = self._doc_contract(
            "probation",
            employee_id=self._new_employee("Third").id,
            date_end=D(2026, 12, 1),
            l10n_vn_probation_job="college",
        )
        probation.action_l10n_vn_approve()
        self.assertEqual(probation.l10n_vn_number, "0001/2026/HĐTV-TC")
        later = self._doc_contract(
            "labour",
            employee_id=self._new_employee("Fourth").id,
            date_start=D(2027, 1, 4),
            l10n_vn_line_ids=[
                Command.create(
                    {"component_id": self.base.id, "amount": 4500000, "date_from": D(2027, 1, 4)}
                )
            ],
        )
        later.action_l10n_vn_approve()
        self.assertEqual(later.l10n_vn_number, "0001/2027/HĐLĐ-TC")
        self.company.l10n_vn_contract_code = False
        uncoded = self._doc_contract("labour", employee_id=self._new_employee("Fifth").id)
        uncoded.action_l10n_vn_approve()
        self.assertEqual(uncoded.l10n_vn_number, "0003/2026/HĐLĐ")

    def test_approve_refused_with_missing(self):
        employee = self._new_employee("No Birthday", birthday=False)
        contract = self._doc_contract("labour", employee_id=employee.id)
        with self.assertRaises(UserError) as caught:
            contract.action_l10n_vn_approve()
        self.assertIn(
            self.env["ir.model.fields"]._get("hr.employee", "birthday").field_description,
            caught.exception.args[0],
        )
        self.assertFalse(contract.l10n_vn_approved)
        self.assertFalse(contract.l10n_vn_version_ids)

    def test_approve_refused_beyond_limits(self):
        # 2 to 10 November 2026: 8 working days on the Monday-Saturday calendar
        clause = self._doc_contract(
            "labour",
            l10n_vn_probation_form="clause",
            trial_date_end=D(2026, 11, 10),
            l10n_vn_probation_job="other",
        )
        with self.assertRaisesRegex(UserError, "longer than the 6"):
            clause.action_l10n_vn_approve()
        long_term = self._doc_contract("labour", date_end=D(2029, 12, 1))
        with self.assertRaisesRegex(UserError, "36 months"):
            long_term.action_l10n_vn_approve()
        training = self._doc_contract("training", date_end=D(2027, 3, 1))
        with self.assertRaisesRegex(UserError, "3 months"):
            training.action_l10n_vn_approve()

    def test_approve_kind_none(self):
        contract = self._doc_contract("none", employee_id=self._new_employee("Casual").id)
        contract.action_l10n_vn_approve()
        self.assertTrue(contract.l10n_vn_approved)
        self.assertFalse(contract.l10n_vn_number)
        other_job = self.env["hr.job"].create({"name": "Other Job", "company_id": self.company.id})
        with self.assertRaises(ValidationError):
            contract.job_id = other_job

    def test_approve_needs_manager(self):
        # core's "Employee Manager" contract group is the line manager's: it reads the
        # contracts of the employees it manages (ir_rule_hr_contract_employee_manager)
        contract = self._doc_contract("labour")
        line_manager = self._user(
            "doc_line_manager", ["hr_contract.group_hr_contract_employee_manager"]
        )
        self.employee.parent_id = self.env["hr.employee"].create(
            {"name": "Line Manager", "user_id": line_manager.id, "company_id": self.company.id}
        )
        as_manager = self._as(line_manager)["hr.contract"].browse(contract.id)
        self.assertEqual(as_manager.name, contract.name)
        with self.assertRaises(AccessError):
            as_manager.action_l10n_vn_approve()
        self.assertFalse(contract.l10n_vn_approved)

    def test_approve_selection(self):
        good = self._doc_contract("labour")
        employee = self._new_employee("Missing Birthday", birthday=False)
        bad = self._doc_contract("labour", employee_id=employee.id, name="Bad Contract")
        action = (good | bad).action_l10n_vn_approve()
        self.assertEqual(action["params"]["type"], "warning")
        self.assertIn("Bad Contract", action["params"]["message"])
        self.assertTrue(good.l10n_vn_approved)
        self.assertFalse(bad.l10n_vn_approved)

    def test_print_from_snapshot(self):
        parameter = self._parameter("vn.test.contract_base", [(D(2026, 1, 1), "4500000")])
        base = self._component(
            "PBASE",
            amount_source="parameter",
            amount_parameter="vn.test.contract_base",
            in_si_base=True,
        )
        contract = self._doc_contract(
            "labour",
            l10n_vn_line_ids=[
                Command.create({"component_id": base.id, "date_from": D(2026, 11, 2)})
            ],
        )
        contract.action_l10n_vn_approve()
        parameter.version_ids.value = "5000000"
        html = self._html(contract)
        self.assertIn("4.500.000", html)
        self.assertNotIn("5.000.000", html)
        self.assertIn("0001/2026/HĐLĐ-TC", html)
        self.assertNotIn("BẢN NHÁP", html)
        self.assertEqual(contract._l10n_vn_document_terms()["salary"][0]["amount"], 5000000)

    def test_print_parties_live(self):
        contract = self._doc_contract("labour")
        contract.action_l10n_vn_approve()
        self.employee.l10n_vn_permanent_address = "Ấp 2, xã Mới, An Giang"
        self.assertIn("Ấp 2, xã Mới, An Giang", self._html(contract))

    def test_versions_access(self):
        contract = self._doc_contract("labour")
        contract.action_l10n_vn_approve()
        version = contract.l10n_vn_version_id
        officer = self._user("doc_version_officer", ["hr_contract.group_hr_contract_employee_manager"])
        with self.assertRaises(AccessError):
            self._as(officer)["l10n_vn.contract.version"].browse(version.id).number  # noqa: B018
        payroll_user = self._user("doc_version_payroll", ["payroll.group_payroll_user"])
        self.assertEqual(
            self._as(payroll_user)["l10n_vn.contract.version"].browse(version.id).number,
            version.number,
        )

    def test_copy_unapproved(self):
        contract = self._doc_contract("labour")
        contract.action_l10n_vn_approve()
        copy = contract.copy()
        self.assertFalse(copy.l10n_vn_approved)
        self.assertFalse(copy.l10n_vn_version_ids)
        self.assertFalse(copy.l10n_vn_version_id)
