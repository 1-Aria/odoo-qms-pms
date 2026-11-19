# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D

from .common import AdvanceCase


@tagged("post_install", "-at_install")
class TestBatch(AdvanceCase):
    def setUp(self):
        super().setUp()
        self.bao_contract.l10n_vn_pay_group = "office"

    def _batch(self, **values):
        return self.env["l10n_vn.payroll.advance.batch"].create(
            {"company_id": self.company.id, "date": D(2026, 10, 16), "reason": "Test batch",
             **values}
        )

    def _do(self, user, batch, method):
        return getattr(self._as(user)["l10n_vn.payroll.advance.batch"].browse(batch.id), method)()

    def test_generate_fixed(self):
        batch = self._batch(pay_group="worker", fixed_amount=1000000)
        self._do(self.officer, batch, "action_generate")
        self.assertEqual(batch.advance_ids.employee_id, self.alice)
        self.assertEqual(batch.advance_ids.date, D(2026, 10, 16))
        batch.advance_ids.amount = 900000
        self._do(self.officer, batch, "action_generate")
        self.assertEqual(len(batch.advance_ids), 1)
        self.assertEqual(batch.advance_ids.amount, 900000)

    def test_generate_share(self):
        # a share of pay earned to date: 0.5 x 2,250,000
        self.bao_contract.l10n_vn_pay_group = "worker"
        batch = self._batch(amount_mode="share", share=0.5, round_to=1000)
        self._do(self.officer, batch, "action_generate")
        self.assertEqual(batch.advance_ids.employee_id, self.alice | self.bao)
        self.assertEqual(set(batch.advance_ids.mapped("amount")), {1125000})
        coarse = self._batch(amount_mode="share", share=0.5, round_to=100000)
        self._do(self.officer, coarse, "action_generate")
        self.assertEqual(set(coarse.advance_ids.mapped("amount")), {1100000})

    def test_generate_eligible(self):
        carl, carl_contract = self._hire(
            lines=[(self.sal, {"amount": 4500000})], date_end=D(2026, 10, 10)
        )
        dan, dan_contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        dan_contract.struct_id = False
        (carl_contract | dan_contract).l10n_vn_pay_group = "worker"
        # Bao is in office, outside the eligible pay groups
        batch = self._batch(fixed_amount=1000000)
        self._do(self.officer, batch, "action_generate")
        self.assertEqual(batch.advance_ids.employee_id, self.alice)
        self.assertNotIn(carl, batch.advance_ids.employee_id)
        self.assertNotIn(dan, batch.advance_ids.employee_id)

    def test_approve_and_pay_together(self):
        self.bao_contract.l10n_vn_pay_group = "worker"
        batch = self._batch(fixed_amount=1000000)
        self._do(self.officer, batch, "action_generate")
        self.assertEqual(batch.state, "draft")
        self._do(self.reviewer, batch, "action_approve")
        self.assertEqual(set(batch.advance_ids.mapped("state")), {"approved"})
        self.assertEqual(batch.state, "approved")
        action = self._do(self.officer, batch, "action_create_payment")
        payment = self.env["l10n_vn.payroll.payment"].browse(action["res_id"])
        self.assertEqual(payment.name, batch.name)
        self._pay(payment, "transfer")
        self.assertEqual(set(batch.advance_ids.mapped("state")), {"paid"})
        self.assertEqual(batch.state, "paid")
        self.assertEqual(batch.amount_total, 2000000)

    def test_over_limit_named(self):
        batch = self._batch(pay_group="worker", fixed_amount=1500000)
        self._do(self.officer, batch, "action_generate")
        with self.assertRaises(UserError) as caught:
            self._do(self.reviewer, batch, "action_approve")
        self.assertIn(self.alice.name, str(caught.exception))
        self.assertEqual(batch.state, "draft")
        self._as(self.reviewer)["l10n_vn.payroll.advance"].browse(
            batch.advance_ids.id
        ).limit_note = "Agreed by the director"
        self._do(self.reviewer, batch, "action_approve")
        self.assertEqual(batch.state, "approved")
