# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tools import mute_logger


def unique_code_prefix():
    """Fixture codes must not collide with real catalog data.

    ``ref_code`` is unique across the whole table and the instance is a working
    database, so a fixed code fails as soon as the same one exists for real.
    """
    return f"T{uuid4().hex[:6].upper()}"


class CatalogCommon:
    """Behaviour every catalog inherits from ``qms.catalog.mixin``.

    Not a TestCase, so the test loader does not run it on its own. Subclasses
    set ``model_name`` and inherit from TransactionCase, in that order: this
    class must come first so that its ``setUpClass`` runs and reaches
    TransactionCase through ``super()``.
    """

    # Odoo only collects test methods from a class's own __dict__ unless this
    # is set (odoo/tests/loader.py:29-38). Without it the subclasses collect
    # nothing and the run passes with zero tests. getattr walks the MRO, so
    # declaring it here covers every subclass.
    allow_inherited_tests_method = True

    model_name = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env[cls.model_name]
        cls.code_prefix = unique_code_prefix()
        cls.group = cls.model.create(
            {
                "name": "Group A",
                "ref_code": f"{cls.code_prefix}-GRP",
                "domain_kind": "qm",
            }
        )
        cls.code = cls.model.create(
            {
                "name": "Code One",
                "ref_code": f"{cls.code_prefix}-GRP-01",
                "domain_kind": "qm",
                "parent_id": cls.group.id,
            }
        )

    def test_display_name(self):
        self.assertEqual(self.group.display_name, "Group A")
        self.assertEqual(self.code.display_name, "Group A / Code One")

    def test_name_search_ref_code(self):
        self.assertEqual(
            self.model.name_search(f"{self.code_prefix}-GRP-01"),
            [(self.code.id, "Group A / Code One")],
        )

    def test_depth_code_under_code(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.model.create(
                {
                    "name": "Code One A",
                    "ref_code": f"{self.code_prefix}-GRP-01-A",
                    "domain_kind": "qm",
                    "parent_id": self.code.id,
                }
            )

    def test_depth_group_with_codes(self):
        other_group = self.model.create(
            {
                "name": "Group B",
                "ref_code": f"{self.code_prefix}-GRB",
                "domain_kind": "qm",
            }
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
                {
                    "name": "Code One again",
                    "ref_code": f"{self.code_prefix}-GRP-01",
                    "domain_kind": "qm",
                }
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
                    "name": "Code Two",
                    "ref_code": f"{self.code_prefix}-GRP-02",
                    "domain_kind": "pm",
                    "parent_id": self.group.id,
                }
            )

    def test_domain_kind_both_group(self):
        both_group = self.model.create(
            {
                "name": "Group General",
                "ref_code": f"{self.code_prefix}-GEN",
                "domain_kind": "both",
            }
        )
        for index, kind in enumerate(["qm", "pm", "both"]):
            code = self.model.create(
                {
                    "name": f"General code {kind}",
                    "ref_code": f"{self.code_prefix}-GEN-0{index}",
                    "domain_kind": kind,
                    "parent_id": both_group.id,
                }
            )
            self.assertEqual(code.parent_id, both_group)

    def test_domain_kind_group_narrowed(self):
        both_group = self.model.create(
            {
                "name": "Group General",
                "ref_code": f"{self.code_prefix}-GEN",
                "domain_kind": "both",
            }
        )
        self.model.create(
            {
                "name": "General code pm",
                "ref_code": f"{self.code_prefix}-GEN-01",
                "domain_kind": "pm",
                "parent_id": both_group.id,
            }
        )
        with self.assertRaises(ValidationError), self.cr.savepoint():
            both_group.write({"domain_kind": "qm"})
