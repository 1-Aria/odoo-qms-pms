# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from odoo.addons.l10n_vn_payroll.tests.common import D

from .common import AdvanceCase


@tagged("post_install", "-at_install")
class TestAdvance(AdvanceCase):
    # ------------------------------------------------------------------ the limit (D2, D3)
    def test_limit_figures(self):
        other = self._component("ADV_OTHER", section="other", proration="none")
        self._line(self.skill, contract=self.alice_contract, amount=1500000)
        self._line(other, contract=self.alice_contract, amount=200000)
        self._line(self.daily, contract=self.alice_contract, amount=200000)
        advance = self._advance(self.alice, 100000)
        self.assertTrue(advance.eligible)
        self.assertAlmostEqual(advance.days_worked, 13)
        self.assertEqual(advance.monthly_amount, 6000000)
        self.assertEqual(advance.earned_amount, 3000000)
        self.assertEqual(advance.limit_left, 1500000)
        self.assertFalse(advance.over_limit)

    def test_earned_to_date(self):
        early = self._advance(self.alice, 100000, D(2026, 10, 8))
        self.assertAlmostEqual(early.days_worked, 6)
        self.assertEqual(early.earned_amount, 1038462)
        self.assertEqual(early.limit_left, 519231)
        first = self._advance(self.alice, 100000, D(2026, 10, 1))
        self.assertEqual((first.days_worked, first.earned_amount, first.limit_left), (0, 0, 0))

    def test_other_advances_reduce_limit(self):
        self._advance(self.alice, 300000, D(2026, 10, 5), state="approved")
        self._paid_advance(self.alice, 200000, D(2026, 10, 20))
        self._advance(self.alice, 300000, D(2026, 10, 6))
        self._advance(self.alice, 400000, D(2026, 10, 7), state="cancelled")
        self._advance(self.alice, 600000, D(2026, 11, 5), state="approved")
        advance = self._advance(self.alice, 100000)
        self.assertEqual(advance.limit_left, 625000)

    def test_within_limit(self):
        advance = self._advance(self.alice, 1000000)
        self._advances(self.reviewer).browse(advance.id).action_approve()
        self.assertEqual(advance.state, "approved")
        self.assertEqual(advance.approved_by, self.reviewer)
        self.assertTrue(advance.approved_at)
        self.assertEqual(advance.limit_at_approval, 1125000)

    def test_above_limit_needs_note(self):
        advance = self._advance(self.alice, 1500000)
        self.assertTrue(advance.over_limit)
        as_reviewer = self._advances(self.reviewer).browse(advance.id)
        with self.assertRaises(UserError) as caught:
            as_reviewer.action_approve()
        self.assertIn(self.alice.name, str(caught.exception))
        self.assertEqual(advance.state, "draft")
        as_reviewer.limit_note = "Hospital bill"
        as_reviewer.action_approve()
        self.assertEqual(advance.state, "approved")

    def test_level_off(self):
        self._parameter_text("vn.check.advance_limit", "off")
        advance = self._advance(self.alice, 2500000)
        self.assertFalse(advance.over_limit)
        self._advances(self.reviewer).browse(advance.id).action_approve()
        self.assertEqual(advance.state, "approved")

    def test_level_error(self):
        self._parameter_text("vn.check.advance_limit", "error")
        advance = self._advance(self.alice, 2500000, limit_note="Hospital bill")
        with self.assertRaises(UserError):
            self._advances(self.reviewer).browse(advance.id).action_approve()
        self.assertEqual(advance.state, "draft")

    def test_not_eligible(self):
        self.bao_contract.l10n_vn_pay_group = "office"
        carl, _contract = self._hire(lines=[(self.sal, {"amount": 4500000})])
        advances = (
            self._advance(self.alice, 100000)
            | self._advance(self.bao, 100000, limit_note="Agreed")
            | self._advance(carl, 100000, limit_note="Agreed")
        )
        self.assertEqual(advances.mapped("eligible"), [True, False, False])
        with self.assertRaises(UserError) as caught:
            self._advances(self.reviewer).browse(advances.ids).action_approve()
        self.assertIn(self.bao.name, str(caught.exception))
        self.assertIn(carl.name, str(caught.exception))
        self.assertEqual(set(advances.mapped("state")), {"draft"})

    def test_eligibility_by_month(self):
        # a worker in October, office staff from November (D18)
        self.alice_contract.date_end = D(2026, 10, 31)
        self._hire(
            employee=self.alice,
            date_start=D(2026, 11, 1),
            lines=[(self.sal, {"amount": 4500000})],
            l10n_vn_pay_group="office",
        )
        october = self._advance(self.alice, 1000000)
        november = self._advance(self.alice, 100000, D(2026, 11, 16), limit_note="Agreed")
        self.assertTrue(october.eligible)
        self.assertFalse(november.eligible)
        as_reviewer = self._advances(self.reviewer)
        as_reviewer.browse(october.id).action_approve()
        self.assertEqual(october.state, "approved")
        with self.assertRaises(UserError):
            as_reviewer.browse(november.id).action_approve()
        self.assertEqual(november.state, "draft")

    def test_eligible_at_zero_limit(self):
        advance = self._advance(self.alice, 100000, D(2026, 10, 1))
        self.assertTrue(advance.eligible)
        self.assertTrue(advance.over_limit)
        as_reviewer = self._advances(self.reviewer).browse(advance.id)
        with self.assertRaises(UserError):
            as_reviewer.action_approve()
        as_reviewer.limit_note = "First days of the month"
        as_reviewer.action_approve()
        self.assertEqual((advance.state, advance.limit_at_approval), ("approved", 0))

    def test_missing_parameter(self):
        self.env["base.time.parameter"].search(
            [("code", "=", "vn.policy.advance_max_share"), ("company_id", "=", self.company.id)]
        ).unlink()
        advance = self._advance(self.alice, 2500000)
        self.assertEqual((advance.monthly_amount, advance.limit_left), (0, 0))
        self.assertFalse(advance.over_limit)
        with self.assertRaises(UserError):
            self._advances(self.reviewer).browse(advance.id).action_approve()

    # ------------------------------------------------------------------ roles and steps (D1, D10, D11)
    def test_only_reviewer_approves(self):
        advance = self._advance(self.alice, 1000000)
        with self.assertRaises(AccessError):
            self._advances(self.officer).browse(advance.id).action_approve()
        self._advances(self.reviewer).browse(advance.id).action_approve()
        self.assertEqual(advance.state, "approved")

    def test_controlled_fields(self):
        advance = self._advance(self.alice, 1000000)
        as_officer = self._advances(self.officer).browse(advance.id)
        as_officer.amount = 900000
        self.assertEqual(advance.amount, 900000)
        with self.assertRaises(AccessError):
            as_officer.write({"state": "approved"})
        with self.assertRaises(AccessError):
            self._advances(self.officer).create(
                {"employee_id": self.alice.id, "date": D(2026, 10, 15), "amount": 1000,
                 "reason": "Test", "state": "paid"}
            )

    def test_frozen_after_draft(self):
        advance = self._advance(self.alice, 1000000, state="approved")
        with self.assertRaises(UserError):
            self._advances(self.officer).browse(advance.id).write({"amount": 900000})
        self.assertEqual(advance.amount, 1000000)

    def test_mark_paid(self):
        draft = self._advance(self.alice, 1000000)
        approved = self._advance(self.bao, 1000000, state="approved")
        Advances = self._advances(self.officer)
        with self.assertRaises(UserError):
            Advances.browse(draft.id).action_open_pay()
        with self.assertRaises(UserError):
            Advances.browse(draft.id)._l10n_vn_mark_paid(D(2026, 10, 16))
        action = Advances.browse((draft | approved).ids).action_open_pay()
        wizard = (
            self._as(self.officer)["l10n_vn.payroll.advance.pay"]
            .with_context(action["context"])
            .create({"paid_date": D(2026, 10, 16)})
        )
        self.assertEqual(wizard.advance_ids, approved)
        wizard.action_confirm()
        self.assertEqual((approved.state, approved.paid_date), ("paid", D(2026, 10, 16)))
        self.assertEqual(draft.state, "draft")

    def test_cancel(self):
        draft = self._advance(self.alice, 1000000)
        approved = self._advance(self.alice, 500000, state="approved")
        paid = self._paid_advance(self.bao, 1000000)
        Advances = self._advances(self.officer)
        Advances.browse((draft | approved).ids).action_cancel()
        self.assertEqual(set((draft | approved).mapped("state")), {"cancelled"})
        with self.assertRaises(AccessError):
            Advances.browse(paid.id).action_cancel()
        self._advances(self.reviewer).browse(paid.id).action_cancel()
        self.assertEqual(paid.state, "cancelled")
        with self.assertRaises(UserError):
            self._advances(self.reviewer).browse(paid.id).action_cancel()

    def test_unlink_draft_only(self):
        draft = self._advance(self.alice, 1000000)
        approved = self._advance(self.alice, 500000, state="approved")
        Advances = self._advances(self.officer)
        Advances.browse(draft.id).unlink()
        self.assertFalse(draft.exists())
        with self.assertRaises(UserError):
            Advances.browse(approved.id).unlink()

    def test_read_roles(self):
        advance = self._advance(self.alice, 1000000)
        vals = {"employee_id": self.alice.id, "date": D(2026, 10, 15), "amount": 1000,
                "reason": "Test"}
        for user in (self.reader, self.approver):
            self.assertEqual(self._advances(user).browse(advance.id).amount, 1000000)
            with self.assertRaises(AccessError):
                self._advances(user).create(dict(vals))
        self.assertTrue(self._advances(self.officer).create(dict(vals)))

    def test_company_rule(self):
        other = self.env["res.company"].create({"name": "Advance Test Other Company"})
        employee = self.env["hr.employee"].create(
            {"name": "Advance Test Other Employee", "company_id": other.id}
        )
        advance = self.env["l10n_vn.payroll.advance"].create(
            {"employee_id": employee.id, "company_id": other.id, "date": D(2026, 10, 15),
             "amount": 1000, "reason": "Test"}
        )
        Advances = self._advances(self.officer)
        self.assertFalse(Advances.search([("id", "=", advance.id)]))
        self.assertTrue(Advances.search([("id", "=", self._advance(self.alice, 1000).id)]))
