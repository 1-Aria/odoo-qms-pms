# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from .common import unique_code_prefix


class TestCatalogProfile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.code_prefix = unique_code_prefix()
        cls.defect_group = cls.env["qms.defect.code"].create(
            {
                "name": "Fabric Defect",
                "ref_code": f"{cls.code_prefix}-FAB",
                "domain_kind": "qm",
            }
        )
        cls.defect_code = cls.env["qms.defect.code"].create(
            {
                "name": "Torn",
                "ref_code": f"{cls.code_prefix}-FAB-01",
                "domain_kind": "qm",
                "parent_id": cls.defect_group.id,
            }
        )
        cls.part_group = cls.env["qms.object.part"].create(
            {
                "name": "Shirt Construction",
                "ref_code": f"{cls.code_prefix}-SHIRT",
                "domain_kind": "qm",
            }
        )
        cls.part_code = cls.env["qms.object.part"].create(
            {
                "name": "Sleeves",
                "ref_code": f"{cls.code_prefix}-SH-03",
                "domain_kind": "qm",
                "parent_id": cls.part_group.id,
            }
        )
        cls.machine_group = cls.env["qms.defect.code"].create(
            {
                "name": "Mechanical",
                "ref_code": f"{cls.code_prefix}-MECH",
                "domain_kind": "pm",
            }
        )
        cls.shared_group = cls.env["qms.defect.code"].create(
            {
                "name": "Handling",
                "ref_code": f"{cls.code_prefix}-HAND",
                "domain_kind": "both",
            }
        )
        cls.profile = cls.env["qms.catalog.profile"].create(
            {"name": "Shirt", "domain_kind": "qm"}
        )

    def test_groups_accepted(self):
        self.profile.write(
            {
                "defect_group_ids": [(6, 0, self.defect_group.ids)],
                "object_part_group_ids": [(6, 0, self.part_group.ids)],
            }
        )
        self.assertEqual(self.profile.defect_group_ids, self.defect_group)
        self.assertEqual(self.profile.object_part_group_ids, self.part_group)

    def test_defect_code_rejected(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.profile.write({"defect_group_ids": [(6, 0, self.defect_code.ids)]})

    def test_object_part_code_rejected(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.profile.write({"object_part_group_ids": [(6, 0, self.part_code.ids)]})

    def test_profile_ids_inverse(self):
        self.profile.write({"defect_group_ids": [(6, 0, self.defect_group.ids)]})
        self.assertEqual(self.defect_group.profile_ids, self.profile)
        self.profile.write({"defect_group_ids": [(5, 0, 0)]})
        self.assertFalse(self.defect_group.profile_ids)

    def test_domain_kind_clash(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.profile.write({"defect_group_ids": [(6, 0, self.machine_group.ids)]})
        pm_profile = self.env["qms.catalog.profile"].create(
            {"name": "Sewing Machine", "domain_kind": "pm"}
        )
        with self.assertRaises(ValidationError), self.cr.savepoint():
            pm_profile.write({"defect_group_ids": [(6, 0, self.defect_group.ids)]})

    def test_domain_kind_profile_narrowed(self):
        both_profile = self.env["qms.catalog.profile"].create(
            {
                "name": "General",
                "domain_kind": "both",
                "defect_group_ids": [(6, 0, self.machine_group.ids)],
            }
        )
        with self.assertRaises(ValidationError), self.cr.savepoint():
            both_profile.write({"domain_kind": "qm"})

    def test_domain_kind_both_accepted(self):
        self.profile.write({"defect_group_ids": [(6, 0, self.shared_group.ids)]})
        self.assertEqual(self.profile.defect_group_ids, self.shared_group)
        both_profile = self.env["qms.catalog.profile"].create(
            {"name": "General", "domain_kind": "both"}
        )
        both_profile.write(
            {
                "defect_group_ids": [
                    (6, 0, (self.defect_group | self.machine_group).ids)
                ]
            }
        )
        self.assertEqual(
            both_profile.defect_group_ids, self.defect_group | self.machine_group
        )
