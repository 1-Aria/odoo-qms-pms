# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestEquipmentStatusAutomation(TransactionCase):
    """A corrective request's stage sets its machine's status.

    The fixtures create their own stages, statuses, categories and machine, and
    never read the instance's: statuses and stages are a site's configuration.

    post_install: the fixtures create equipment, requests and a user.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category, cls.other_category = cls.env[
            "maintenance.equipment.category"
        ].create([{"name": "Status test sewing"}, {"name": "Status test cutting"}])
        statuses = cls.env["maintenance.equipment.status"]
        cls.down = statuses.create({"name": "Status test down"})
        cls.operational = statuses.create({"name": "Status test operational"})
        # Limited to a category the machine is not in.
        cls.retired = statuses.create(
            {
                "name": "Status test retired",
                "category_ids": [Command.set(cls.other_category.ids)],
            }
        )
        (
            cls.stage_new,
            cls.stage_down,
            cls.stage_down_too,
            cls.stage_restored,
            cls.stage_retired,
        ) = cls.env["maintenance.stage"].create(
            [
                {"name": "Status test: new", "sequence": 951},
                {
                    "name": "Status test: in progress",
                    "sequence": 952,
                    "equipment_status_id": cls.down.id,
                },
                {
                    "name": "Status test: waiting",
                    "sequence": 953,
                    "equipment_status_id": cls.down.id,
                },
                {
                    "name": "Status test: restored",
                    "sequence": 954,
                    "equipment_status_id": cls.operational.id,
                },
                {
                    "name": "Status test: scrap",
                    "sequence": 955,
                    "equipment_status_id": cls.retired.id,
                },
            ]
        )
        cls.machine = cls.env["maintenance.equipment"].create(
            {"name": "Status test machine", "category_id": cls.category.id}
        )

    def _request(self, **values):
        values.setdefault("name", "Status test request")
        values.setdefault("maintenance_type", "corrective")
        values.setdefault("stage_id", self.stage_new.id)
        values.setdefault("equipment_id", self.machine.id)
        return self.env["maintenance.request"].create(values)

    def test_reaching_a_mapped_stage_sets_the_status(self):
        request = self._request()
        self.assertFalse(self.machine.status_id)
        request.stage_id = self.stage_down
        self.assertEqual(self.machine.status_id, self.down)
        request.stage_id = self.stage_restored
        self.assertEqual(self.machine.status_id, self.operational)

    def test_unmapped_stage_leaves_the_status(self):
        request = self._request(stage_id=self.stage_down.id)
        request.stage_id = self.stage_new
        self.assertEqual(self.machine.status_id, self.down)

    def test_preventive_requests_ignored(self):
        request = self._request(maintenance_type="preventive")
        request.stage_id = self.stage_down
        self.assertFalse(self.machine.status_id)

    def test_created_in_a_mapped_stage(self):
        self._request(stage_id=self.stage_down.id)
        self.assertEqual(self.machine.status_id, self.down)

    def test_manual_status_survives_an_unchanged_stage(self):
        request = self._request(stage_id=self.stage_down.id)
        self.machine.status_id = self.operational
        request.write({"stage_id": self.stage_down.id})
        self.assertEqual(self.machine.status_id, self.operational)
        request.write({"description": "Status test note"})
        self.assertEqual(self.machine.status_id, self.operational)

    def test_status_limited_to_other_categories_skipped(self):
        request = self._request(stage_id=self.stage_down.id)
        request.stage_id = self.stage_retired
        self.assertEqual(self.machine.status_id, self.down)

    def test_request_without_equipment_ignored(self):
        request = self._request(equipment_id=False)
        request.stage_id = self.stage_down
        request.stage_id = self.stage_restored
        self.assertFalse(self.machine.status_id)

    def test_any_request_mover_may_trigger_it(self):
        """Written as sudo(): a user who cannot write equipment still moves it.

        The user is the request's responsible: hr_maintenance empties
        owner_user_id, so being responsible is what lets a plain internal user
        reach the request at all.
        """
        user = new_test_user(
            self.env, login="status_test_mover", groups="base.group_user"
        )
        # The control: this user cannot write the machine directly.
        with self.assertRaises(AccessError):
            self.machine.with_user(user).write({"status_id": self.operational.id})
        request = self._request(user_id=user.id)
        request.with_user(user).write({"stage_id": self.stage_down.id})
        self.assertEqual(self.machine.status_id, self.down)

    def test_no_write_when_unchanged(self):
        """Two stages mapped to one status: nothing written on the second move.

        write_date cannot show it: within one test transaction every write
        carries the same timestamp. The registry's class is patched, which is
        the class every equipment record uses.
        """
        request = self._request(stage_id=self.stage_down.id)
        equipment_class = self.env.registry["maintenance.equipment"]
        original = equipment_class.write
        with patch.object(
            equipment_class, "write", autospec=True, side_effect=original
        ) as write:
            request.stage_id = self.stage_down_too
        write.assert_not_called()
        self.assertEqual(self.machine.status_id, self.down)
