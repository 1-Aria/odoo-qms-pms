# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRequestPriority(TransactionCase):
    """The suggestion, and the write-time derivation of priority."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        category = cls.env["maintenance.equipment.category"].create(
            {"name": "Sewing machines", "criticality": "a"}
        )
        minor_category = cls.env["maintenance.equipment.category"].create(
            {"name": "Office equipment", "criticality": "c"}
        )
        equipment = cls.env["maintenance.equipment"]
        cls.critical_machine = equipment.create(
            {"name": "Overlock 1", "category_id": category.id}
        )
        cls.minor_machine = equipment.create(
            {"name": "Printer", "category_id": minor_category.id}
        )

        rule = cls.env["maintenance.priority.rule"]
        # A: stopped line is High, degraded is Normal. C: stopped line is Low.
        cls.rule_a_stopped = rule.create(
            {"criticality": "a", "urgency": "line_stopped", "priority": "3"}
        )
        rule.create({"criticality": "a", "urgency": "degraded", "priority": "2"})
        rule.create({"criticality": "c", "urgency": "line_stopped", "priority": "1"})

    def _request(self, machine=None, **values):
        values.setdefault("name", "Needle bar seized")
        values.setdefault(
            "equipment_id", (machine or self.critical_machine).id
        )
        return self.env["maintenance.request"].create(values)

    # -- the snapshot and the suggestion -----------------------------------

    def test_criticality_snapshot(self):
        request = self._request()
        self.assertEqual(request.criticality, "a")
        # Re-rating the machine leaves the request as it was raised.
        self.critical_machine.criticality = "c"
        self.assertEqual(request.criticality, "a")

    def test_suggestion_from_rules(self):
        request = self._request(urgency="line_stopped")
        self.assertEqual(request.priority_suggested, "3")
        request.urgency = "degraded"
        self.assertEqual(request.priority_suggested, "2")

    # -- the derivation ----------------------------------------------------

    def test_priority_follows_suggestion_on_create(self):
        request = self._request(urgency="line_stopped")
        self.assertEqual(request.priority, "3")

    def test_explicit_priority_on_create_kept(self):
        request = self._request(urgency="line_stopped", priority="0")
        self.assertEqual(request.priority, "0")
        self.assertEqual(request.priority_suggested, "3")

    def test_priority_follows_new_suggestion(self):
        request = self._request(urgency="degraded")
        self.assertEqual(request.priority, "2")
        request.urgency = "line_stopped"
        self.assertEqual(request.priority, "3")

    def test_override_survives_new_suggestion(self):
        """A hand-set priority is not moved when the suggestion changes."""
        request = self._request(urgency="degraded")
        request.priority = "0"
        request.urgency = "line_stopped"
        self.assertEqual(request.priority, "0")
        self.assertEqual(request.priority_suggested, "3")

    def test_reassigned_equipment_moves_priority(self):
        """vals carries only equipment_id, and the priority still follows.

        criticality is a compute on equipment_id, so a trigger list naming
        criticality and urgency would have missed this.
        """
        request = self._request(urgency="line_stopped")
        self.assertEqual(request.priority, "3")
        request.equipment_id = self.minor_machine
        self.assertEqual(request.criticality, "c")
        self.assertEqual(request.priority, "1")

    def test_cleared_priority_is_an_override(self):
        """A blank is a decision, not an absence."""
        request = self._request(urgency="degraded")
        request.priority = False
        request.urgency = "line_stopped"
        self.assertFalse(request.priority)

    def test_no_rules_leaves_priority_alone(self):
        """The unconfigured state, which is every instance before the grid."""
        self.env["maintenance.priority.rule"].search([]).unlink()
        request = self._request(urgency="line_stopped")
        self.assertFalse(request.priority_suggested)
        self.assertFalse(request.priority)
        request.urgency = "degraded"
        self.assertFalse(request.priority)

    def test_priority_override_tracked(self):
        """Tracking needs two precommit runs: create() discards tracking for
        the rest of the transaction, and messages post only at commit."""
        request = self._request(urgency="degraded")
        self.env.cr.precommit.run()
        request.write({"priority": "0", "priority_reason": "Spare on site"})
        self.env.cr.precommit.run()
        request.invalidate_recordset(["message_ids"])
        body = "\n".join(request.message_ids.mapped("body"))
        self.assertIn("Priority", body)
