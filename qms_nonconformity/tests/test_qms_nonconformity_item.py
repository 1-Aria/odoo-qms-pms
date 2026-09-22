# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestNonconformityItem(TransactionCase):
    """Analysis items and the profile-scoped code filtering.

    post_install because the fixtures create a product. at_install runs while
    later modules are still unloaded, so columns they added -- here
    product_template.sale_line_warn, from sale -- are NOT NULL in the database
    but absent from the registry, and no default applies.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        part = cls.env["qms.object.part"]
        cls.defect_group = defect.create(
            {"name": "Fabric Defect", "ref_code": f"{cls.prefix}-FAB"}
        )
        cls.defect_code = defect.create(
            {
                "name": "Torn",
                "ref_code": f"{cls.prefix}-FAB-01",
                "parent_id": cls.defect_group.id,
            }
        )
        cls.other_defect_group = defect.create(
            {"name": "Mechanical", "ref_code": f"{cls.prefix}-MECH"}
        )
        cls.other_defect_code = defect.create(
            {
                "name": "Bearing failure",
                "ref_code": f"{cls.prefix}-MECH-01",
                "parent_id": cls.other_defect_group.id,
            }
        )
        cls.part_group = part.create(
            {"name": "Shirt Construction", "ref_code": f"{cls.prefix}-SHIRT"}
        )
        cls.part_code = part.create(
            {
                "name": "Sleeves",
                "ref_code": f"{cls.prefix}-SH-03",
                "parent_id": cls.part_group.id,
            }
        )
        cls.other_part_group = part.create(
            {"name": "Machine Assemblies", "ref_code": f"{cls.prefix}-MACH"}
        )
        cls.other_part_code = part.create(
            {
                "name": "Needle bar",
                "ref_code": f"{cls.prefix}-MA-01",
                "parent_id": cls.other_part_group.id,
            }
        )
        cls.profile = cls.env["qms.catalog.profile"].create(
            {
                "name": "Shirt",
                "defect_group_ids": [(6, 0, cls.defect_group.ids)],
                "object_part_group_ids": [(6, 0, cls.part_group.ids)],
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Oxford Shirt", "qms_profile_ids": [(6, 0, cls.profile.ids)]}
        )
        cls.nonconformity = cls._create_nonconformity(product=cls.product)

    @classmethod
    def _create_nonconformity(cls, product=None):
        """Fill in everything mgmtsystem_nonconformity requires."""
        user = cls.env.user
        return cls.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Torn sleeves on the January lot",
                "partner_id": cls.env.ref("base.main_partner").id,
                "origin_ids": [
                    (6, 0, cls.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
                "product_id": product.id if product else False,
            }
        )

    def _code_domain(self, model, nonconformity):
        """The item's view domain, with parent.<field> substituted."""
        return self.env[model].search(
            [
                (
                    "parent_id.profile_ids",
                    "in",
                    nonconformity.qms_effective_profile_ids.ids,
                )
            ]
        )

    def test_item_created(self):
        item = self.env["qms.nonconformity.item"].create(
            {
                "nonconformity_id": self.nonconformity.id,
                "defect_code_id": self.defect_code.id,
                "object_part_id": self.part_code.id,
            }
        )
        self.assertEqual(item.defect_code_id, self.defect_code)
        self.assertEqual(self.nonconformity.item_ids, item)

    def test_item_display_name(self):
        item = self.env["qms.nonconformity.item"].create(
            {
                "nonconformity_id": self.nonconformity.id,
                "defect_code_id": self.defect_code.id,
                "object_part_id": self.part_code.id,
            }
        )
        self.assertEqual(item.display_name, "Torn · Sleeves")
        item.object_part_id = False
        self.assertEqual(item.display_name, "Torn")

    def test_item_cascade(self):
        nonconformity = self._create_nonconformity(product=self.product)
        item = self.env["qms.nonconformity.item"].create(
            {
                "nonconformity_id": nonconformity.id,
                "defect_code_id": self.defect_code.id,
            }
        )
        nonconformity.unlink()
        self.assertFalse(item.exists())

    @mute_logger("odoo.sql_db")
    def test_defect_code_restrict(self):
        code = self.env["qms.defect.code"].create(
            {
                "name": "Scratch",
                "ref_code": f"{self.prefix}-FAB-02",
                "parent_id": self.defect_group.id,
            }
        )
        self.env["qms.nonconformity.item"].create(
            {
                "nonconformity_id": self.nonconformity.id,
                "defect_code_id": code.id,
            }
        )
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            code.unlink()

    def test_effective_profiles_related(self):
        self.assertEqual(
            self.nonconformity.qms_effective_profile_ids,
            self.product.qms_effective_profile_ids,
        )
        self.assertEqual(self.nonconformity.qms_effective_profile_ids, self.profile)

    def test_domain_matches_profile_codes(self):
        codes = self._code_domain("qms.defect.code", self.nonconformity)
        self.assertIn(self.defect_code, codes)
        self.assertNotIn(self.other_defect_code, codes)
        # A group has no parent, so the domain never offers one.
        self.assertNotIn(self.defect_group, codes)

    def test_domain_matches_object_parts(self):
        parts = self._code_domain("qms.object.part", self.nonconformity)
        self.assertIn(self.part_code, parts)
        self.assertNotIn(self.other_part_code, parts)
        self.assertNotIn(self.part_group, parts)

    def test_domain_without_product(self):
        nonconformity = self._create_nonconformity()
        self.assertFalse(nonconformity.qms_effective_profile_ids)
        self.assertFalse(self._code_domain("qms.defect.code", nonconformity))
