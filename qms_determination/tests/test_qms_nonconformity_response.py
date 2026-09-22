# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestNonconformityResponse(TransactionCase):
    """Matching and Suggest Response.

    post_install: the fixtures create nonconformities, a model later modules
    extend. The rules follow the revised plan's worked example: R1 Torn +
    Sleeves + Machine fault, R2 Torn + Incorrect operation, R3 the Fabric
    Defect group.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        part = cls.env["qms.object.part"]
        cause = cls.env["mgmtsystem.nonconformity.cause"]
        severity = cls.env["mgmtsystem.nonconformity.severity"]

        cls.fabric = defect.create(
            {"name": "Fabric Defect", "ref_code": f"{prefix}-FAB"}
        )
        cls.torn = defect.create(
            {"name": "Torn", "ref_code": f"{prefix}-FAB-01", "parent_id": cls.fabric.id}
        )
        shirt = part.create({"name": "Shirt", "ref_code": f"{prefix}-SHIRT"})
        cls.sleeves = part.create(
            {"name": "Sleeves", "ref_code": f"{prefix}-SH-03", "parent_id": shirt.id}
        )
        cls.machine_fault = cause.create({"name": "Machine fault"})
        cls.operation = cause.create({"name": "Incorrect operation"})
        cls.minor = severity.create({"name": "Minor"})
        cls.major = severity.create({"name": "Major"})

        rule = cls.env["qms.determination.rule"]
        cls.r1 = rule.create(
            {
                "name": "R1",
                "defect_code_id": cls.torn.id,
                "object_part_id": cls.sleeves.id,
                "cause_id": cls.machine_fault.id,
                "severity_id": cls.major.id,
            }
        )
        cls.r2 = rule.create(
            {
                "name": "R2",
                "defect_code_id": cls.torn.id,
                "cause_id": cls.operation.id,
            }
        )
        cls.r3 = rule.create({"name": "R3", "defect_code_id": cls.fabric.id})

    def _nonconformity(self):
        user = self.env.user
        return self.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Suggest Response",
                "origin_ids": [
                    (6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
            }
        )

    def _item(self, nonconformity, **values):
        values.setdefault("defect_code_id", self.torn.id)
        return self.env["qms.nonconformity.item"].create(
            dict(values, nonconformity_id=nonconformity.id)
        )

    def _manual_line(self, nonconformity, rule):
        return self.env["qms.nonconformity.response"].create(
            {"nonconformity_id": nonconformity.id, "rule_id": rule.id}
        )

    def _pairs(self, nonconformity):
        return {(line.item_id, line.rule_id) for line in nonconformity.response_ids}

    def test_worked_example(self):
        nonconformity = self._nonconformity()
        self._item(
            nonconformity,
            object_part_id=self.sleeves.id,
            cause_id=self.machine_fault.id,
        )
        nonconformity.action_suggest_response()
        self.assertEqual(nonconformity.response_ids.rule_id, self.r1 | self.r3)

    def test_partial_item(self):
        # An inspection resolves only a defect code: rules asking for a part
        # or a cause must not fire on it.
        nonconformity = self._nonconformity()
        self._item(nonconformity)
        nonconformity.action_suggest_response()
        self.assertEqual(nonconformity.response_ids.rule_id, self.r3)

    def test_two_items_same_rule(self):
        nonconformity = self._nonconformity()
        first = self._item(nonconformity)
        second = self._item(nonconformity)
        nonconformity.action_suggest_response()
        self.assertEqual(
            self._pairs(nonconformity), {(first, self.r3), (second, self.r3)}
        )

    def test_rerun_replaces_all_lines(self):
        nonconformity = self._nonconformity()
        self._item(nonconformity)
        nonconformity.action_suggest_response()
        suggested = self._pairs(nonconformity)
        manual = self._manual_line(nonconformity, self.r2)
        nonconformity.action_suggest_response()
        self.assertFalse(manual.exists())
        self.assertEqual(self._pairs(nonconformity), suggested)

    def test_no_items_clears_lines(self):
        nonconformity = self._nonconformity()
        self._manual_line(nonconformity, self.r2)
        nonconformity.action_suggest_response()
        self.assertFalse(nonconformity.response_ids)

    def test_item_severity_untouched(self):
        # R1 suggests Major; the item keeps the Minor it was given.
        nonconformity = self._nonconformity()
        item = self._item(
            nonconformity,
            object_part_id=self.sleeves.id,
            cause_id=self.machine_fault.id,
            severity_id=self.minor.id,
        )
        nonconformity.action_suggest_response()
        self.assertIn(self.r1, nonconformity.response_ids.rule_id)
        self.assertEqual(item.severity_id, self.minor)

    def test_archived_group_still_matches(self):
        # The case a parent_of search would miss: the search is filtered by
        # active, so an archived group would drop out of the ancestors.
        self.fabric.active = False
        nonconformity = self._nonconformity()
        self._item(nonconformity)
        nonconformity.action_suggest_response()
        self.assertEqual(nonconformity.response_ids.rule_id, self.r3)

    def test_archived_rule_not_matched(self):
        self.r3.active = False
        nonconformity = self._nonconformity()
        self._item(nonconformity)
        nonconformity.action_suggest_response()
        self.assertFalse(nonconformity.response_ids)

    def test_item_delete_cascades(self):
        nonconformity = self._nonconformity()
        item = self._item(nonconformity)
        nonconformity.action_suggest_response()
        manual = self._manual_line(nonconformity, self.r2)
        item.unlink()
        self.assertEqual(nonconformity.response_ids, manual)

    @mute_logger("odoo.sql_db")
    def test_rule_with_lines_restrict(self):
        nonconformity = self._nonconformity()
        self._item(nonconformity)
        nonconformity.action_suggest_response()
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.r3.unlink()
