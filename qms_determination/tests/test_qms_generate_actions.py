# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestGenerateActions(TransactionCase):
    """Generate Actions.

    post_install: the fixtures create nonconformities and actions. A rule on
    the Fabric Defect group carries two templates, Typed and Untyped, so every
    Torn item matches it. A second rule, on Seam Defect, carries Typed only.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        fabric = defect.create({"name": "Fabric Defect", "ref_code": f"{prefix}-FAB"})
        cls.torn = defect.create(
            {"name": "Torn", "ref_code": f"{prefix}-FAB-01", "parent_id": fabric.id}
        )
        seam = defect.create({"name": "Seam Defect", "ref_code": f"{prefix}-SEAM"})
        cls.stitch = defect.create(
            {
                "name": "Broken stitch",
                "ref_code": f"{prefix}-SEAM-01",
                "parent_id": seam.id,
            }
        )

        cls.tag = cls.env["mgmtsystem.action.tag"].create({"name": "Garments"})
        template = cls.env["mgmtsystem.action.template"]
        cls.typed = template.create(
            {
                "name": "Typed",
                "type_action": "prevention",
                "description": "<p>Check the cutting table</p>",
                "user_id": cls.env.user.id,
                "tag_ids": [(6, 0, cls.tag.ids)],
            }
        )
        cls.untyped = template.create({"name": "Untyped"})

        rule = cls.env["qms.determination.rule"]
        cls.fabric_rule = rule.create(
            {
                "name": "Fabric",
                "defect_code_id": fabric.id,
                "action_template_ids": [(6, 0, (cls.typed | cls.untyped).ids)],
            }
        )
        rule.create(
            {
                "name": "Seam",
                "defect_code_id": seam.id,
                "action_template_ids": [(6, 0, cls.typed.ids)],
            }
        )

    def _nonconformity(self, *codes):
        user = self.env.user
        nonconformity = self.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Generate Actions",
                "origin_ids": [
                    (6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
            }
        )
        for code in codes:
            self.env["qms.nonconformity.item"].create(
                {"nonconformity_id": nonconformity.id, "defect_code_id": code.id}
            )
        nonconformity.action_suggest_response()
        return nonconformity

    def _actions(self, nonconformity):
        return self.env["mgmtsystem.action"].search(
            [("nonconformity_ids", "in", nonconformity.ids)]
        )

    def test_one_action_per_typed_template(self):
        nonconformity = self._nonconformity(self.torn)
        nonconformity.action_generate_actions()
        actions = self._actions(nonconformity)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions.template_id, self.typed)
        self.assertIn(actions, nonconformity.action_ids)

    def test_copies_template_fields(self):
        nonconformity = self._nonconformity(self.torn)
        nonconformity.action_generate_actions()
        action = self._actions(nonconformity)
        self.assertEqual(action.name, "Typed")
        self.assertEqual(action.type_action, "prevention")
        self.assertEqual(action.description, self.typed.description)
        self.assertEqual(action.user_id, self.typed.user_id)
        self.assertEqual(action.tag_ids, self.tag)
        self.assertEqual(action.template_id, self.typed)

    def test_untyped_template_skipped(self):
        nonconformity = self._nonconformity(self.torn)
        nonconformity.action_generate_actions()
        self.assertNotIn(self.untyped, self._actions(nonconformity).template_id)

    def test_skipped_templates_notified(self):
        nonconformity = self._nonconformity(self.torn, self.torn)
        result = nonconformity.action_generate_actions()
        self.assertEqual(result["tag"], "display_notification")
        # Named once although two lines carry it.
        self.assertEqual(result["params"]["message"].count("Untyped"), 1)

    def test_nothing_skipped_returns_true(self):
        nonconformity = self._nonconformity(self.stitch)
        self.assertIs(nonconformity.action_generate_actions(), True)
        self.assertEqual(len(self._actions(nonconformity)), 1)

    def test_manual_line_included(self):
        nonconformity = self._nonconformity()
        self.env["qms.nonconformity.response"].create(
            {"nonconformity_id": nonconformity.id, "rule_id": self.fabric_rule.id}
        )
        nonconformity.action_generate_actions()
        self.assertEqual(self._actions(nonconformity).template_id, self.typed)

    def test_two_lines_two_actions(self):
        nonconformity = self._nonconformity(self.torn, self.torn)
        nonconformity.action_generate_actions()
        self.assertEqual(len(self._actions(nonconformity)), 2)

    def test_generate_twice_generates_twice(self):
        # D27, deliberate: no deduplication.
        nonconformity = self._nonconformity(self.torn)
        nonconformity.action_generate_actions()
        nonconformity.action_generate_actions()
        self.assertEqual(len(self._actions(nonconformity)), 2)

    def test_no_lines_no_actions(self):
        nonconformity = self._nonconformity()
        self.assertIs(nonconformity.action_generate_actions(), True)
        self.assertFalse(self._actions(nonconformity))
