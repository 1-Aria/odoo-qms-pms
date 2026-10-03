# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from lxml import etree

from odoo.tests.common import new_test_user, tagged

from .test_maintenance_sla_rematch import RematchCase

FINISHED = [("state", "in", ("achieved", "achieved_late"))]
NOT_WAIVED = [("waived", "=", False)]


@tagged("post_install", "-at_install")
class TestSlaReport(RematchCase):
    """The SLA Analysis report: its measures, filters, action and menu.

    post_install: the fixtures create users, equipment and requests.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env,
            login="sla_test_report_manager",
            groups="base.group_user,maintenance.group_equipment_manager",
        )
        cls.reason = cls.env["maintenance.sla.waive.reason"].create(
            {"name": "SLA test power cut"}
        )

    def _three_responses(self):
        """One met on time, one met late, one still running."""
        on_time = self._new()
        self._write(on_time, 0.5, stage_id=self.stage_progress.id)
        late = self._new()
        self._write(late, 2, stage_id=self.stage_progress.id)
        running = self._new()
        requests = on_time | late | running
        domain = [
            ("sla_id", "=", self.response.id),
            ("request_id", "in", requests.ids),
        ]
        return domain, self._record(late, self.response)

    def _average(self, domain, field):
        [(value,)] = self.env["maintenance.request.sla"]._read_group(
            domain, [], [f"{field}:avg"]
        )
        return value

    def test_compliance_averages_finished_records(self):
        domain, _late = self._three_responses()
        self.assertAlmostEqual(
            self._average(domain + FINISHED + NOT_WAIVED, "on_time"), 50.0
        )
        # The running record's on_time is NULL, which AVG skips.
        self.assertAlmostEqual(self._average(domain, "on_time"), 50.0)

    def test_waived_records_leave_compliance(self):
        domain, late = self._three_responses()
        self.env["maintenance.request.sla.waive"].with_user(self.manager).create(
            {"sla_record_id": late.id, "reason_id": self.reason.id}
        ).action_confirm()
        self.assertAlmostEqual(
            self._average(domain + FINISHED + NOT_WAIVED, "on_time"), 100.0
        )

    def test_aggregators(self):
        domain, _late = self._three_responses()
        [totals] = self.env["maintenance.request.sla"].read_group(
            domain + FINISHED, ["elapsed"], []
        )
        self.assertAlmostEqual(totals["elapsed"], 1.25)
        fields = self.env["maintenance.request.sla"].fields_get(
            attributes=["aggregator"]
        )
        for name in ("on_time", "elapsed", "paused_time", "duration"):
            with self.subTest(field=name):
                self.assertEqual(fields[name].get("aggregator"), "avg")
        # A field without an aggregator may omit the key.
        for name in ("target_sequence", "at_risk_pct", "consumed", "cycle"):
            with self.subTest(field=name):
                self.assertFalse(fields[name].get("aggregator"))

    def test_report_action_and_menu(self):
        action = self.env.ref("maintenance_sla.maintenance_request_sla_action_report")
        context = ast.literal_eval(action.context)
        self.assertTrue(context["search_default_finished"])
        self.assertTrue(context["search_default_not_waived"])
        arch = self.env["maintenance.request.sla"].get_view(
            action.search_view_id.id, "search"
        )["arch"]
        filters = etree.fromstring(arch).xpath("//filter/@name")
        self.assertIn("finished", filters)
        self.assertIn("not_waived", filters)
        menu = self.env.ref("maintenance_sla.menu_maintenance_sla_report")
        self.assertEqual(menu.parent_id, self.env.ref("maintenance.maintenance_reporting"))
        self.assertEqual(
            menu.groups_id, self.env.ref("maintenance.group_equipment_manager")
        )

    def test_report_views_load(self):
        records = self.env["maintenance.request.sla"]
        pivot = self.env.ref("maintenance_sla.maintenance_request_sla_view_pivot")
        arch = etree.fromstring(records.get_view(pivot.id, "pivot")["arch"])
        self.assertIn("on_time", arch.xpath("//field[@type='measure']/@name"))
        graph = self.env.ref("maintenance_sla.maintenance_request_sla_view_graph")
        self.assertEqual(
            etree.fromstring(records.get_view(graph.id, "graph")["arch"]).tag,
            "graph",
        )
