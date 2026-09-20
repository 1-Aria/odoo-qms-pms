# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestCatalogAssignment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.grand_categ = cls.env["product.category"].create({"name": "Garments"})
        cls.parent_categ = cls.env["product.category"].create(
            {"name": "Shirts", "parent_id": cls.grand_categ.id}
        )
        cls.child_categ = cls.env["product.category"].create(
            {"name": "Dress Shirts", "parent_id": cls.parent_categ.id}
        )
        cls.template = cls.env["product.template"].create(
            {"name": "Oxford Shirt", "categ_id": cls.child_categ.id}
        )
        cls.product = cls.template.product_variant_ids
        profile = cls.env["qms.catalog.profile"]
        cls.categ_profile = profile.create({"name": "Garment Category"})
        cls.tmpl_profile = profile.create({"name": "Shirt Template"})
        cls.variant_profile = profile.create({"name": "Oxford Variant"})

    def test_category_chain(self):
        self.parent_categ.qms_profile_ids = self.categ_profile
        self.assertEqual(self.child_categ.qms_effective_profile_ids, self.categ_profile)
        self.assertEqual(
            self.parent_categ.qms_effective_profile_ids, self.categ_profile
        )
        self.assertFalse(self.grand_categ.qms_effective_profile_ids)

    def test_template_effective(self):
        self.parent_categ.qms_profile_ids = self.categ_profile
        self.template.qms_profile_ids = self.tmpl_profile
        self.assertEqual(
            self.template.qms_effective_profile_ids,
            self.categ_profile | self.tmpl_profile,
        )

    def test_product_effective(self):
        self.parent_categ.qms_profile_ids = self.categ_profile
        self.template.qms_profile_ids = self.tmpl_profile
        self.product.qms_profile_ids = self.variant_profile
        self.assertEqual(
            self.product.qms_effective_profile_ids,
            self.categ_profile | self.tmpl_profile | self.variant_profile,
        )

    def test_product_without_assignment(self):
        self.assertFalse(self.product.qms_effective_profile_ids)

    def test_category_ancestor_invalidation(self):
        # Read first, so the value is cached, then change an ancestor two
        # levels up: without recursive=True the second read is stale.
        self.assertFalse(self.child_categ.qms_effective_profile_ids)
        self.grand_categ.qms_profile_ids = self.categ_profile
        self.assertEqual(self.child_categ.qms_effective_profile_ids, self.categ_profile)
        self.assertEqual(
            self.product.qms_effective_profile_ids, self.categ_profile
        )

    def test_profile_inverse_assignment(self):
        self.categ_profile.write(
            {
                "product_ids": [(6, 0, self.product.ids)],
                "product_tmpl_ids": [(6, 0, self.template.ids)],
                "categ_ids": [(6, 0, self.child_categ.ids)],
            }
        )
        self.assertEqual(self.product.qms_profile_ids, self.categ_profile)
        self.assertEqual(self.template.qms_profile_ids, self.categ_profile)
        self.assertEqual(self.child_categ.qms_profile_ids, self.categ_profile)
        self.categ_profile.write(
            {
                "product_ids": [(5, 0, 0)],
                "product_tmpl_ids": [(5, 0, 0)],
                "categ_ids": [(5, 0, 0)],
            }
        )
        self.assertFalse(self.product.qms_profile_ids)
        self.assertFalse(self.template.qms_profile_ids)
        self.assertFalse(self.child_categ.qms_profile_ids)
