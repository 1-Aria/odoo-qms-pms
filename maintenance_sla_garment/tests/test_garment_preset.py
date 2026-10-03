# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged

from ..hooks import (
    MODULE,
    PRIORITY_GRID,
    RESPONSE_RULES,
    _arrange_stages,
    _fill_priority_grid,
    post_init_hook,
)

RESTORE_RULES = [
    "sla_restore_high",
    "sla_restore_normal",
    "sla_restore_low",
    "sla_restore_very_low",
    "sla_restore_any",
]


@tagged("post_install", "-at_install")
class TestGarmentPreset(TransactionCase):
    """The preset, as the hook and the data install it.

    Each test runs the hook or a helper inside its own transaction and asserts
    the result, rather than reading what the install left: a site's later
    tuning would otherwise break the run.

    post_install: the preset depends on the whole SLA cluster being loaded.
    """

    def _ref(self, xml_id):
        return self.env.ref(f"{MODULE}.{xml_id}")

    def test_stage_flow(self):
        _arrange_stages(self.env)
        expected = [
            self.env.ref("maintenance.stage_0"),
            self.env.ref("maintenance.stage_1"),
            self._ref("stage_waiting_parts"),
            self._ref("stage_waiting_production"),
            self._ref("stage_restored"),
            self.env.ref("maintenance.stage_3"),
            self.env.ref("maintenance.stage_4"),
        ]
        stages = self.env["maintenance.stage"].search(
            [("id", "in", [stage.id for stage in expected])], order="sequence, id"
        )
        self.assertEqual(list(stages), expected)
        done = self.env.ref("maintenance.stage_3").with_context(lang="en_US")
        self.assertEqual(done.name, "Done")
        self.assertTrue(done.done)
        self.assertTrue(self.env.ref("maintenance.stage_4").sla_cancel)
        # Flagged done, it would set close_date before anyone confirmed.
        self.assertFalse(self._ref("stage_restored").done)

    def test_restore_rules_pause_in_waiting_stages(self):
        waiting = self._ref("stage_waiting_parts") | self._ref("stage_waiting_production")
        for xml_id in RESTORE_RULES:
            with self.subTest(rule=xml_id):
                rule = self._ref(xml_id)
                self.assertEqual(rule.target_stage_id, self._ref("stage_restored"))
                self.assertEqual(rule.pause_stage_ids, waiting)

    def test_every_priority_covered(self):
        expected = ["0", "1", "2", "3", False]
        response = [self._ref(xml_id).priority for xml_id, *_rest in RESPONSE_RULES]
        restore = [self._ref(xml_id).priority for xml_id in RESTORE_RULES]
        for kind, priorities in (("response", response), ("restore", restore)):
            with self.subTest(kind=kind):
                self.assertCountEqual(priorities, expected)

    def test_hook_runs_again_without_duplicates(self):
        rules = self.env["maintenance.sla"].with_context(active_test=False)
        grid = self.env["maintenance.priority.rule"].with_context(active_test=False)
        before = (rules.search_count([]), grid.search_count([]))
        post_init_hook(self.env)
        self.assertEqual((rules.search_count([]), grid.search_count([])), before)

    def test_grid_keeps_a_configured_pair(self):
        grid = self.env["maintenance.priority.rule"].with_context(active_test=False)
        grid.search([]).unlink()
        configured = grid.create(
            {"criticality": "a", "urgency": "safety", "priority": "1"}
        )
        _fill_priority_grid(self.env)
        self.assertEqual(grid.search_count([]), len(PRIORITY_GRID))
        self.assertEqual(configured.priority, "1")

    def test_hook_survives_missing_core_stages(self):
        """The safe-to-fail path: nothing to find, nothing done, no error.

        ir.model.data.unlink() clears the lookup cache, so env.ref sees the
        removal at once.
        """
        scrap = self.env.ref("maintenance.stage_4")
        scrap.sequence = 99
        response_ids = [xml_id for xml_id, *_rest in RESPONSE_RULES]
        self.env["ir.model.data"].search(
            [
                "|",
                "&",
                ("module", "=", "maintenance"),
                ("model", "=", "maintenance.stage"),
                "&",
                ("module", "=", MODULE),
                ("name", "in", response_ids),
            ]
        ).unlink()
        rules = self.env["maintenance.sla"].with_context(active_test=False)
        before = rules.search_count([])
        post_init_hook(self.env)
        self.assertEqual(rules.search_count([]), before)
        self.assertEqual(scrap.sequence, 99)
