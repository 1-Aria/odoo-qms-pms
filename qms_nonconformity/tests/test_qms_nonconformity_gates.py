# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNonconformityGates(TransactionCase):
    """The three gates OCA enforces, each behind a company switch.

    post_install: the fixtures create a nonconformity, a model later modules
    extend. The switches are written on the company directly; the settings form
    is a view over the same fields.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.stage_open = cls.env.ref("mgmtsystem_nonconformity.stage_open")
        cls.stage_done = cls.env.ref("mgmtsystem_nonconformity.stage_done")
        # is_ending = False, so a nonconformity holding this action cannot close
        # while the actions gate is on.
        cls.action_stage_open = cls.env.ref("mgmtsystem_action.stage_draft")

    def _nonconformity(self, **values):
        user = self.env.user
        values.setdefault("description", "Gates")
        values.setdefault("responsible_user_id", user.id)
        values.setdefault("manager_user_id", user.id)
        values.setdefault("user_id", user.id)
        return self.env["mgmtsystem.nonconformity"].create(values)

    def _open_action(self, nonconformity):
        return self.env["mgmtsystem.action"].create(
            {
                "name": "Still running",
                "type_action": "correction",
                "stage_id": self.action_stage_open.id,
                "nonconformity_ids": [(4, nonconformity.id)],
            }
        )

    # -- action plan comments, at In Progress ------------------------------

    def test_action_comments_required_by_default(self):
        nonconformity = self._nonconformity()
        with self.assertRaises(ValidationError):
            nonconformity.stage_id = self.stage_open

    def test_action_comments_gate_off(self):
        self.company.qms_require_action_plan_comments = False
        nonconformity = self._nonconformity()
        nonconformity.stage_id = self.stage_open
        self.assertEqual(nonconformity.state, "open")

    # -- evaluation comments, at Closed -----------------------------------

    def test_evaluation_comments_required_by_default(self):
        nonconformity = self._nonconformity()
        with self.assertRaises(ValidationError):
            nonconformity.stage_id = self.stage_done

    def test_evaluation_comments_gate_off(self):
        self.company.qms_require_evaluation_comments = False
        nonconformity = self._nonconformity()
        nonconformity.stage_id = self.stage_done
        self.assertEqual(nonconformity.state, "done")

    # -- all actions done, at Closed --------------------------------------

    def test_actions_done_required_by_default(self):
        nonconformity = self._nonconformity(evaluation_comments="Effective")
        self._open_action(nonconformity)
        with self.assertRaises(ValidationError):
            nonconformity.stage_id = self.stage_done

    def test_actions_done_gate_off(self):
        self.company.qms_require_actions_done = False
        nonconformity = self._nonconformity(evaluation_comments="Effective")
        self._open_action(nonconformity)
        nonconformity.stage_id = self.stage_done
        self.assertEqual(nonconformity.state, "done")

    def test_settings_form_writes_the_company(self):
        """The settings round trip, which the storage choice turns on.

        The first version of this step stored the switches in
        ir.config_parameter. That cannot hold a default-on switch: settings write
        a False Boolean as set_param(key, False), and set_param deletes a
        parameter whose value is falsy
        (base/models/ir_config_parameter.py:91-98), so get_param returned the
        default and the gate read as on again. This test is what would have
        caught it.
        """
        settings = self.env["res.config.settings"].create(
            {"qms_require_action_plan_comments": False}
        )
        settings.execute()
        self.assertFalse(self.company.qms_require_action_plan_comments)

        settings = self.env["res.config.settings"].create(
            {"qms_require_action_plan_comments": True}
        )
        settings.execute()
        self.assertTrue(self.company.qms_require_action_plan_comments)

    def test_gates_are_independent(self):
        """Why the override restates both checks instead of calling super().

        OCA enforces the comment and the actions in one method, so delegating
        could only keep or skip the pair.
        """
        self.company.qms_require_evaluation_comments = False
        self.company.qms_require_actions_done = True
        with_action = self._nonconformity()
        self._open_action(with_action)
        with self.assertRaises(ValidationError):
            with_action.stage_id = self.stage_done

        self.company.qms_require_evaluation_comments = True
        self.company.qms_require_actions_done = False
        no_comment = self._nonconformity()
        self._open_action(no_comment)
        with self.assertRaises(ValidationError):
            no_comment.stage_id = self.stage_done
