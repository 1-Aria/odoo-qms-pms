# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestQmsCatalog(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["qms.defect.code"]
        cls.group = cls.model.create(
            {"name": "Fabric Defect", "ref_code": "FAB", "domain_kind": "qm"}
        )
        cls.code = cls.model.create(
            {
                "name": "Torn",
                "ref_code": "FAB-01",
                "domain_kind": "qm",
                "parent_id": cls.group.id,
            }
        )

    def test_display_name(self):
        self.assertEqual(self.group.display_name, "Fabric Defect")
        self.assertEqual(self.code.display_name, "Fabric Defect / Torn")

    def test_name_search_ref_code(self):
        self.assertEqual(
            self.model.name_search("FAB-01"),
            [(self.code.id, "Fabric Defect / Torn")],
        )

    def test_depth_code_under_code(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.model.create(
                {
                    "name": "Torn edge",
                    "ref_code": "FAB-01-A",
                    "domain_kind": "qm",
                    "parent_id": self.code.id,
                }
            )

    def test_depth_group_with_codes(self):
        other_group = self.model.create(
            {"name": "Seam Defect", "ref_code": "SEAM", "domain_kind": "qm"}
        )
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.group.write({"parent_id": other_group.id})

    def test_depth_self_parent(self):
        # _parent_store checks for recursion while flushing parent_id, so this
        # raises UserError before @api.constrains runs (odoo/models.py:5378).
        with self.assertRaises(UserError), self.cr.savepoint():
            self.group.write({"parent_id": self.group.id})

    @mute_logger("odoo.sql_db")
    def test_ref_code_unique(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.model.create(
                {"name": "Torn again", "ref_code": "FAB-01", "domain_kind": "qm"}
            )
            self.model.flush_model()

    @mute_logger("odoo.sql_db")
    def test_ref_code_required(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.model.create({"name": "No code", "domain_kind": "qm"})
            self.model.flush_model()

    def test_domain_kind_mismatch(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.model.create(
                {
                    "name": "Bearing failure",
                    "ref_code": "FAB-02",
                    "domain_kind": "pm",
                    "parent_id": self.group.id,
                }
            )

    def test_domain_kind_both_group(self):
        both_group = self.model.create(
            {"name": "General", "ref_code": "GEN", "domain_kind": "both"}
        )
        for index, kind in enumerate(["qm", "pm", "both"]):
            code = self.model.create(
                {
                    "name": f"General code {kind}",
                    "ref_code": f"GEN-0{index}",
                    "domain_kind": kind,
                    "parent_id": both_group.id,
                }
            )
            self.assertEqual(code.parent_id, both_group)

    def test_domain_kind_group_narrowed(self):
        both_group = self.model.create(
            {"name": "General", "ref_code": "GEN", "domain_kind": "both"}
        )
        self.model.create(
            {
                "name": "Bearing failure",
                "ref_code": "GEN-01",
                "domain_kind": "pm",
                "parent_id": both_group.id,
            }
        )
        with self.assertRaises(ValidationError), self.cr.savepoint():
            both_group.write({"domain_kind": "qm"})
