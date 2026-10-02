# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from freezegun import freeze_time
from lxml import etree
from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import new_test_user, tagged
from odoo.tools import mute_logger

from .test_maintenance_request_sla import RequestSlaCase
from .test_maintenance_sla_clock import T0, at

OPEN = ("running", "paused")


class RematchCase(RequestSlaCase):
    """Shared helpers on fixed time; no tests of its own."""

    def _new(self, **values):
        with freeze_time(T0):
            return self._request(**values)

    def _write(self, request, hours, **values):
        with freeze_time(at(hours)):
            request.write(values)

    def _notes(self, request, text):
        request.invalidate_recordset(["message_ids"])
        return [
            body
            for body in request.message_ids.mapped("body")
            if body and text in body
        ]


@tagged("post_install", "-at_install")
class TestSlaRematch(RematchCase):
    """Re-matching on request changes, and correcting reported_at.

    post_install: the fixtures create equipment and requests.
    """

    def _urgent(self, **values):
        """A priority-3 rule winning on in progress over the fixture Response."""
        values.setdefault("name", "SLA test urgent response")
        values.setdefault("target_stage_id", self.stage_progress.id)
        values.setdefault("sequence", 1)
        values.setdefault("priority", "3")
        values.setdefault("duration", 0.5)
        return self._make_rule(**values)

    # -- replacing --------------------------------------------------------

    def test_priority_change_replaces_the_record(self):
        urgent = self._urgent()
        request = self._new()
        old = self._record(request, self.response)
        self._write(request, 1, priority="3")
        self.assertEqual(old.state, "cancelled")
        self.assertAlmostEqual(old.consumed, 1.0)
        new = self._record(request, urgent)
        self.assertEqual(new.replaced_id, old)
        self.assertEqual(new.start_at, T0)
        self.assertAlmostEqual(new.consumed, 1.0)
        self.assertEqual(new.cycle, 1)
        self.assertEqual(new.last_change_at, at(1))
        # Half an hour allowed, an hour already counted: overdue at once.
        self.assertEqual(new.deadline, at(0.5))
        self.assertTrue(
            self._notes(
                request, "SLA test response replaced by SLA test urgent response"
            )
        )

    def test_one_open_record_per_target_stage(self):
        urgent = self._urgent()
        request = self._request()
        request.write({"priority": "3"})
        records = self._records(request).filtered(lambda r: r.state in OPEN)
        self.assertEqual(
            records.target_stage_id, self.stage_progress | self.stage_restored
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(
            records.filtered(
                lambda r: r.target_stage_id == self.stage_progress
            ).sla_id,
            urgent,
        )
        names = ["sla_id", "state", "start_at", "deadline", "cycle"]
        before = self._records(request).read(names)
        request._sla_apply()
        self.assertEqual(self._records(request).read(names), before)

    def test_rule_no_longer_matching_cancels(self):
        (self.response | self.restore).write({"active": False})
        team_rule = self._make_rule(
            name="SLA test team A response",
            target_stage_id=self.stage_progress.id,
            team_ids=[Command.set(self.team_a.ids)],
        )
        request = self._new()
        self._write(request, 1, maintenance_team_id=self.team_b.id)
        record = self._record(request, team_rule)
        self.assertEqual(record.state, "cancelled")
        self.assertTrue(self._notes(request, "SLA test team A response cancelled"))

    def test_matching_again_resumes_the_clock(self):
        (self.response | self.restore).write({"active": False})
        team_rule = self._make_rule(
            name="SLA test team A response",
            target_stage_id=self.stage_progress.id,
            team_ids=[Command.set(self.team_a.ids)],
        )
        request = self._new()
        self._write(request, 1, maintenance_team_id=self.team_b.id)
        self._write(request, 3, maintenance_team_id=self.team_a.id)
        cancelled, resumed = self._cycles(request, team_rule)
        self.assertEqual(cancelled.state, "cancelled")
        self.assertEqual(resumed.replaced_id, cancelled)
        self.assertEqual(resumed.start_at, T0)
        # The two hours uncovered count nowhere.
        self.assertAlmostEqual(resumed.consumed, 1.0)
        self.assertEqual(resumed.last_change_at, at(3))
        self.assertTrue(self._notes(request, "SLA test team A response resumed"))

    def _cycles(self, request, rule):
        return self._records(request).filtered(
            lambda record: record.sla_id == rule
        ).sorted("id")

    def test_reassigned_machine_rematches(self):
        category_rule = self._make_rule(
            name="SLA test conveyor response",
            target_stage_id=self.stage_progress.id,
            sequence=1,
            equipment_category_ids=[Command.set(self.category_y.ids)],
        )
        conveyor = self.env["maintenance.equipment"].create(
            {"name": "SLA test conveyor", "category_id": self.category_y.id}
        )
        request = self._new()
        old = self._record(request, self.response)
        self._write(request, 1, equipment_id=conveyor.id)
        self.assertEqual(old.state, "cancelled")
        self.assertEqual(self._record(request, category_rule).replaced_id, old)

    # -- first records ----------------------------------------------------

    def _top_priority_rule(self):
        return self._make_rule(
            name="SLA test top priority",
            target_stage_id=self.stage_waiting.id,
            priority="1",
        )

    def test_newly_matching_rule_creates_a_first_record(self):
        rule = self._top_priority_rule()
        request = self._new()
        self._write(request, 1, priority="1")
        record = self._record(request, rule)
        self.assertEqual(record.cycle, 1)
        self.assertEqual(record.start_at, request.reported_at)

    def test_rule_created_later_gives_no_first_record(self):
        rule = self._top_priority_rule()
        request = self._new()
        # Within a test every record shares the transaction's timestamp, so the
        # rule is made later than the request with SQL.
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE maintenance_sla SET create_date = %s WHERE id = %s",
            [request.create_date + timedelta(hours=1), rule.id],
        )
        self.env.invalidate_all()
        self._write(request, 1, priority="1")
        self.assertNotIn(rule, self._records(request).sla_id)

    # -- what re-matching leaves alone ------------------------------------

    def test_finished_records_untouched(self):
        urgent = self._urgent()
        request = self._new()
        self._write(request, 1, stage_id=self.stage_progress.id)
        response = self._record(request, self.response)
        self._write(request, 2, priority="3")
        self.assertEqual(response.state, "achieved")
        self.assertEqual(response.reached_at, at(1))
        self.assertNotIn(urgent, self._records(request).sla_id)

    def test_dimensions_refreshed_while_open(self):
        request = self._new()
        self._write(request, 1, stage_id=self.stage_progress.id)
        self._write(request, 2, maintenance_team_id=self.team_b.id)
        self.assertEqual(self._record(request, self.restore).team_id, self.team_b)
        self.assertEqual(self._record(request, self.response).team_id, self.team_a)

    def test_domain_read_only_when_rematching(self):
        named = self._make_rule(
            name="SLA test named response",
            target_stage_id=self.stage_progress.id,
            sequence=1,
            domain="[('name', 'ilike', 'urgent')]",
        )
        request = self._new()
        self._write(request, 1, name="SLA test urgent request")
        self.assertNotIn(named, self._records(request).sla_id)
        self._write(request, 2, priority="3")
        self.assertIn(named, self._records(request).sla_id)

    # -- correcting reported_at -------------------------------------------

    def test_reported_at_correction_moves_unchanged_clocks(self):
        request = self._new()
        self._write(request, 0.5, reported_at=at(-1))
        response = self._record(request, self.response)
        restore = self._record(request, self.restore)
        for record in response | restore:
            self.assertEqual(record.start_at, at(-1))
            self.assertEqual(record.last_change_at, at(-1))
        self.assertEqual(restore.deadline, at(7))

    def test_reported_at_correction_leaves_changed_clocks(self):
        request = self._new()
        self._write(request, 1, stage_id=self.stage_progress.id)
        self._write(request, 1.5, reported_at=at(-1))
        response = self._record(request, self.response)
        self.assertEqual(response.start_at, T0)
        self.assertEqual(response.state, "achieved")
        restore = self._record(request, self.restore)
        self.assertEqual(restore.start_at, at(-1))
        self.assertEqual(restore.deadline, at(7))

    def test_reported_at_locked_once_a_record_changes_state(self):
        request = self._new()
        self.assertFalse(request.reported_at_locked)
        self._write(request, 1, stage_id=self.stage_progress.id)
        self.assertTrue(request.reported_at_locked)


@tagged("post_install", "-at_install")
class TestSlaWaiver(RematchCase):
    """Waiving a finished record.

    post_install: the fixtures create users, equipment and requests.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env,
            login="sla_test_waiver_manager",
            groups="base.group_user,maintenance.group_equipment_manager",
        )
        cls.requester = new_test_user(
            cls.env, login="sla_test_waiver_requester", groups="base.group_user"
        )
        cls.reason = cls.env["maintenance.sla.waive.reason"].create(
            {"name": "SLA test power cut"}
        )

    def _late_response(self):
        request = self._new()
        self._write(request, 2, stage_id=self.stage_progress.id)
        return request, self._record(request, self.response)

    def _wizard(self, record, user, **values):
        values.setdefault("reason_id", self.reason.id)
        return (
            self.env["maintenance.request.sla.waive"]
            .with_user(user)
            .create({"sla_record_id": record.id, **values})
        )

    def test_manager_waives_a_finished_record(self):
        request, record = self._late_response()
        self.assertEqual(record.state, "achieved_late")
        with freeze_time(at(3)):
            self._wizard(
                record, self.manager, note="Breaker on line 2"
            ).action_confirm()
        self.assertTrue(record.waived)
        self.assertEqual(record.waive_reason_id, self.reason)
        self.assertEqual(record.waive_note, "Breaker on line 2")
        self.assertEqual(record.waived_by_id, self.manager)
        self.assertEqual(record.waived_at, at(3))
        self.assertTrue(
            self._notes(
                request,
                "SLA test response waived: SLA test power cut — Breaker on line 2",
            )
        )

    @mute_logger("odoo.sql_db")
    def test_waiver_requires_a_reason(self):
        """The ORM has no Python required check: the column's NOT NULL refuses."""
        request, record = self._late_response()
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._wizard(record, self.manager, reason_id=False)

    def test_archived_reason_not_offered(self):
        """name_search is what the wizard's dropdown runs."""
        retired = self.env["maintenance.sla.waive.reason"].create(
            {"name": "SLA test retired reason", "active": False}
        )
        offered = [
            reason_id
            for reason_id, _name in self.env["maintenance.sla.waive.reason"]
            .with_user(self.manager)
            .name_search("SLA test")
        ]
        self.assertIn(self.reason.id, offered)
        self.assertNotIn(retired.id, offered)

    def test_waiver_refused_for_an_open_record(self):
        request, record = self._late_response()
        restore = self._record(request, self.restore)
        self.assertEqual(restore.state, "running")
        with self.assertRaises(UserError):
            self._wizard(restore, self.manager).action_confirm()

    def test_waiver_refused_twice(self):
        request, record = self._late_response()
        self._wizard(record, self.manager).action_confirm()
        with self.assertRaises(UserError):
            self._wizard(record, self.manager).action_confirm()

    def test_waiver_refused_for_a_non_manager(self):
        request, record = self._late_response()
        with self.assertRaises(AccessError):
            self._wizard(record, self.requester)

    def test_waive_hidden_from_non_managers(self):
        view = self.env.ref("maintenance_sla.maintenance_request_sla_view_list")
        records = self.env["maintenance.request.sla"]

        def buttons(user):
            arch = records.with_user(user).get_view(view.id, "list")["arch"]
            return etree.fromstring(arch).xpath("//button[@name='action_waive']")

        self.assertTrue(buttons(self.manager))
        self.assertFalse(buttons(self.requester))
