# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestNonconformitySeverity(TransactionCase):
    """Item severity defaults and the header roll-up.

    Severities are created here with explicit ranks rather than taken from
    OCA's records, whose ranks this module never sets.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        severity = cls.env["mgmtsystem.nonconformity.severity"]
        cls.low = severity.create({"name": "Low", "qms_severity_rank": 10})
        cls.high = severity.create({"name": "High", "qms_severity_rank": 20})
        cls.zero_a = severity.create({"name": "Zero A", "qms_severity_rank": 0})
        cls.zero_b = severity.create({"name": "Zero B", "qms_severity_rank": 0})

        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        group = defect.create({"name": "Fabric Defect", "ref_code": f"{prefix}-FAB"})
        cls.code_low = defect.create(
            {
                "name": "Scratch",
                "ref_code": f"{prefix}-FAB-01",
                "parent_id": group.id,
                "default_severity_id": cls.low.id,
            }
        )
        cls.code_high = defect.create(
            {
                "name": "Torn",
                "ref_code": f"{prefix}-FAB-02",
                "parent_id": group.id,
                "default_severity_id": cls.high.id,
            }
        )
        cls.code_none = defect.create(
            {
                "name": "Other",
                "ref_code": f"{prefix}-FAB-03",
                "parent_id": group.id,
            }
        )

    def _nonconformity(self, **extra):
        user = self.env.user
        values = {
            "description": "Severity roll-up",
            "origin_ids": [
                (6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
            ],
            "responsible_user_id": user.id,
            "manager_user_id": user.id,
            "user_id": user.id,
        }
        values.update(extra)
        return self.env["mgmtsystem.nonconformity"].create(values)

    def _item(self, nonconformity, code, sequence=10, **extra):
        values = {
            "nonconformity_id": nonconformity.id,
            "defect_code_id": code.id,
            "sequence": sequence,
        }
        values.update(extra)
        return self.env["qms.nonconformity.item"].create(values)

    # Item severity

    def test_item_severity_from_defect_code(self):
        item = self._item(self._nonconformity(), self.code_high)
        self.assertEqual(item.severity_id, self.high)

    def test_item_severity_manual_kept(self):
        item = self._item(self._nonconformity(), self.code_high)
        item.severity_id = self.low
        item.qty_affected = 3
        self.assertEqual(item.severity_id, self.low)

    def test_item_severity_rederived_on_code_change(self):
        item = self._item(self._nonconformity(), self.code_high)
        item.severity_id = self.zero_a
        item.defect_code_id = self.code_low
        self.assertEqual(item.severity_id, self.low)

    # Header roll-up

    def test_header_rollup_highest_rank(self):
        nonconformity = self._nonconformity()
        self._item(nonconformity, self.code_low, sequence=1)
        self._item(nonconformity, self.code_high, sequence=2)
        self.assertEqual(nonconformity.severity_id, self.high)

    def test_header_rollup_all_zero_first_item(self):
        # The unconfigured state: every rank still 0.
        nonconformity = self._nonconformity()
        self._item(
            nonconformity, self.code_none, sequence=2, severity_id=self.zero_b.id
        )
        self._item(
            nonconformity, self.code_none, sequence=1, severity_id=self.zero_a.id
        )
        self.assertEqual(nonconformity.severity_id, self.zero_a)

    def test_header_rollup_follows_reorder(self):
        # Under the tie rule the first item wins, so reordering existing items
        # must re-roll the header. Both ranks are 0 on purpose: with different
        # ranks the more severe item wins whatever the order, and this would
        # pass without exercising item_ids.sequence at all.
        nonconformity = self._nonconformity()
        first = self._item(
            nonconformity, self.code_none, sequence=1, severity_id=self.zero_a.id
        )
        self._item(
            nonconformity, self.code_none, sequence=2, severity_id=self.zero_b.id
        )
        self.assertEqual(nonconformity.severity_id, self.zero_a)
        first.sequence = 3
        self.assertEqual(nonconformity.severity_id, self.zero_b)

    def test_header_rollup_skips_unset(self):
        nonconformity = self._nonconformity()
        self._item(nonconformity, self.code_none, sequence=1)
        self._item(nonconformity, self.code_low, sequence=2)
        self.assertEqual(nonconformity.severity_id, self.low)

    def test_header_no_items_untouched(self):
        nonconformity = self._nonconformity(severity_id=self.high.id)
        nonconformity.description = "Edited"
        self.assertEqual(nonconformity.severity_id, self.high)
        # An item with no severity does not count either.
        self._item(nonconformity, self.code_none)
        self.assertEqual(nonconformity.severity_id, self.high)

    def test_rank_change_does_not_recompute(self):
        nonconformity = self._nonconformity()
        self._item(nonconformity, self.code_low, sequence=1)
        self._item(nonconformity, self.code_high, sequence=2)
        self.assertEqual(nonconformity.severity_id, self.high)
        self.low.qms_severity_rank = 30
        self.env.flush_all()
        nonconformity.invalidate_recordset(["severity_id"])
        self.assertEqual(nonconformity.severity_id, self.high)
