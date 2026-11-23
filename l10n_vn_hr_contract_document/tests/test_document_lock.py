# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import D, ContractDocumentCase


@tagged("post_install", "-at_install")
class TestDocumentLock(ContractDocumentCase):
    def _approved(self, **values):
        contract = self._doc_contract("labour", **values)
        contract.action_l10n_vn_approve()
        return contract

    def test_switch_refuses_running(self):
        self.company.l10n_vn_contract_approval = True
        draft = self._doc_contract("labour", employee_id=self._new_employee("Draft").id)
        with self.assertRaises(ValidationError):
            draft.state = "open"
        with self.assertRaises(ValidationError):
            self._doc_contract("labour", employee_id=self._new_employee("Open").id, state="open")
        # core's cron skips an Incoming contract that is not approved
        incoming = self._doc_contract(
            "labour", employee_id=self._new_employee("Incoming").id, kanban_state="done"
        )
        with mute_logger("odoo.addons.hr_contract.models.hr_contract"):
            self.env["hr.contract"].with_context(from_cron=True).update_state()
        self.assertEqual(incoming.state, "draft")
        # and opens an approved one on its start date
        start = fields.Date.today() + relativedelta(days=30)
        approved = self._doc_contract(
            "labour",
            employee_id=self._new_employee("Approved Incoming").id,
            date_start=start,
            l10n_vn_line_ids=[
                Command.create({"component_id": self.base.id, "amount": 4500000, "date_from": start})
            ],
        )
        approved.action_l10n_vn_approve()
        self.assertEqual(approved.kanban_state, "done")
        approved.with_context(l10n_vn_contract_unlock=True).date_start = fields.Date.today()
        self.env["hr.contract"].with_context(from_cron=True).update_state()
        self.assertEqual(approved.state, "open")

    def test_switch_off_allows_running(self):
        draft = self._doc_contract("labour", employee_id=self._new_employee("Free").id)
        draft.state = "open"
        self.assertEqual(draft.state, "open")

    def test_lock_terms(self):
        contract = self._approved()
        other_job = self.env["hr.job"].create({"name": "Other Job", "company_id": self.company.id})
        with self.assertRaisesRegex(ValidationError, "is approved"):
            contract.job_id = other_job
        # positive controls: unprinted fields, and the same value again
        other_department = self.env["hr.department"].create(
            {"name": "Other Department", "company_id": self.company.id}
        )
        contract.write({"department_id": other_department.id, "notes": "<p>Moved</p>"})
        contract.write({"job_id": self.job.id})
        self.assertEqual(contract.department_id, other_department)

    def test_lock_superuser(self):
        contract = self._approved()
        other_job = self.env["hr.job"].create({"name": "Other Job", "company_id": self.company.id})
        with self.assertRaises(ValidationError):
            contract.sudo().job_id = other_job

    def test_lock_date_end(self):
        contract = self._approved()
        contract.date_end = D(2027, 6, 30)
        contract.date_end = D(2027, 3, 31)
        self.assertEqual(contract.date_end, D(2027, 3, 31))
        with self.assertRaises(ValidationError):
            contract.date_end = D(2027, 12, 31)
        with self.assertRaises(ValidationError):
            contract.date_end = False

    def test_departure_on_locked(self):
        contract = self._approved()
        self.assertEqual(self.employee.contract_id, contract)
        wizard = (
            self.env["hr.departure.wizard"]
            .with_context(active_id=self.employee.id)
            .create(
                {
                    "employee_id": self.employee.id,
                    "departure_date": D(2026, 12, 15),
                    "set_date_end": True,
                }
            )
        )
        wizard.action_register_departure()
        self.assertEqual(contract.date_end, D(2026, 12, 15))
        self.assertEqual(contract.state, "close")

    def test_pay_lines_locked(self):
        contract = self._approved()
        base_line = contract.l10n_vn_line_ids.filtered(lambda line: line.component_id == self.base)
        prod_line = contract.l10n_vn_line_ids.filtered(lambda line: line.component_id == self.prod)
        Line = self.env["l10n_vn.payroll.contract.line"]
        with self.assertRaises(ValidationError):
            base_line.amount = 5000000
        with self.assertRaises(ValidationError):
            Line.create(
                {
                    "contract_id": contract.id,
                    "component_id": self.base.id,
                    "amount": 5000000,
                    "date_from": D(2027, 1, 1),
                }
            )
        with self.assertRaises(ValidationError):
            base_line.unlink()
        # a level review: the old line ends, a new one starts
        prod_line.date_to = D(2026, 12, 31)
        new_prod = Line.create(
            {
                "contract_id": contract.id,
                "component_id": self.prod.id,
                "amount": 1000000,
                "date_from": D(2027, 1, 1),
            }
        )
        perf = self._component(
            "PERF2", legal_nature="variable_salary", variable=True, attainment_source="manager"
        )
        with self.assertRaises(ValidationError):
            Line.create(
                {
                    "contract_id": contract.id,
                    "component_id": perf.id,
                    "amount": 1000000,
                    "date_from": D(2027, 1, 1),
                }
            )
        new_prod.unlink()
        with self.assertRaises(ValidationError):
            prod_line.unlink()
        Line.create(
            {
                "contract_id": contract.id,
                "component_id": self.phone.id,
                "amount": 200000,
                "date_from": D(2027, 1, 1),
            }
        )

    def test_unapproved_not_locked(self):
        contract = self._doc_contract("labour")
        other_job = self.env["hr.job"].create({"name": "Other Job", "company_id": self.company.id})
        contract.job_id = other_job
        base_line = contract.l10n_vn_line_ids.filtered(lambda line: line.component_id == self.base)
        base_line.amount = 5000000
        self.assertEqual(contract.job_id, other_job)
        self.assertEqual(base_line.amount, 5000000)
