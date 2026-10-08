# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.zalo_oa_garment.hooks import MODULE, post_init_hook

STAGES = {
    "parts": "maintenance_sla_garment.stage_waiting_parts",
    "production": "maintenance_sla_garment.stage_waiting_production",
    "restored": "maintenance_sla_garment.stage_restored",
}


@tagged("post_install", "-at_install")
class TestZaloGarment(TransactionCase):
    """The preset's templates, rules and install hook.

    post_install: the fixtures create requests and inspections, core records
    later modules extend. The shipped rules queue nothing without a
    destination, so the fixtures give every action one; nothing is sent, since
    the send cron does not run in a test.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.actions = cls._module_records("ir.actions.server")
        # Read before the fixture gives them a destination.
        cls.shipped_destinations = cls.actions.mapped("zalo_destination_ids")
        cls.destination = cls.env["zalo.destination"].create(
            {"name": "Garment test chat", "zalo_id": "G-GARMENT"}
        )
        cls.actions.write({"zalo_destination_ids": [(6, 0, cls.destination.ids)]})

        cls.equipment = cls.env["maintenance.equipment"].create(
            {"name": "Zalo garment test machine"}
        )
        cls.qc_test = cls.env["qc.test"].create({"name": "Zalo garment test"})
        # Archived, so that it matches no other request; the SLA test attaches
        # records to it by hand.
        cls.sla_rule = cls.env["maintenance.sla"].create(
            {
                "name": "Zalo garment test SLA",
                "maintenance_type": "corrective",
                "target_stage_id": cls.env.ref(STAGES["restored"]).id,
                "duration": 1.0,
                "active": False,
            }
        )

    def setUp(self):
        super().setUp()
        # The rules fire through patches base_automation puts on the model
        # classes when the registry loads. _unregister_hook strips every one
        # (base_automation.py:983-991), and tests that create a rule call it in
        # tearDown — zalo_oa's template tests do — leaving the installed rules
        # off for the rest of the run. So they are registered afresh here, and
        # the classes put back as they were found: Odoo's after-test check
        # fails on attributes the class did not have at setUpClass.
        automations = self.env["base.automation"]
        patched = "create" in vars(type(self.env["maintenance.request"]))
        automations._unregister_hook()
        automations._register_hook()
        if not patched:
            self.addCleanup(automations._unregister_hook)

    @classmethod
    def _module_records(cls, model):
        data = cls.env["ir.model.data"].search(
            [("module", "=", MODULE), ("model", "=", model)]
        )
        return cls.env[model].browse(data.mapped("res_id"))

    def _request(self, maintenance_type="corrective", **values):
        values.setdefault("name", "Zalo garment test request")
        values.setdefault("equipment_id", self.equipment.id)
        values.setdefault("priority", "2")
        return self.env["maintenance.request"].create(
            dict(values, maintenance_type=maintenance_type)
        )

    def _messages(self, template_xmlid, record):
        return self.env["zalo.message"].search(
            [
                ("template_id", "=", self.env.ref(f"{MODULE}.{template_xmlid}").id),
                ("res_model", "=", record._name),
                ("res_id", "=", record.id),
            ],
            order="id",
        )

    def _sla_record(self, request, state):
        """An SLA record whose at-risk time and deadline passed two minutes ago."""
        record = self.env["maintenance.request.sla"].create(
            {
                "request_id": request.id,
                "sla_id": self.sla_rule.id,
                "target_stage_id": self.sla_rule.target_stage_id.id,
                "start_at": fields.Datetime.now() - timedelta(hours=1),
            }
        )
        self.env.flush_all()
        past = fields.Datetime.now() - timedelta(minutes=2)
        self.env.cr.execute(
            "UPDATE maintenance_request_sla "
            "SET risk_at = %s, deadline = %s, state = %s WHERE id = %s",
            [past, past, state, record.id],
        )
        record.invalidate_recordset()
        return record

    def test_shipped_without_destinations(self):
        self.assertEqual(len(self.actions), 8)
        self.assertFalse(self.shipped_destinations)

    def test_templates_render(self):
        request = self._request()
        sla_record = self._sla_record(request, "running")
        inspection = self.env["qc.inspection"].create({"test": self.qc_test.id})
        expected = {
            "template_request_new": (request, [request.code, "Bình thường"]),
            "template_request_paused": (request, [request.code]),
            "template_request_restored": (request, [request.code]),
            "template_request_assigned": (request, [request.code, "Bình thường"]),
            "template_sla_at_risk": (sla_record, [request.code, "Bình thường"]),
            "template_sla_breached": (sla_record, [request.code, "Bình thường"]),
            "template_inspection_new": (inspection, [inspection.name]),
            "template_inspection_failed": (inspection, [inspection.name]),
        }
        for xmlid, (record, fragments) in expected.items():
            with self.subTest(xmlid):
                template = self.env.ref(f"{MODULE}.{xmlid}")
                text = template._render_field("body", record.ids)[record.id]
                for fragment in fragments:
                    self.assertIn(fragment, text)
                self.assertNotIn("{{", text)

    def test_new_corrective_request(self):
        corrective = self._request()
        preventive = self._request("preventive")
        self.assertEqual(len(self._messages("template_request_new", corrective)), 1)
        self.assertFalse(self._messages("template_request_new", preventive))

    def test_paused_and_restored(self):
        corrective = self._request()
        preventive = self._request("preventive")
        for request in corrective | preventive:
            for stage in ("parts", "production", "restored"):
                request.stage_id = self.env.ref(STAGES[stage])
        self.assertEqual(len(self._messages("template_request_paused", corrective)), 2)
        self.assertEqual(
            len(self._messages("template_request_restored", corrective)), 1
        )
        self.assertFalse(self._messages("template_request_paused", preventive))
        self.assertFalse(self._messages("template_request_restored", preventive))

    def test_technician_assigned(self):
        technician = self.env.ref("base.user_admin")
        request = self._request()
        self.assertFalse(request.user_id)
        self.assertFalse(self._messages("template_request_assigned", request))
        request.user_id = technician
        messages = self._messages("template_request_assigned", request)
        self.assertEqual(len(messages), 1)
        self.assertIn(technician.name, messages.text)
        request.user_id = False
        self.assertEqual(len(self._messages("template_request_assigned", request)), 1)

    def test_sla_time_rules(self):
        request = self._request()
        running = self._sla_record(request, "running")
        paused = self._sla_record(request, "paused")
        rules = self._module_records("base.automation").filtered(
            lambda rule: rule.trigger == "on_time"
        )
        rules.write({"last_run": fields.Datetime.now() - timedelta(minutes=10)})
        self.env["base.automation"]._check()
        for xmlid in ("template_sla_at_risk", "template_sla_breached"):
            with self.subTest(xmlid):
                self.assertEqual(len(self._messages(xmlid, running)), 1)
                self.assertFalse(self._messages(xmlid, paused))

    def test_inspection_rules(self):
        failing = self.env["qc.inspection"].create({"test": self.qc_test.id})
        passing = self.env["qc.inspection"].create({"test": self.qc_test.id})
        self.assertEqual(len(self._messages("template_inspection_new", failing)), 1)
        failing.state = "waiting"
        failing.state = "failed"
        passing.state = "success"
        messages = self._messages("template_inspection_failed", failing)
        self.assertEqual(len(messages), 2)
        self.assertIn("chờ duyệt", messages[0].text)
        self.assertIn("không đạt", messages[1].text)
        self.assertFalse(self._messages("template_inspection_failed", passing))

    def test_hook_runs_again(self):
        rules = self.env["base.automation"].search_count([])
        post_init_hook(self.env)
        self.assertEqual(self.env["base.automation"].search_count([]), rules)

    def test_hook_survives_missing_stages(self):
        self.env["ir.model.data"].search(
            [
                ("module", "=", MODULE),
                ("name", "in", ["rule_request_paused", "rule_request_restored"]),
            ]
        ).unlink()
        self.env["ir.model.data"].search(
            [
                ("module", "=", "maintenance_sla_garment"),
                ("model", "=", "maintenance.stage"),
            ]
        ).unlink()
        rules = self.env["base.automation"].search_count([])
        post_init_hook(self.env)
        self.assertEqual(self.env["base.automation"].search_count([]), rules)
