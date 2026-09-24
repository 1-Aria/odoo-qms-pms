# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMaintenanceAction(TransactionCase):
    """The action to request link, the count, and its extension point.

    post_install: the fixtures create equipment and users.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.suffix = uuid4().hex[:6]
        cls.equipment = cls.env["maintenance.equipment"].create(
            {"name": f"Sewing machine {cls.suffix}"}
        )
        cls.request = cls._request()

    @classmethod
    def _request(cls):
        return cls.env["maintenance.request"].create(
            {
                "name": "Needle bar seized",
                "equipment_id": cls.equipment.id,
            }
        )

    def _action(self, **values):
        values.setdefault("name", "Replace the needle bar")
        values.setdefault("type_action", "correction")
        return self.env["mgmtsystem.action"].create(values)

    def _user(self, *group_refs):
        return self.env["res.users"].create(
            {
                "name": "Test user",
                "login": f"mma-{self.suffix}-{len(group_refs)}",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref(ref).id
                            for ref in ("base.group_user",) + group_refs
                        ],
                    )
                ],
            }
        )

    # -- the link ---------------------------------------------------------

    def test_link_visible_both_ways(self):
        action = self._action(maintenance_request_id=self.request.id)
        self.assertEqual(self.request.action_ids, action)
        self.assertEqual(self.request.action_count, 1)
        self._action(maintenance_request_id=self.request.id)
        self.assertEqual(self.request.action_count, 2)

    def test_count_zero(self):
        self.assertEqual(self.request.action_count, 0)

    def test_count_refreshes_within_transaction(self):
        """What @api.depends("action_ids") buys a search_count."""
        self.assertEqual(self.request.action_count, 0)
        self._action(maintenance_request_id=self.request.id)
        self.assertEqual(self.request.action_count, 1)

    def test_view_actions_domain_and_context(self):
        result = self.request.action_view_actions()
        self.assertEqual(result["res_model"], "mgmtsystem.action")
        self.assertEqual(result["view_mode"], "list,form")
        self.assertEqual(result["domain"], self.request._action_domain())
        self.assertEqual(
            result["context"]["default_maintenance_request_id"], self.request.id
        )

    def test_request_delete_keeps_action(self):
        """An action outlives its source -- ondelete="set null"."""
        request = self._request()
        action = self._action(maintenance_request_id=request.id)
        request.unlink()
        # The FK is cleared in the database; drop the cached value to read it.
        action.invalidate_recordset(["maintenance_request_id"])
        self.assertTrue(action.exists())
        self.assertFalse(action.maintenance_request_id)

    def test_domain_is_the_extension_point(self):
        """The contract a module adding an arm relies on.

        Widening _action_domain must widen the count, which is why the count is
        a search over the method rather than len(action_ids).
        """
        other = self._action()
        self.assertEqual(self.request.action_count, 0)

        def _wider_domain(request):
            # What an extending module does: the direct arm, plus another.
            return [
                "|",
                ("maintenance_request_id", "=", request.id),
                ("id", "=", other.id),
            ]

        self.patch(
            self.env.registry["maintenance.request"], "_action_domain", _wider_domain
        )
        self.request.invalidate_recordset(["action_count"])
        self.assertEqual(self.request.action_count, 1)

    # -- access (D31) -----------------------------------------------------

    def test_actions_button_hidden_without_mgmtsystem(self):
        """The count reads mgmtsystem.action, so the button needs that group."""
        form = self.env.ref("maintenance.hr_equipment_request_view_form")
        model = self.env["maintenance.request"]
        viewer = self._user("mgmtsystem.group_mgmtsystem_viewer")
        self.assertIn(
            "action_count", model.with_user(viewer).get_view(form.id, "form")["arch"]
        )
        plain = self._user()
        arch = model.with_user(plain).get_view(form.id, "form")["arch"]
        self.assertNotIn("action_count", arch)

    def test_request_form_has_one_button_box(self):
        """The button goes into base_maintenance's box, not a second one.

        Core puts no box on the request form; base_maintenance adds an empty one
        for other modules to fill. This module created its own at first, which
        left the form with two clusters and gave any later
        //div[hasclass('oe_button_box')] xpath two boxes to choose from.
        """
        form = self.env.ref("maintenance.hr_equipment_request_view_form")
        arch = self.env["maintenance.request"].get_view(form.id, "form")["arch"]
        self.assertEqual(arch.count('name="button_box"'), 1)
        self.assertIn("action_count", arch)

    def test_request_field_has_no_group(self):
        """Core grants request read to every internal user, so no gate.

        The negative of the test above: the asymmetry is deliberate, not an
        oversight, and gating this field would hide something that works.
        """
        form = self.env.ref("mgmtsystem_action.view_mgmtsystem_action_form")
        model = self.env["mgmtsystem.action"]
        user = self._user("mgmtsystem.group_mgmtsystem_user")
        arch = model.with_user(user).get_view(form.id, "form")["arch"]
        self.assertIn("maintenance_request_id", arch)
