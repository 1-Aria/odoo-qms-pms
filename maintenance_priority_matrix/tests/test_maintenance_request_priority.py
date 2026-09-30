# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRequestPriority(TransactionCase):
    """The suggestion, and the write-time derivation of priority."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The instance holds a real, configured grid, and this vocabulary is
        # closed: there are fifteen criticality-urgency pairs and no way to make
        # a fixture pair nobody has used, so the unique_code_prefix() trick that
        # protects the catalog fixtures has no equivalent here. Clearing the
        # table is safe -- a test transaction is rolled back, so the instance's
        # own rows come back untouched -- and it makes the fixtures below the
        # only rules in play.
        cls.env["maintenance.priority.rule"].search([]).unlink()
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
        """An explicit Very Low is a choice, and "0" is truthy."""
        request = self._request(urgency="line_stopped", priority="0")
        self.assertEqual(request.priority, "0")
        self.assertEqual(request.priority_suggested, "3")

    def test_falsy_priority_in_vals_still_fills(self):
        """What the web client actually sends.

        A field on the form but untouched arrives as priority: False, so a guard
        written as "priority" not in vals skipped the fill on every request
        raised from the form -- and the tests missed it by omitting the key,
        which the client never does.
        """
        request = self._request(urgency="line_stopped", priority=False)
        self.assertEqual(request.priority, "3")

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

    # -- the form path ----------------------------------------------------

    def test_onchange_moves_priority_in_the_form(self):
        """The form follows the suggestion, so no reason is demanded for a
        difference the save would have removed anyway."""
        request = self._request(urgency="degraded")
        self.assertEqual(request.priority, "2")

        form = request.new(origin=request)
        form.urgency = "line_stopped"
        form._onchange_priority_follows_suggestion()
        self.assertEqual(form.priority_suggested, "3")
        self.assertEqual(form.priority, "3")

    def test_onchange_leaves_an_override_alone(self):
        request = self._request(urgency="degraded")
        request.priority = "0"

        form = request.new(origin=request)
        form.urgency = "line_stopped"
        form._onchange_priority_follows_suggestion()
        self.assertEqual(form.priority, "0")

    def test_onchange_leaves_an_unsaved_change_alone(self):
        """The term that compares the in-form priority to _origin's.

        Without it, changing urgency after picking a priority by hand would
        overwrite the pick, because _origin still shows the pre-edit pair
        matching.
        """
        request = self._request(urgency="degraded")

        form = request.new(origin=request)
        form.priority = "1"
        form.urgency = "line_stopped"
        form._onchange_priority_follows_suggestion()
        self.assertEqual(form.priority, "1")

    def test_onchange_fills_a_new_record(self):
        """On a new request the priority is filled before the save."""
        form = self.env["maintenance.request"].new(
            {
                "name": "Thread break",
                "equipment_id": self.critical_machine.id,
                "urgency": "line_stopped",
            }
        )
        form._onchange_priority_follows_suggestion()
        self.assertEqual(form.priority, "3")

    def test_priority_form_is_a_plain_selection(self):
        """Not a star, and not required.

        The star is a one-click toggle with no confirmation, too casual for the
        field SLA targets hang off. The requirement was tried and reverted: a
        view requirement is evaluated before the save, while priority is filled
        by create() after it, so requiring the field makes the automatic path
        unreachable and forces a manual pick on every request.
        """
        form = self.env.ref("maintenance.hr_equipment_request_view_form")
        arch = etree.fromstring(
            self.env["maintenance.request"].get_view(form.id, "form")["arch"]
        )
        priority = arch.xpath("//field[@name='priority']")[0]
        self.assertEqual(priority.get("widget"), "selection")
        self.assertIsNone(priority.get("required"))

    def test_reason_requirement_allows_the_unsaved_state(self):
        """The reason must not block the save that fills priority.

        A form expression is evaluated before the save, while create() fills
        priority after it, so on an untouched new record the suggestion already
        differs from an empty priority. The (id or priority) term is what lets
        that save through while still asking for a reason when someone picks a
        priority by hand on a new record.
        """
        form = self.env.ref("maintenance.hr_equipment_request_view_form")
        arch = etree.fromstring(
            self.env["maintenance.request"].get_view(form.id, "form")["arch"]
        )
        reason = arch.xpath("//field[@name='priority_reason']")[0]
        required = reason.get("required")
        self.assertIn("priority_suggested", required)
        self.assertIn("priority != priority_suggested", required)
        self.assertIn("(id or priority)", required)

    def test_priority_fills_on_save_without_being_required(self):
        """The path the requirement blocked: no priority in, suggestion out."""
        request = self.env["maintenance.request"].create(
            {
                "name": "Thread break",
                "equipment_id": self.critical_machine.id,
                "urgency": "line_stopped",
            }
        )
        self.assertEqual(request.priority, "3")

    def test_priority_override_tracked(self):
        """An override and its reason reach the chatter.

        Two precommit runs, as every tracking test in this repository needs:
        create() calls _track_discard, which parks None against the record and
        suppresses tracking for the rest of the transaction, and the tracking
        message itself is written from the same queue, which a test transaction
        never reaches on its own.

        The assertion reads tracking values, not the message body: a tracked
        change carries no body text, it carries mail.tracking.value rows whose
        field_id names the field (mail/models/mail_tracking_value.py:15).
        """
        request = self._request(urgency="degraded")
        self.env.cr.precommit.run()
        before = len(request.message_ids)

        request.write({"priority": "0", "priority_reason": "Spare on site"})
        self.env.cr.precommit.run()
        request.invalidate_recordset(["message_ids"])
        self.assertGreater(len(request.message_ids), before)

        tracked = request.message_ids.tracking_value_ids.mapped("field_id.name")
        self.assertIn("priority", tracked)
        self.assertIn("priority_reason", tracked)
