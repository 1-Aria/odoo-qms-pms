# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged

LOGGER = "odoo.addons.maintenance_plan_action_template.models.maintenance_request"


@tagged("post_install", "-at_install")
class TestPlanActionTemplate(TransactionCase):
    """Actions from a plan's templates on the requests it generates.

    post_install: the fixtures create equipment, a plan, requests and a user.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tag = cls.env["mgmtsystem.action.tag"].create({"name": "Plan test tag"})
        templates = cls.env["mgmtsystem.action.template"]
        cls.lubricate = templates.create(
            {
                "name": "Plan test lubricate",
                "type_action": "prevention",
                "description": "<p>Oil the needle bar</p>",
                "tag_ids": [Command.set(cls.tag.ids)],
            }
        )
        cls.belts = templates.create(
            {"name": "Plan test inspect belts", "type_action": "immediate"}
        )
        cls.untyped = templates.create({"name": "Plan test untyped"})
        cls.machine = cls.env["maintenance.equipment"].create(
            {"name": "Plan test machine"}
        )
        cls.plan = cls.env["maintenance.plan"].create(
            {
                "name": "Plan test plan",
                "equipment_id": cls.machine.id,
                "interval": 1,
                "interval_step": "month",
                "maintenance_plan_horizon": 2,
                "planning_step": "month",
                "start_maintenance_date": fields.Date.today(),
                "action_template_ids": [
                    Command.set((cls.lubricate | cls.belts | cls.untyped).ids)
                ],
            }
        )

    def _actions(self, requests):
        return self.env["mgmtsystem.action"].search(
            [("maintenance_request_id", "in", requests.ids)]
        )

    def _generate(self, plan=None):
        plan = plan or self.plan
        plan.button_manual_request_generation()
        return plan.maintenance_ids

    def test_plan_generation_creates_actions(self):
        """The real path O6 depends on: the plan's own generation button."""
        requests = self._generate()
        self.assertTrue(requests)
        for request in requests:
            with self.subTest(request=request.display_name):
                self.assertEqual(
                    self._actions(request).template_id, self.lubricate | self.belts
                )

    def test_action_values(self):
        request = self._generate()[:1]
        action = self._actions(request).filtered(
            lambda action: action.template_id == self.lubricate
        )
        self.assertEqual(action.name, "Plan test lubricate")
        self.assertEqual(action.type_action, "prevention")
        self.assertEqual(action.description, self.lubricate.description)
        self.assertEqual(action.user_id, self.lubricate.user_id)
        self.assertEqual(action.tag_ids, self.tag)
        self.assertEqual(action.date_deadline, request.schedule_date.date())

    def test_template_without_type_skipped(self):
        with self.assertLogs(LOGGER, level="INFO") as logs:
            requests = self._generate()
        self.assertNotIn(self.untyped, self._actions(requests).template_id)
        self.assertTrue(any("Plan test untyped" in line for line in logs.output))

    def test_request_given_a_plan_by_hand(self):
        request = self.env["maintenance.request"].create(
            {
                "name": "Plan test raised by hand",
                "maintenance_type": "preventive",
                "equipment_id": self.machine.id,
                "maintenance_plan_id": self.plan.id,
            }
        )
        self.assertEqual(
            self._actions(request).template_id, self.lubricate | self.belts
        )

    def test_request_without_plan_gets_none(self):
        request = self.env["maintenance.request"].create(
            {"name": "Plan test no plan", "equipment_id": self.machine.id}
        )
        self.assertFalse(self._actions(request))

    def test_plan_set_later_gets_none(self):
        """At creation only (plan D23)."""
        request = self.env["maintenance.request"].create(
            {"name": "Plan test plan set later", "equipment_id": self.machine.id}
        )
        request.maintenance_plan_id = self.plan
        self.assertFalse(self._actions(request))

    def test_generation_outside_the_management_system(self):
        """Created as sudo(): generation works for a user without the group."""
        user = new_test_user(
            self.env,
            login="plan_test_maintenance_manager",
            groups="base.group_user,maintenance.group_equipment_manager",
        )
        # The control: this user cannot create an action directly.
        with self.assertRaises(AccessError):
            self.env["mgmtsystem.action"].with_user(user).create(
                {"name": "Plan test direct", "type_action": "immediate"}
            )
        requests = self._generate(self.plan.with_user(user))
        self.assertTrue(requests)
        self.assertEqual(
            self._actions(requests).template_id, self.lubricate | self.belts
        )
