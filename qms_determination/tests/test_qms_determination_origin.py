# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestDeterminationOrigin(TransactionCase):
    """Origin as the fourth rule condition.

    post_install: the fixtures create nonconformities.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        origin = cls.env["mgmtsystem.nonconformity.origin"]

        group = defect.create({"name": "Fabric Defect", "ref_code": f"{prefix}-FAB"})
        cls.torn = defect.create(
            {"name": "Torn", "ref_code": f"{prefix}-FAB-01", "parent_id": group.id}
        )
        cls.part = cls.env["qms.object.part"].create(
            {"name": f"Sleeves {prefix}", "ref_code": f"{prefix}-SH-03"}
        )
        cls.cause = cls.env["mgmtsystem.nonconformity.cause"].create(
            {"name": f"Machine fault {prefix}"}
        )

        cls.external = origin.create({"name": f"External {prefix}"})
        cls.supplier = origin.create(
            {"name": f"External Supplier {prefix}", "parent_id": cls.external.id}
        )
        cls.audit = origin.create({"name": f"Internal Audit {prefix}"})

        cls.rule_model = cls.env["qms.determination.rule"]

    def _nonconformity(self):
        user = self.env.user
        return self.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Origin conditions",
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
            }
        )

    def _item(self, nonconformity, **values):
        values.setdefault("defect_code_id", self.torn.id)
        values["nonconformity_id"] = nonconformity.id
        return self.env["qms.nonconformity.item"].create(values)

    def test_rule_origin_only_allowed(self):
        """The widened has_condition CHECK."""
        rule = self.rule_model.create(
            {"name": "Supplier defect", "origin_id": self.supplier.id}
        )
        self.assertFalse(rule.defect_code_id)
        self.assertEqual(rule.origin_id, self.supplier)

    def test_matches_on_origin(self):
        rule = self.rule_model.create(
            {"name": "Supplier defect", "origin_id": self.supplier.id}
        )
        nonconformity = self._nonconformity()
        matching = self._item(nonconformity, origin_id=self.supplier.id)
        self.assertIn(rule, self.rule_model._match_item(matching))
        other = self._item(nonconformity, origin_id=self.audit.id)
        self.assertNotIn(rule, self.rule_model._match_item(other))

    def test_matches_origin_group(self):
        """A rule on the group fires for an origin beneath it."""
        rule = self.rule_model.create(
            {"name": "Anything external", "origin_id": self.external.id}
        )
        item = self._item(self._nonconformity(), origin_id=self.supplier.id)
        self.assertIn(rule, self.rule_model._match_item(item))

    def test_item_without_origin_does_not_match(self):
        """An empty item value matches only rules that leave origin empty."""
        origin_rule = self.rule_model.create(
            {"name": "Supplier defect", "origin_id": self.supplier.id}
        )
        any_rule = self.rule_model.create(
            {"name": "Any torn", "defect_code_id": self.torn.id}
        )
        item = self._item(self._nonconformity())
        matched = self.rule_model._match_item(item)
        self.assertNotIn(origin_rule, matched)
        self.assertIn(any_rule, matched)

    def test_four_conditions_together(self):
        rule = self.rule_model.create(
            {
                "name": "All four",
                "defect_code_id": self.torn.id,
                "object_part_id": self.part.id,
                "cause_id": self.cause.id,
                "origin_id": self.supplier.id,
            }
        )
        nonconformity = self._nonconformity()
        complete = self._item(
            nonconformity,
            object_part_id=self.part.id,
            cause_id=self.cause.id,
            origin_id=self.supplier.id,
        )
        self.assertIn(rule, self.rule_model._match_item(complete))
        wrong_origin = self._item(
            nonconformity,
            object_part_id=self.part.id,
            cause_id=self.cause.id,
            origin_id=self.audit.id,
        )
        self.assertNotIn(rule, self.rule_model._match_item(wrong_origin))

    def test_response_line_shows_rule_origin(self):
        self.rule_model.create(
            {"name": "Supplier defect", "origin_id": self.supplier.id}
        )
        nonconformity = self._nonconformity()
        self._item(nonconformity, origin_id=self.supplier.id)
        nonconformity.action_suggest_response()
        self.assertEqual(
            nonconformity.response_ids.mapped("rule_origin_id"), self.supplier
        )

    @mute_logger("odoo.sql_db")
    def test_origin_restrict(self):
        self.rule_model.create({"name": "Audit defect", "origin_id": self.audit.id})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.audit.unlink()
