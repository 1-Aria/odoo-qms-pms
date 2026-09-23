# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestActionInspection(TransactionCase):
    """The action to inspection link, and the inspection's three-path count.

    post_install: the fixtures create a product, nonconformities and users.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prefix = unique_code_prefix()

        # One qualitative question is enough: the link does not care what the
        # inspection found.
        cls.test = cls.env["qc.test"].create(
            {
                "name": "Shirt inspection",
                "test_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Fabric intact?",
                            "type": "qualitative",
                            "ql_values": [(0, 0, {"name": "Yes", "ok": True})],
                        },
                    )
                ],
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Shirt"})
        cls.inspection = cls._inspection()
        cls.other_inspection = cls._inspection()

        cls.nonconformity = cls._nonconformity(inspection=cls.inspection)
        cls.other_nonconformity = cls._nonconformity(inspection=cls.other_inspection)
        cls.loose_nonconformity = cls._nonconformity()

    @classmethod
    def _inspection(cls, state="failed"):
        inspection = cls.env["qc.inspection"].create(
            {
                "object_id": f"product.product,{cls.product.id}",
                "test": cls.test.id,
            }
        )
        if state != "draft":
            inspection.state = state
        return inspection

    @classmethod
    def _nonconformity(cls, inspection=None):
        user = cls.env.user
        return cls.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Action link",
                "origin_ids": [
                    (6, 0, cls.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
                "qc_inspection_id": inspection and inspection.id or False,
            }
        )

    def _action(self, **values):
        values.setdefault("name", "Rework the sleeve")
        values.setdefault("type_action", "correction")
        return self.env["mgmtsystem.action"].create(values)

    def _user(self, *group_refs):
        return self.env["res.users"].create(
            {
                "name": "Test user",
                "login": f"{self.prefix.lower()}-{len(group_refs)}-{group_refs[-1]}",
                "groups_id": [
                    (
                        6,
                        0,
                        [self.env.ref(ref).id for ref in ("base.group_user",) + group_refs],
                    )
                ],
            }
        )

    # -- the three arms ---------------------------------------------------

    def test_direct_action_counts(self):
        action = self._action(qms_inspection_id=self.inspection.id)
        self.assertEqual(self.inspection.qms_action_ids, action)
        self.assertEqual(self.inspection.qms_action_count, 1)
        self._action(qms_inspection_id=self.inspection.id)
        self.assertEqual(self.inspection.qms_action_count, 2)

    def test_generated_action_counts(self):
        """What Generate Actions writes: a link to the nonconformity only."""
        action = self._action(nonconformity_ids=[(4, self.nonconformity.id)])
        self.assertFalse(action.qms_inspection_id)
        self.assertFalse(self.inspection.qms_action_ids)
        self.assertEqual(self.inspection.qms_action_count, 1)

    def test_immediate_action_counts(self):
        action = self._action()
        self.nonconformity.immediate_action_id = action
        self.assertNotIn(action, self.nonconformity.action_ids)
        self.assertEqual(self.inspection.qms_action_count, 1)

    def test_action_on_unrelated_nonconformity_does_not_count(self):
        self._action(nonconformity_ids=[(4, self.loose_nonconformity.id)])
        self._action(nonconformity_ids=[(4, self.other_nonconformity.id)])
        self.assertEqual(self.inspection.qms_action_count, 0)
        self.assertEqual(self.other_inspection.qms_action_count, 1)

    def test_action_reachable_twice_counts_once(self):
        self._action(
            qms_inspection_id=self.inspection.id,
            nonconformity_ids=[(4, self.nonconformity.id)],
        )
        self.assertEqual(self.inspection.qms_action_count, 1)

    def test_count_zero(self):
        self.assertEqual(self.inspection.qms_action_count, 0)

    def test_count_refreshes_within_transaction(self):
        """What the @api.depends list buys.

        A search_count has no dependency path of its own, so without the three
        declared paths the first read would be cached and never invalidated.
        """
        self.assertEqual(self.inspection.qms_action_count, 0)
        self._action(qms_inspection_id=self.inspection.id)
        self.assertEqual(self.inspection.qms_action_count, 1)
        self._action(nonconformity_ids=[(4, self.nonconformity.id)])
        self.assertEqual(self.inspection.qms_action_count, 2)
        self.nonconformity.immediate_action_id = self._action()
        self.assertEqual(self.inspection.qms_action_count, 3)

    # -- the window actions -----------------------------------------------

    def test_view_actions_domain_and_context(self):
        result = self.inspection.action_view_qms_actions()
        self.assertEqual(result["res_model"], "mgmtsystem.action")
        self.assertEqual(result["view_mode"], "list,form")
        self.assertEqual(result["domain"], self.inspection._qms_action_domain())
        self.assertEqual(
            result["context"]["default_qms_inspection_id"], self.inspection.id
        )

    def test_view_inspection_res_id(self):
        action = self._action(qms_inspection_id=self.inspection.id)
        result = action.action_view_qms_inspection()
        self.assertEqual(result["res_model"], "qc.inspection")
        self.assertEqual(result["res_id"], self.inspection.id)
        self.assertEqual(result["view_mode"], "form")

    def test_draft_inspection_delete_keeps_action(self):
        """An action outlives its source -- ondelete="set null".

        Only a draft inspection can be deleted at all
        (qc_inspection._unlink_except_autogenerated_and_non_draft).
        """
        draft = self._inspection(state="draft")
        action = self._action(qms_inspection_id=draft.id)
        draft.unlink()
        # The FK is cleared in the database; drop the cached value to read it.
        action.invalidate_recordset(["qms_inspection_id"])
        self.assertTrue(action.exists())
        self.assertFalse(action.qms_inspection_id)

    # -- access (D31) -----------------------------------------------------

    def test_combined_groups_read_both_ways(self):
        """The role matrix D31 rests on: both domains, both directions."""
        user = self._user(
            "mgmtsystem.group_mgmtsystem_user",
            "quality_control_oca.group_quality_control_user",
        )
        action = self._action(qms_inspection_id=self.inspection.id)
        self.assertEqual(
            action.with_user(user).qms_inspection_id.state, self.inspection.state
        )
        self.assertEqual(self.inspection.with_user(user).qms_action_count, 1)

    def test_action_form_hides_inspection_without_quality_control(self):
        form = self.env.ref("mgmtsystem_action.view_mgmtsystem_action_form")
        model = self.env["mgmtsystem.action"]
        self.assertIn("qms_inspection_id", model.get_view(form.id, "form")["arch"])
        user = self._user("mgmtsystem.group_mgmtsystem_user")
        arch = model.with_user(user).get_view(form.id, "form")["arch"]
        self.assertNotIn("qms_inspection_id", arch)

    def test_inspection_form_hides_actions_without_mgmtsystem(self):
        """The mirror, and the more exposed of the two.

        It proves this button adds no second failure for such a user; it cannot
        make their form work, because OCA's own ungated nonconformity count
        already breaks it -- see docs/Cross_Module_Access_Policy.md section 6.
        """
        form = self.env.ref("quality_control_oca.qc_inspection_form_view")
        model = self.env["qc.inspection"]
        self.assertIn("qms_action_count", model.get_view(form.id, "form")["arch"])
        user = self._user("quality_control_oca.group_quality_control_user")
        arch = model.with_user(user).get_view(form.id, "form")["arch"]
        self.assertNotIn("qms_action_count", arch)
