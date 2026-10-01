# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged


class RequestSlaCase(TransactionCase):
    """Shared fixtures; no tests of its own.

    The fixtures archive every active SLA rule first, so the instance's own
    configuration never adds a record to a fixture request. Archived rather than
    deleted: a rule with records cannot be deleted. Urgency and criticality are
    left unset, so maintenance_priority_matrix, where installed, suggests
    nothing and leaves priority as the fixture sets it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["maintenance.sla"].search([]).write({"active": False})
        (
            cls.stage_new,
            cls.stage_progress,
            cls.stage_waiting,
            cls.stage_restored,
            cls.stage_scrap,
        ) = cls.env["maintenance.stage"].create(
            [
                {"name": "SLA test: new", "sequence": 901},
                {"name": "SLA test: in progress", "sequence": 902},
                {"name": "SLA test: waiting", "sequence": 903},
                {"name": "SLA test: restored", "sequence": 904},
                {"name": "SLA test: scrap", "sequence": 905, "sla_cancel": True},
            ]
        )
        cls.team_a, cls.team_b = cls.env["maintenance.team"].create(
            [{"name": "SLA test team A"}, {"name": "SLA test team B"}]
        )
        cls.category_x, cls.category_y = cls.env[
            "maintenance.equipment.category"
        ].create([{"name": "SLA test presses"}, {"name": "SLA test conveyors"}])
        cls.equipment = cls.env["maintenance.equipment"].create(
            {
                "name": "SLA test press",
                "category_id": cls.category_x.id,
                "maintenance_team_id": cls.team_a.id,
            }
        )
        cls.response = cls._make_rule(
            name="SLA test response",
            target_stage_id=cls.stage_progress.id,
            duration=1.0,
        )
        cls.restore = cls._make_rule(
            name="SLA test restore",
            target_stage_id=cls.stage_restored.id,
            pause_stage_ids=[Command.set(cls.stage_waiting.ids)],
            duration=8.0,
            at_risk_pct=50,
        )

    @classmethod
    def _make_rule(cls, **values):
        values.setdefault("maintenance_type", "corrective")
        values.setdefault("duration", 1.0)
        return cls.env["maintenance.sla"].create(values)

    def _request(self, **values):
        values.setdefault("name", "SLA test request")
        values.setdefault("maintenance_type", "corrective")
        values.setdefault("stage_id", self.stage_new.id)
        values.setdefault("equipment_id", self.equipment.id)
        values.setdefault("maintenance_team_id", self.team_a.id)
        values.setdefault("priority", "2")
        return self.env["maintenance.request"].create(values)

    def _records(self, request):
        # Searched rather than read through sla_ids, so the assertions never
        # depend on what the request's one2many cache happens to hold.
        return self.env["maintenance.request.sla"].search(
            [("request_id", "=", request.id)]
        )

    def _record(self, request, rule):
        return self._records(request).filtered(lambda record: record.sla_id == rule)


@tagged("post_install", "-at_install")
class TestRequestSla(RequestSlaCase):
    """Matching at creation, and what each new record carries.

    post_install: the fixtures create equipment and requests.
    """

    def test_records_created_per_target_stage(self):
        records = self._records(self._request())
        self.assertEqual(len(records), 2)
        for rule in (self.response, self.restore):
            record = records.filtered(lambda r, rule=rule: r.sla_id == rule)
            self.assertEqual(record.target_stage_id, rule.target_stage_id)
            self.assertEqual(record.target_sequence, rule.target_stage_id.sequence)
            self.assertEqual(record.duration, rule.duration)
            self.assertEqual(record.at_risk_pct, rule.at_risk_pct)
            self.assertEqual(record.cycle, 1)
            self.assertEqual(record.state, "running")
            self.assertEqual(record.consumed, 0.0)
            self.assertEqual(record.paused_time, 0.0)

    def test_clock_starts_at_reported_at(self):
        request = self._request()
        self.assertEqual(
            self._record(request, self.response).start_at, request.reported_at
        )
        reported = fields.Datetime.now() - timedelta(hours=3)
        request = self._request(reported_at=reported)
        record = self._record(request, self.restore)
        self.assertEqual(record.start_at, reported)
        self.assertEqual(record.deadline, reported + timedelta(hours=8))
        # at_risk_pct 50 of 8 hours: at risk 4 hours before the deadline.
        self.assertEqual(record.risk_at, record.deadline - timedelta(hours=4))

    def test_clock_start_without_reported_at(self):
        request = self._request(reported_at=False)
        self.assertFalse(request.reported_at)
        record = self._record(request, self.response)
        self.assertTrue(record)
        self.assertEqual(record.start_at, request.create_date)

    def test_lowest_sequence_wins(self):
        first = self._make_rule(
            name="SLA test first",
            target_stage_id=self.stage_progress.id,
            sequence=1,
        )
        records = self._records(self._request()).filtered(
            lambda record: record.target_stage_id == self.stage_progress
        )
        self.assertEqual(records.sla_id, first)

    def test_rule_conditions(self):
        """Each condition: a request failing it gets no record, one meeting it does.

        Each conditional rule has sequence 1 and is archived after its sub-test,
        so it never competes with the next one for the target stage.
        """
        equipment_y = self.env["maintenance.equipment"].create(
            {"name": "SLA test conveyor", "category_id": self.category_y.id}
        )
        cases = [
            (
                "type",
                {"maintenance_type": "preventive"},
                {},
                {"maintenance_type": "preventive"},
            ),
            ("priority", {"priority": "3"}, {"priority": "1"}, {"priority": "3"}),
            (
                "team",
                {"team_ids": [Command.set(self.team_b.ids)]},
                {},
                {"maintenance_team_id": self.team_b.id},
            ),
            (
                "category",
                {"equipment_category_ids": [Command.set(self.category_y.ids)]},
                {},
                {"equipment_id": equipment_y.id},
            ),
            (
                "domain",
                {"domain": "[('name', 'ilike', 'urgent')]"},
                {},
                {"name": "SLA test urgent request"},
            ),
        ]
        for label, rule_values, failing, meeting in cases:
            with self.subTest(condition=label):
                rule = self._make_rule(
                    name=f"SLA test {label}",
                    target_stage_id=self.stage_progress.id,
                    sequence=1,
                    **rule_values,
                )
                self.assertNotIn(rule, self._records(self._request(**failing)).sla_id)
                self.assertIn(rule, self._records(self._request(**meeting)).sla_id)
                rule.active = False
        with self.subTest(condition="company"):
            other_company = self.env["res.company"].create(
                {"name": "SLA test other plant"}
            )
            here = self._make_rule(
                name="SLA test here",
                target_stage_id=self.stage_progress.id,
                sequence=1,
                company_id=self.env.company.id,
            )
            elsewhere = self._make_rule(
                name="SLA test elsewhere",
                target_stage_id=self.stage_restored.id,
                sequence=1,
                company_id=other_company.id,
            )
            rules = self._records(self._request()).sla_id
            self.assertIn(here, rules)
            self.assertNotIn(elsewhere, rules)

    def test_empty_priority_collects_only_priority_free_rules(self):
        priced = self._make_rule(
            name="SLA test priced",
            target_stage_id=self.stage_restored.id,
            sequence=1,
            priority="3",
        )
        request = self._request(priority=False)
        self.assertFalse(request.priority)
        rules = self._records(request).sla_id
        self.assertEqual(rules, self.response | self.restore)
        self.assertNotIn(priced, rules)

    def test_paused_at_creation(self):
        record = self._record(
            self._request(stage_id=self.stage_waiting.id), self.restore
        )
        self.assertEqual(record.state, "paused")
        self.assertFalse(record.deadline)
        self.assertFalse(record.risk_at)

    def test_preventive_clock_start(self):
        completion = self._make_rule(
            name="SLA test completion",
            maintenance_type="preventive",
            target_stage_id=self.stage_restored.id,
            duration=24.0,
        )
        scheduled = fields.Datetime.now() + timedelta(days=2)
        request = self._request(maintenance_type="preventive", schedule_date=scheduled)
        record = self._record(request, completion)
        self.assertEqual(record.start_at, scheduled)
        self.assertEqual(record.deadline, scheduled + timedelta(hours=24))
        request = self._request(maintenance_type="preventive")
        self.assertFalse(request.schedule_date)
        self.assertEqual(
            self._record(request, completion).start_at, request.reported_at
        )

    def test_nothing_promised_when_cancelled(self):
        self.assertFalse(self._records(self._request(stage_id=self.stage_scrap.id)))
        self.assertFalse(self._records(self._request(archive=True)))

    def test_no_rules_no_records(self):
        (self.response | self.restore).write({"active": False})
        self.assertFalse(self._records(self._request()))

    def test_apply_twice_changes_nothing(self):
        request = self._request()
        names = ["sla_id", "state", "start_at", "deadline", "risk_at", "cycle"]
        before = self._records(request).read(names)
        request._sla_apply()
        self.assertEqual(self._records(request).read(names), before)

    def test_rule_edit_leaves_records(self):
        record = self._record(self._request(), self.response)
        self.response.write(
            {"duration": 5.0, "target_stage_id": self.stage_restored.id}
        )
        record.invalidate_recordset()
        self.assertEqual(record.duration, 1.0)
        self.assertEqual(record.target_stage_id, self.stage_progress)

    def test_dimensions_copied(self):
        request = self._request()
        record = self._record(request, self.response)
        self.assertEqual(record.team_id, self.team_a)
        self.assertEqual(record.equipment_id, self.equipment)
        self.assertEqual(record.category_id, self.category_x)
        self.assertEqual(record.priority, "2")
        self.assertEqual(record.maintenance_type, "corrective")
        self.assertEqual(record.company_id, request.company_id)

    def test_on_time_stays_null(self):
        """The ORM reads NULL as 0.0, so only SQL can tell them apart."""
        record = self._record(self._request(), self.response)
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT on_time FROM maintenance_request_sla WHERE id = %s", [record.id]
        )
        self.assertIsNone(self.env.cr.fetchone()[0])


@tagged("post_install", "-at_install")
class TestRequestSlaAccess(RequestSlaCase):
    """Who creates, reads and changes the evidence.

    post_install: the fixtures create users, equipment and requests.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.requester = new_test_user(
            cls.env, login="sla_test_requester", groups="base.group_user"
        )
        cls.manager = new_test_user(
            cls.env,
            login="sla_test_manager",
            groups="base.group_user,maintenance.group_equipment_manager",
        )

    def test_requester_creates_records(self):
        """The engine runs as sudo(): the requester has no create right on them.

        No machine: core's equipment rule limits internal users to equipment
        they follow, and core's own computes read the machine as the requesting
        user (maintenance.py:305-310, :313-319).

        The requester is the request's responsible, which is what lets a plain
        internal user create it at all on this stack: see the comment on
        user_id below.
        """
        request = (
            self.env["maintenance.request"]
            .with_user(self.requester)
            .create(
                {
                    "name": "SLA test raised by a requester",
                    "maintenance_type": "corrective",
                    "stage_id": self.stage_new.id,
                    "maintenance_team_id": self.team_a.id,
                    "priority": "2",
                    # hr_maintenance computes owner_user_id from an employee
                    # (hr_maintenance/models/equipment.py:87-97), and create()
                    # checks record rules before mail subscribes the creator, so
                    # being responsible is what lets a plain internal user pass
                    # the own-requests rule.
                    "user_id": self.requester.id,
                }
            )
        )
        self.assertEqual(self._records(request).sla_id, self.response | self.restore)

    def test_records_readable_by_any_internal_user(self):
        request = self._request()
        # The setup this test relies on: the requester cannot read the request.
        with self.assertRaises(AccessError):
            request.with_user(self.requester).check_access("read")
        for record in self._records(request).with_user(self.requester):
            self.assertEqual(record.state, "running")
            self.assertTrue(record.deadline)
            self.assertIn(request.name, record.display_name)

    def test_records_read_only_for_everyone(self):
        records = self._records(self._request()).with_user(self.manager)
        self.assertEqual(set(records.mapped("state")), {"running"})
        with self.assertRaises(AccessError):
            records.write({"cycle": 2})
        with self.assertRaises(AccessError):
            records.unlink()
