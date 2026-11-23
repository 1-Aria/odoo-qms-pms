# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tools import mute_logger

from ..models.l10n_vn_contract_wording import DEFAULT_WORDING
from .common import D, ContractDocumentCase


@tagged("post_install", "-at_install")
class TestDocumentData(ContractDocumentCase):
    def _missing(self, contract):
        contract.invalidate_recordset(["l10n_vn_document_missing"])
        return contract._l10n_vn_document_missing()

    def _label(self, model, name):
        return self.env["ir.model.fields"]._get(model, name).field_description

    def test_print_mode_defaults(self):
        bonus = self._component("BONUS", legal_nature="bonus")
        deduction = self._component("DED", kind="deduction", legal_nature="statutory")
        self.assertEqual(self.base.l10n_vn_contract_print, "amount")
        self.assertEqual(self.prod.l10n_vn_contract_print, "reference")
        self.assertEqual(self.train.l10n_vn_contract_print, "amount")
        self.assertEqual(self.phone.l10n_vn_contract_print, "welfare")
        self.assertEqual(bonus.l10n_vn_contract_print, "welfare")
        self.assertEqual(deduction.l10n_vn_contract_print, "none")
        # an edited mode is kept when an unrelated field changes
        self.train.l10n_vn_contract_print = "none"
        self.train.name = "Training allowance"
        self.assertEqual(self.train.l10n_vn_contract_print, "none")

    def test_print_mode_follows_flags(self):
        component = self._component("FLAG")
        self.assertEqual(component.l10n_vn_contract_print, "amount")
        component.write({"variable": True, "attainment_source": "manager"})
        self.assertEqual(component.l10n_vn_contract_print, "reference")

    def test_work_address_default(self):
        contract = self._doc_contract("labour")
        self.assertEqual(contract.l10n_vn_work_address_id, self.workplace)
        other_place = self.env["res.partner"].create({"name": "Other Factory"})
        other = self.env["hr.employee"].create(
            {"name": "Other Employee", "company_id": self.company.id, "address_id": other_place.id}
        )
        contract.employee_id = other
        self.assertEqual(contract.l10n_vn_work_address_id, other_place)

    def test_missing_none_when_complete(self):
        contract = self._doc_contract("labour")
        self.assertEqual(self._missing(contract), [])
        self.assertFalse(contract.l10n_vn_document_missing)

    def test_missing_lists_employee_fields(self):
        contract = self._doc_contract("labour")
        self.employee.write(
            {
                "birthday": False,
                "l10n_vn_id_issue_place": False,
                "l10n_vn_permanent_address": False,
            }
        )
        self.assertEqual(
            self._missing(contract),
            [
                self._label("hr.employee", "birthday"),
                self._label("hr.employee", "l10n_vn_id_issue_place"),
                self._label("hr.employee", "l10n_vn_permanent_address"),
            ],
        )
        self.assertTrue(contract.l10n_vn_document_missing)

    def test_missing_personal_id_length(self):
        contract = self._doc_contract("labour")
        self.employee.l10n_vn_personal_id = "00119501234"
        self.assertEqual(
            self._missing(contract), ["Personal ID No. (CCCD) must have 12 digits"]
        )

    def test_missing_company_representative(self):
        contract = self._doc_contract("labour")
        self.company.l10n_vn_legal_rep_id = False
        self.assertEqual(
            self._missing(contract), [self._label("res.company", "l10n_vn_legal_rep_id")]
        )

    def test_missing_probation_job(self):
        contract = self._doc_contract(
            "labour", l10n_vn_probation_form="clause", trial_date_end=D(2026, 11, 9)
        )
        self.assertEqual(
            self._missing(contract), [self._label("hr.contract", "l10n_vn_probation_job")]
        )
        contract.l10n_vn_probation_job = "other"
        self.assertEqual(self._missing(contract), [])

    def test_missing_amount_line(self):
        contract = self._doc_contract("labour")
        contract.l10n_vn_line_ids.filtered(lambda line: line.component_id == self.base).unlink()
        self.assertEqual(
            self._missing(contract),
            ["A pay line in force on the start date with an amount in the contract"],
        )

    def test_missing_empty_for_kind_none(self):
        contract = self._doc_contract("none", job_id=False)
        self.employee.birthday = False
        self.assertEqual(self._missing(contract), [])
        self.assertFalse(contract.l10n_vn_document_missing)

    def test_wording_one_per_company(self):
        Wording = self.env["l10n_vn.contract.wording"]
        Wording.create({"company_id": self.company.id})
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            Wording.create({"company_id": self.company.id})
            Wording.flush_model()

    def test_wording_defaults_without_record(self):
        wording = self.env["l10n_vn.contract.wording"]._for_company(self.company)
        self.assertFalse(wording.id)
        self.assertEqual(wording.payday, DEFAULT_WORDING["payday"])
        self.assertIn("nâng bậc", wording.raises)

    def test_warning_shows_approval_limits(self):
        # 2 to 10 November 2026: 8 working days on the Monday-Saturday calendar (D36)
        contract = self._doc_contract(
            "labour",
            l10n_vn_probation_form="clause",
            trial_date_end=D(2026, 11, 10),
            l10n_vn_probation_job="other",
        )
        self.assertEqual(self._missing(contract), [])
        contract.invalidate_recordset(["l10n_vn_document_missing"])
        self.assertIn("longer than the 6", contract.l10n_vn_document_missing)
