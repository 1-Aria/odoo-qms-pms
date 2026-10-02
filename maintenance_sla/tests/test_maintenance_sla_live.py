# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .test_maintenance_sla_clock import T0, at
from .test_maintenance_sla_rematch import RematchCase


@tagged("post_install", "-at_install")
class TestSlaLive(RematchCase):
    """Live state on records and requests, next_deadline, the kanban's order.

    Response is at risk from T0 + 0:45 and overdue from T0 + 1. Live state is
    computed on read, so each reading at a new frozen time invalidates it first.

    post_install: the fixtures create equipment and requests.
    """

    def _live(self, records, hours):
        with freeze_time(at(hours)):
            records.invalidate_recordset(["live_state"])
            return records.mapped("live_state")

    def _request_state(self, request, hours):
        with freeze_time(at(hours)):
            request.sla_ids.invalidate_recordset(["live_state"])
            request.invalidate_recordset(["sla_live_state"])
            return request.sla_live_state

    def _search_records(self, records, hours, operator, value):
        with freeze_time(at(hours)):
            return self.env["maintenance.request.sla"].search(
                [("id", "in", records.ids), ("live_state", operator, value)]
            )

    def _search_requests(self, requests, hours, operator, value):
        with freeze_time(at(hours)):
            return self.env["maintenance.request"].search(
                [("id", "in", requests.ids), ("sla_live_state", operator, value)]
            )

    # -- records ----------------------------------------------------------

    def test_live_state_follows_the_clock(self):
        response = self._record(self._new(), self.response)
        self.assertEqual(self._live(response, 0.5), ["on_track"])
        self.assertEqual(self._live(response, 50 / 60), ["at_risk"])
        self.assertEqual(self._live(response, 70 / 60), ["overdue"])

    def test_live_state_paused_and_finished(self):
        request = self._new()
        self._write(request, 1, stage_id=self.stage_progress.id)
        self._write(request, 2, stage_id=self.stage_waiting.id)
        self.assertEqual(self._live(self._record(request, self.restore), 3), ["paused"])
        self.assertEqual(self._live(self._record(request, self.response), 3), [False])

    def test_live_state_search(self):
        waiting = self._new()
        reached = self._new()
        self._write(reached, 0.5, stage_id=self.stage_progress.id)
        records = self._records(waiting) | self._records(reached)
        at_risk = self._record(waiting, self.response)
        finished = self._record(reached, self.response)
        hours = 50 / 60
        self.assertEqual(self._search_records(records, hours, "=", "at_risk"), at_risk)
        self.assertFalse(self._search_records(records, hours, "=", "overdue"))
        self.assertEqual(
            self._search_records(records, hours, "in", ["at_risk", "overdue"]),
            at_risk,
        )
        self.assertEqual(self._search_records(records, hours, "=", False), finished)
        with self.assertRaises(UserError):
            self._search_records(records, hours, "like", "at")

    def test_negated_search(self):
        """The complement of the positive search, False included."""
        waiting = self._new()
        reached = self._new()
        self._write(reached, 0.5, stage_id=self.stage_progress.id)
        records = self._records(waiting) | self._records(reached)
        at_risk = self._record(waiting, self.response)
        finished = self._record(reached, self.response)
        hours = 50 / 60
        self.assertEqual(
            self._search_records(records, hours, "!=", "at_risk"), records - at_risk
        )
        self.assertEqual(
            self._search_records(records, hours, "not in", ["at_risk", False]),
            records - at_risk - finished,
        )
        # waiting is at risk (its Response), reached on track (its Restore).
        requests = waiting | reached
        self.assertEqual(
            self._search_requests(requests, hours, "!=", "at_risk"), reached
        )
        self.assertEqual(
            self._search_requests(requests, hours, "not in", ["on_track", False]),
            waiting,
        )

    # -- requests ---------------------------------------------------------

    def test_request_shows_the_worst_state(self):
        request = self._new()
        hours = 70 / 60
        # Response overdue, Restore on track.
        self.assertEqual(self._request_state(request, hours), "overdue")
        self.assertEqual(
            self._search_requests(request, hours, "=", "overdue"), request
        )
        self.assertFalse(self._search_requests(request, hours, "=", "at_risk"))

    def test_request_without_open_records(self):
        request = self._new()
        self._write(request, 1, stage_id=self.stage_restored.id)
        self.assertEqual(self._request_state(request, 2), False)
        self.assertEqual(self._search_requests(request, 2, "=", False), request)

    def test_request_paused_when_nothing_runs(self):
        paused = self._new()
        self._write(paused, 1, stage_id=self.stage_progress.id)
        self._write(paused, 2, stage_id=self.stage_waiting.id)
        self.assertEqual(self._request_state(paused, 3), "paused")
        self.assertEqual(self._search_requests(paused, 3, "=", "paused"), paused)
        # A running record beside a paused one: the running state wins.
        stage_done = self.env["maintenance.stage"].create(
            {"name": "SLA test: done", "sequence": 906}
        )
        self._make_rule(
            name="SLA test completion",
            target_stage_id=stage_done.id,
            duration=24.0,
        )
        mixed = self._new()
        self._write(mixed, 1, stage_id=self.stage_waiting.id)
        self.assertEqual(self._request_state(mixed, 2), "on_track")
        self.assertFalse(self._search_requests(mixed, 2, "=", "paused"))

    # -- next_deadline and the board --------------------------------------

    def test_next_deadline_is_the_earliest_running(self):
        request = self._new()
        self.assertEqual(request.next_deadline, at(1))
        self._write(request, 0.5, stage_id=self.stage_progress.id)
        self.assertEqual(request.next_deadline, at(8))
        self._write(request, 1, stage_id=self.stage_waiting.id)
        self.assertFalse(request.next_deadline)
        # Resumed with an hour counted: seven left from +2.
        self._write(request, 2, stage_id=self.stage_progress.id)
        self.assertEqual(request.next_deadline, at(9))
        self._write(request, 3, stage_id=self.stage_restored.id)
        self.assertFalse(request.next_deadline)

    def test_kanban_ordered_by_next_deadline(self):
        view = self.env.ref("maintenance.hr_equipment_request_view_kanban")
        arch = self.env["maintenance.request"].get_view(view.id, "kanban")["arch"]
        self.assertEqual(
            etree.fromstring(arch).get("default_order"), "next_deadline asc, id desc"
        )
