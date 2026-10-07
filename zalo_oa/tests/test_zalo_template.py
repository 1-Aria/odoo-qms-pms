# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger

MESSAGE_LOGGER = "odoo.addons.zalo_oa.models.zalo_message"


@tagged("post_install", "-at_install")
class TestZaloTemplate(TransactionCase):
    """Templates, the "Send Zalo Message" action, and its isolation rule.

    post_install: the fixtures create partners, a core record later modules
    extend.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env.ref("base.model_res_partner")
        destination = cls.env["zalo.destination"]
        cls.maintenance = destination.create(
            {"name": "Maintenance group", "zalo_id": "G-MAINT"}
        )
        cls.managers = destination.create({"name": "Managers", "zalo_id": "G-MGR"})
        cls.destinations = cls.maintenance | cls.managers
        template = cls.env["zalo.template"]
        cls.template = template.create(
            {
                "name": "New partner",
                "model_id": cls.partner_model.id,
                "body": "New partner {{ object.name }}",
            }
        )
        cls.broken = template.create(
            {
                "name": "Broken",
                "model_id": cls.partner_model.id,
                "body": "New partner {{ object.nmae }}",
            }
        )
        cls.action = cls._action(cls.template)

    def tearDown(self):
        # Creating an automation rule patches create, write and
        # _compute_field_value onto the model class, which the rollback does
        # not undo; core's own tests unregister them the same way
        # (base_automation/tests/test_automation.py:12-14). tearDown runs
        # before Odoo's after-test attribute check.
        self.env["base.automation"]._unregister_hook()
        super().tearDown()

    @classmethod
    def _action(cls, template):
        return cls.env["ir.actions.server"].create(
            {
                "name": f"Zalo: {template.name}",
                "model_id": cls.partner_model.id,
                "state": "zalo",
                "zalo_template_id": template.id,
                "zalo_destination_ids": [(6, 0, cls.destinations.ids)],
            }
        )

    def _run(self, action, partners):
        action.with_context(
            active_model="res.partner",
            active_ids=partners.ids,
            active_id=partners[:1].id,
        ).run()

    def _messages(self, partners):
        return self.env["zalo.message"].search(
            [("res_model", "=", "res.partner"), ("res_id", "in", partners.ids)]
        )

    def _automation(self, action):
        return self.env["base.automation"].create(
            {
                "name": f"Zalo on save: {action.name}",
                "model_id": self.partner_model.id,
                "trigger": "on_create_or_write",
                "action_server_ids": [(6, 0, action.ids)],
            }
        )

    # -- templates and the action ----------------------------------------------

    def test_render(self):
        partner = self.env["res.partner"].create({"name": "Ann"})
        texts = self.template._render_field("body", partner.ids)
        self.assertEqual(texts[partner.id], "New partner Ann")

    def test_action_queues_per_record_and_destination(self):
        partners = self.env["res.partner"].create([{"name": "Ann"}, {"name": "Cy"}])
        self._run(self.action, partners)
        messages = self._messages(partners)
        self.assertEqual(len(messages), 4)
        for partner in partners:
            mine = messages.filtered(lambda message, p=partner: message.res_id == p.id)
            self.assertEqual(mine.destination_id, self.destinations)
            self.assertEqual(set(mine.mapped("text")), {f"New partner {partner.name}"})
            self.assertEqual(mine.template_id, self.template)
            self.assertEqual(set(mine.mapped("state")), {"queued"})

    def test_action_without_destinations(self):
        self.action.zalo_destination_ids = False
        partner = self.env["res.partner"].create({"name": "Ann"})
        self._run(self.action, partner)
        self.assertFalse(self._messages(partner))

    def test_template_model_must_match(self):
        other = self.env["zalo.template"].create(
            {
                "name": "On destinations",
                "model_id": self.env.ref("zalo_oa.model_zalo_destination").id,
                "body": "{{ object.name }}",
            }
        )
        with self.assertRaises(ValidationError):
            self.action.zalo_template_id = other

    # -- isolation -------------------------------------------------------------

    @mute_logger(MESSAGE_LOGGER, "odoo.addons.mail.models.mail_render_mixin")
    def test_broken_template_does_not_block_save(self):
        self._automation(self._action(self.broken))
        partner = self.env["res.partner"].create({"name": "Dee"})
        self.assertTrue(partner.exists())
        messages = self._messages(partner)
        self.assertEqual(messages.destination_id, self.destinations)
        self.assertEqual(set(messages.mapped("state")), {"failed"})
        for message in messages:
            self.assertIn("could not be rendered", message.last_error)

    def test_manual_run_by_a_user(self):
        user = self.env["res.users"].create(
            {
                "name": "Zalo action user",
                "login": "zalo-action-user@example.com",
                # Running a server action checks write access to its model.
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("base.group_partner_manager").id,
                        ],
                    )
                ],
            }
        )
        partner = self.env["res.partner"].create({"name": "Fay"})
        self._run(self.action.with_user(user), partner)
        messages = self._messages(partner)
        self.assertEqual(len(messages), 2)
        self.assertEqual(set(messages.mapped("text")), {"New partner Fay"})

    def test_automation_queues_on_save(self):
        self._automation(self.action)
        partner = self.env["res.partner"].create({"name": "Bob"})
        messages = self._messages(partner)
        self.assertEqual(messages.destination_id, self.destinations)
        self.assertEqual(set(messages.mapped("text")), {"New partner Bob"})

    def test_queue_from_template_flushes_first(self):
        """The caller's own error is the caller's, not swallowed."""
        partner = self.env["res.partner"].create({"name": "Gus"})
        with self.assertRaises(RuntimeError):
            with patch.object(
                type(self.env), "flush_all", side_effect=RuntimeError("caller")
            ):
                self.env["zalo.message"]._queue_from_template(
                    self.template, partner, self.destinations
                )
