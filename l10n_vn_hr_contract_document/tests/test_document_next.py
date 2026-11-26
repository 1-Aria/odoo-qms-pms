# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import D, ContractDocumentCase

EFFECTIVE = D(2027, 1, 1)


@tagged("post_install", "-at_install")
class TestDocumentNext(ContractDocumentCase):
    def _parameter_contracts(self):
        """Two approved contracts on a parameter-based base salary, one on a fixed amount."""
        parameter = self._parameter("vn.test.contract_base", [(D(2026, 1, 1), "4500000")])
        base = self._component(
            "PBASE",
            amount_source="parameter",
            amount_parameter="vn.test.contract_base",
            in_si_base=True,
        )
        def lines():
            return [Command.create({"component_id": base.id, "date_from": D(2026, 11, 2)})]

        first = self._doc_contract("labour", l10n_vn_line_ids=lines())
        second = self._doc_contract(
            "labour", employee_id=self._new_employee("Second").id, l10n_vn_line_ids=lines()
        )
        fixed = self._doc_contract("labour", employee_id=self._new_employee("Fixed").id)
        (first | second | fixed).action_l10n_vn_approve()
        return parameter, first, second, fixed

    def _batch(self, contracts):
        return self.env["l10n_vn.contract.annex.batch.wizard"].create(
            {"date": EFFECTIVE, "contract_ids": [Command.set(contracts.ids)]}
        )

    def _next_wizard(self, contract, **values):
        Wizard = self.env["l10n_vn.contract.next.wizard"].with_context(
            default_contract_id=contract.id
        )
        defaults = Wizard.default_get(["contract_id", "date_start", "contract_type_id", "date_end"])
        return Wizard.create(dict(defaults, **values)), defaults

    def test_annexes_for_date(self):
        parameter, first, second, fixed = self._parameter_contracts()
        parameter.version_ids = [Command.create({"date_from": EFFECTIVE, "value": "5000000"})]
        wizard = self._batch(first | second | fixed)
        wizard.action_find_changes()
        self.assertEqual(wizard.line_ids.contract_id, first | second)
        self.assertIn("salary", wizard.line_ids[0].groups)
        wizard.action_confirm()
        for contract in first | second:
            self.assertEqual(contract.l10n_vn_version_id.kind, "annex")
            self.assertEqual(contract.l10n_vn_version_id.state, "approved")
        self.assertEqual(len(fixed.l10n_vn_version_ids), 1)

    def test_annexes_for_date_skips_open_amendment(self):
        parameter, first, second, fixed = self._parameter_contracts()
        parameter.version_ids = [Command.create({"date_from": EFFECTIVE, "value": "5000000"})]
        first._l10n_vn_amend(EFFECTIVE, "Đang sửa đổi")
        wizard = self._batch(first | second)
        wizard.action_find_changes()
        self.assertEqual(wizard.line_ids.contract_id, second)

    def test_next_contract_after_fixed_term(self):
        contract = self._doc_contract("labour", date_end=D(2027, 11, 1))
        contract.action_l10n_vn_approve()
        wizard, defaults = self._next_wizard(contract)
        self.assertEqual(defaults["date_start"], D(2027, 11, 2))
        self.assertEqual(defaults["contract_type_id"], self.types["labour"].id)
        action = wizard.action_create_contract()
        new = self.env["hr.contract"].browse(action["res_id"])
        self.assertEqual(new.state, "draft")
        self.assertFalse(new.l10n_vn_approved)
        self.assertEqual(
            sorted((line.component_id.code, line.amount, line.date_from) for line in new.l10n_vn_line_ids),
            sorted(
                [
                    (self.base.code, 4500000, D(2027, 11, 2)),
                    (self.prod.code, 500000, D(2027, 11, 2)),
                ]
            ),
        )
        self.assertEqual(contract.date_end, D(2027, 11, 1))

    def test_next_contract_ends_open_contract(self):
        contract = self._doc_contract("labour")
        contract.action_l10n_vn_approve()
        wizard, _defaults = self._next_wizard(contract, date_start=D(2027, 6, 1))
        wizard.action_create_contract()
        self.assertEqual(contract.date_end, D(2027, 5, 31))

    def test_next_contract_after_probation(self):
        probation = self._doc_contract(
            "probation",
            employee_id=self._new_employee("On Probation").id,
            date_end=D(2026, 12, 1),
            l10n_vn_probation_job="college",
        )
        probation.action_l10n_vn_approve()
        wizard, defaults = self._next_wizard(
            probation, contract_type_id=self.types["labour"].id
        )
        self.assertEqual(defaults["date_start"], D(2026, 12, 2))
        default_type = self.env["hr.contract.type"].browse(defaults["contract_type_id"])
        self.assertEqual(default_type.l10n_vn_document_kind, "labour")
        new = self.env["hr.contract"].browse(wizard.action_create_contract()["res_id"])
        self.assertEqual(new.contract_type_id, self.types["labour"])
        self.assertEqual(new.l10n_vn_probation_form, "none")
        self.assertFalse(new.trial_date_end)

    def test_annexes_for_date_in_force_only(self):
        # a contract that ends before the date is not considered; nothing found says so (D54)
        parameter = self._parameter("vn.test.contract_base", [(D(2026, 1, 1), "4500000")])
        base = self._component(
            "PBASE",
            amount_source="parameter",
            amount_parameter="vn.test.contract_base",
            in_si_base=True,
        )
        ended = self._doc_contract(
            "labour",
            date_end=D(2026, 12, 31),
            l10n_vn_line_ids=[
                Command.create({"component_id": base.id, "date_from": D(2026, 11, 2)})
            ],
        )
        ended.action_l10n_vn_approve()
        parameter.version_ids = [Command.create({"date_from": EFFECTIVE, "value": "5000000"})]
        with self.assertRaisesRegex(UserError, "No approved contract"):
            self._batch(ended).action_find_changes()
