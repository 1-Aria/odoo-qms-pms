# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from freezegun import freeze_time
from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import tagged
from odoo.tools import SQL

from .test_maintenance_request_sla import RequestSlaCase

T0 = datetime(2026, 1, 5, 8, 0, 0)


def at(hours):
    return T0 + timedelta(hours=hours)


@tagged("post_install", "-at_install")
class TestSlaClock(RequestSlaCase):
    """The clock, driven by stage changes.

    Time is fixed with freeze_time: each request is created at T0 and moved at
    T0 plus a number of hours, so every duration is exact. Response is 1 hour at
    75 %, Restore 8 hours at 50 % pausing in waiting.

    post_install: the fixtures create equipment and requests.
    """

    def _new(self, **values):
        with freeze_time(T0):
            return self._request(**values)

    def _move(self, request, stage, hours):
        with freeze_time(at(hours)):
            request.write({"stage_id": stage.id})

    def _cycles(self, request, rule):
        return self._records(request).filtered(
            lambda record: record.sla_id == rule
        ).sorted("cycle")

    def _stored(self, record, field):
        """The value in the database, not in the cache.

        A field left out of create() is cached as 0.0 while its column is
        NULL, so an ORM read cannot tell a stored 0 from a skipped write.
        """
        self.env.flush_all()
        self.env.cr.execute(
            SQL(
                "SELECT %s FROM maintenance_request_sla WHERE id = %s",
                SQL.identifier(field),
                record.id,
            )
        )
        return self.env.cr.fetchone()[0]

    def _notes(self, request):
        request.invalidate_recordset(["message_ids"])
        return [
            body
            for body in request.message_ids.mapped("body")
            if body and ("SLA test response" in body or "SLA test restore" in body)
        ]

    # -- reaching the target ----------------------------------------------

    def test_target_reached_on_time(self):
        request = self._new()
        self._move(request, self.stage_progress, 0.5)
        response = self._record(request, self.response)
        self.assertEqual(response.state, "achieved")
        self.assertEqual(response.reached_at, at(0.5))
        self.assertAlmostEqual(response.elapsed, 0.5)
        self.assertEqual(self._stored(response, "on_time"), 100.0)
        self.assertFalse(response.deadline)
        # Still below its target: a move between counting stages leaves it be.
        restore = self._record(request, self.restore)
        self.assertEqual(restore.state, "running")
        self.assertEqual(restore.last_change_at, T0)
        self.assertEqual(restore.deadline, at(8))

    def test_target_reached_late(self):
        request = self._new()
        self._move(request, self.stage_progress, 2)
        response = self._record(request, self.response)
        self.assertEqual(response.state, "achieved_late")
        self.assertAlmostEqual(response.elapsed, 2.0)
        self.assertEqual(self._stored(response, "on_time"), 0.0)

    def test_reached_exactly_at_the_deadline(self):
        """The float_compare boundary: thirds of an hour do not sum exactly."""
        request = self._new()
        self._move(request, self.stage_waiting, 1 / 3)
        self._move(request, self.stage_progress, 2 / 3)
        restore = self._record(request, self.restore)
        self.assertEqual(restore.state, "running")
        with freeze_time(restore.deadline):
            request.write({"stage_id": self.stage_restored.id})
        self.assertEqual(restore.state, "achieved")
        self.assertEqual(self._stored(restore, "on_time"), 100.0)

    def test_later_stage_counts_as_reached(self):
        request = self._new()
        self._move(request, self.stage_restored, 3)
        self.assertEqual(self._record(request, self.response).state, "achieved_late")
        self.assertEqual(self._record(request, self.restore).state, "achieved")

    # -- pausing ----------------------------------------------------------

    def test_pause_and_resume(self):
        request = self._new()
        restore = self._record(request, self.restore)
        self._move(request, self.stage_progress, 1)
        self._move(request, self.stage_waiting, 2)
        self.assertEqual(restore.state, "paused")
        self.assertAlmostEqual(restore.consumed, 2.0)
        self.assertFalse(restore.deadline)
        self.assertFalse(restore.risk_at)
        self._move(request, self.stage_progress, 5)
        self.assertEqual(restore.state, "running")
        self.assertAlmostEqual(restore.paused_time, 3.0)
        self.assertEqual(restore.deadline, at(11))
        self.assertEqual(restore.risk_at, at(7))
        self._move(request, self.stage_restored, 6)
        self.assertEqual(restore.state, "achieved")
        self.assertAlmostEqual(restore.elapsed, 3.0)
        self.assertAlmostEqual(restore.paused_time, 3.0)

    def test_clock_at_rest_before_its_start(self):
        """The clamp: nothing counts, running or paused, before start_at."""
        completion = self._make_rule(
            name="SLA test completion",
            maintenance_type="preventive",
            target_stage_id=self.stage_restored.id,
            pause_stage_ids=[Command.set(self.stage_waiting.ids)],
            duration=24.0,
        )
        request = self._new(maintenance_type="preventive", schedule_date=at(48))
        self._move(request, self.stage_waiting, 1)
        self._move(request, self.stage_new, 50)
        record = self._record(request, completion)
        self.assertEqual(record.state, "running")
        self.assertAlmostEqual(record.consumed, 0.0)
        self.assertAlmostEqual(record.paused_time, 2.0)
        self.assertEqual(record.deadline, at(74))

    # -- cancellation -----------------------------------------------------

    def test_cancel_stage_cancels_open_records_only(self):
        request = self._new()
        self._move(request, self.stage_progress, 1)
        self._move(request, self.stage_scrap, 2)
        restore = self._record(request, self.restore)
        self.assertEqual(restore.state, "cancelled")
        self.assertAlmostEqual(restore.consumed, 2.0)
        response = self._record(request, self.response)
        self.assertEqual(response.state, "achieved")
        self.assertEqual(response.reached_at, at(1))

    def test_archiving_cancels_open_records(self):
        request = self._new()
        with freeze_time(at(1)):
            request.archive_equipment_request()
        self.assertEqual(set(self._records(request).mapped("state")), {"cancelled"})

    def test_cancelled_request_cannot_come_back(self):
        scrapped = self._new()
        self._move(scrapped, self.stage_scrap, 1)
        with self.assertRaises(UserError):
            self._move(scrapped, self.stage_new, 2)
        archived = self._new()
        archived.archive_equipment_request()
        with self.assertRaises(UserError):
            archived.reset_equipment_request()

    def test_request_without_records_reopens_freely(self):
        (self.response | self.restore).write({"active": False})
        scrapped = self._new()
        self._move(scrapped, self.stage_scrap, 1)
        self._move(scrapped, self.stage_new, 2)
        self.assertEqual(scrapped.stage_id, self.stage_new)
        archived = self._new()
        archived.archive_equipment_request()
        archived.reset_equipment_request()
        self.assertFalse(archived.archive)

    def test_reopen_hidden_under_sla(self):
        view = self.env.ref("maintenance.hr_equipment_request_view_form")
        arch = self.env["maintenance.request"].get_view(view.id, "form")["arch"]
        button = etree.fromstring(arch).xpath(
            "//button[@name='reset_equipment_request']"
        )[0]
        self.assertEqual(button.get("invisible"), "not archive or sla_ids")

    # -- cycles -----------------------------------------------------------

    def test_rejection_opens_the_next_cycle(self):
        request = self._new()
        self._move(request, self.stage_progress, 1)
        self._move(request, self.stage_restored, 3)
        self._move(request, self.stage_progress, 4)
        first, second = self._cycles(request, self.restore)
        self.assertEqual(first.state, "achieved")
        self.assertEqual(first.reached_at, at(3))
        self.assertEqual(second.cycle, 2)
        self.assertEqual(second.start_at, at(4))
        self.assertEqual(second.state, "running")
        self.assertEqual(second.deadline, at(12))
        # Response is still reached: in progress is its target.
        self.assertEqual(len(self._cycles(request, self.response)), 1)
        # Rejected back to new, below both targets: both open a cycle 2.
        to_new = self._new()
        self._move(to_new, self.stage_progress, 1)
        self._move(to_new, self.stage_restored, 3)
        self._move(to_new, self.stage_new, 4)
        self.assertEqual(self._cycles(to_new, self.response).mapped("cycle"), [1, 2])
        self.assertEqual(self._cycles(to_new, self.restore).mapped("cycle"), [1, 2])

    def test_next_cycle_opens_once(self):
        request = self._new()
        self._move(request, self.stage_progress, 1)
        self._move(request, self.stage_restored, 3)
        self._move(request, self.stage_progress, 4)
        self._move(request, self.stage_waiting, 5)
        self._move(request, self.stage_progress, 6)
        self.assertEqual(len(self._cycles(request, self.restore)), 2)

    def test_next_cycle_follows_the_current_rule(self):
        request = self._new()
        self._move(request, self.stage_progress, 1)
        self._move(request, self.stage_restored, 3)
        stricter = self._make_rule(
            name="SLA test restore, stricter",
            target_stage_id=self.stage_restored.id,
            sequence=1,
            duration=4.0,
        )
        self._move(request, self.stage_progress, 4)
        second = self._records(request).filtered(lambda record: record.cycle == 2)
        self.assertEqual(second.sla_id, stricter)

    def test_outcome_stored_when_met_at_creation(self):
        """A late 0 and a zero-time elapsed reach the database, not only the cache.

        The record is created and finished in one environment, where its
        on_time and elapsed are cached as 0.0 over NULL columns: the case a
        write skipped as unchanged.
        """
        late = self._new(stage_id=self.stage_progress.id, reported_at=at(-2))
        response = self._record(late, self.response)
        self.assertEqual(self._stored(response, "on_time"), 0.0)
        self.assertEqual(self._stored(response, "elapsed"), 2.0)
        instant = self._new(stage_id=self.stage_progress.id)
        response = self._record(instant, self.response)
        self.assertEqual(self._stored(response, "elapsed"), 0.0)
        self.assertEqual(self._stored(response, "on_time"), 100.0)

    def test_reached_at_creation(self):
        request = self._new(stage_id=self.stage_progress.id, reported_at=at(-2))
        response = self._record(request, self.response)
        self.assertEqual(response.state, "achieved_late")
        self.assertAlmostEqual(response.elapsed, 2.0)
        self.assertEqual(response.reached_at, T0)
        self.assertEqual(self._record(request, self.restore).state, "running")

    # -- what does not happen ---------------------------------------------

    def test_unchanged_stage_does_nothing(self):
        request = self._new()
        before = self._records(request).read(["state", "last_change_at", "deadline"])
        self._move(request, self.stage_new, 1)
        self.assertEqual(
            self._records(request).read(["state", "last_change_at", "deadline"]),
            before,
        )
        self.assertFalse(self._notes(request))

    def test_new_rule_not_picked_up_on_stage_change(self):
        request = self._new()
        later = self._make_rule(
            name="SLA test added later", target_stage_id=self.stage_waiting.id
        )
        self._move(request, self.stage_progress, 1)
        self.assertNotIn(later, self._records(request).sla_id)

    # -- the chatter ------------------------------------------------------

    def test_outcomes_posted(self):
        request = self._new()
        self._move(request, self.stage_progress, 2)
        self._move(request, self.stage_waiting, 3)
        self._move(request, self.stage_scrap, 4)
        notes = self._notes(request)
        self.assertEqual(len(notes), 2)
        self.assertTrue(
            any("SLA test response met late: 2:00 of 1:00" in note for note in notes)
        )
        self.assertTrue(any("SLA test restore cancelled" in note for note in notes))

    def test_next_cycle_posted(self):
        request = self._new()
        self._move(request, self.stage_progress, 1)
        self._move(request, self.stage_restored, 3)
        self._move(request, self.stage_progress, 4)
        self.assertTrue(
            any(
                "SLA test restore: cycle 2 started" in note
                for note in self._notes(request)
            )
        )
