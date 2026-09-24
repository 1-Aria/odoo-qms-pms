# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestCodeDomain(TransactionCase):
    """The advisory catalog filtering on analysis items.

    Each test reads the computed domain and runs it as a search, which is what
    the client ultimately sends. post_install: the fixtures create a product.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        part = cls.env["qms.object.part"]

        # In the profile.
        cls.defect_group = defect.create(
            {"name": "Fabric Defect", "ref_code": f"{prefix}-FAB"}
        )
        cls.torn = defect.create(
            {
                "name": "Torn",
                "ref_code": f"{prefix}-FAB-01",
                "parent_id": cls.defect_group.id,
            }
        )
        cls.part_group = part.create({"name": "Shirt", "ref_code": f"{prefix}-SHIRT"})
        cls.sleeves = part.create(
            {
                "name": "Sleeves",
                "ref_code": f"{prefix}-SH-03",
                "parent_id": cls.part_group.id,
            }
        )
        # Outside every profile.
        outside_defect_group = defect.create(
            {"name": "Packing", "ref_code": f"{prefix}-PACK"}
        )
        cls.outside_defect = defect.create(
            {
                "name": "Wrong label",
                "ref_code": f"{prefix}-PACK-01",
                "parent_id": outside_defect_group.id,
            }
        )
        outside_part_group = part.create(
            {"name": "Carton", "ref_code": f"{prefix}-CARTON"}
        )
        cls.outside_part = part.create(
            {
                "name": "Lid",
                "ref_code": f"{prefix}-CARTON-01",
                "parent_id": outside_part_group.id,
            }
        )

        cls.profile = cls.env["qms.catalog.profile"].create(
            {
                "name": f"Shirt {prefix}",
                "defect_group_ids": [(6, 0, cls.defect_group.ids)],
                "object_part_group_ids": [(6, 0, cls.part_group.ids)],
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Shirt", "qms_profile_ids": [(6, 0, cls.profile.ids)]}
        )
        cls.bare_product = cls.env["product.product"].create({"name": "Unprofiled"})

    def _nonconformity(self, product=None):
        user = self.env.user
        values = {
            "description": "Filtering",
            "origin_ids": [
                (6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
            ],
            "responsible_user_id": user.id,
            "manager_user_id": user.id,
            "user_id": user.id,
        }
        if product is not None:
            values["product_id"] = product.id
        return self.env["mgmtsystem.nonconformity"].create(values)

    def _item(self, nonconformity):
        return self.env["qms.nonconformity.item"].create(
            {
                "nonconformity_id": nonconformity.id,
                "defect_code_id": self.torn.id,
            }
        )

    def _codes(self, item):
        """What each dropdown would offer, by running the computed domains."""
        return (
            self.env["qms.defect.code"].search(item.qms_defect_code_domain),
            self.env["qms.object.part"].search(item.qms_object_part_domain),
        )

    def test_domain_filters_to_profile(self):
        item = self._item(self._nonconformity(self.product))
        defects, parts = self._codes(item)
        self.assertIn(self.torn, defects)
        self.assertNotIn(self.outside_defect, defects)
        self.assertIn(self.sleeves, parts)
        self.assertNotIn(self.outside_part, parts)

    def test_domain_without_profile_is_unfiltered(self):
        """No profile means no filter -- what the static domain got wrong."""
        for nonconformity in (
            self._nonconformity(self.bare_product),
            self._nonconformity(),
        ):
            with self.subTest(product=nonconformity.product_id.display_name):
                item = self._item(nonconformity)
                defects, parts = self._codes(item)
                self.assertIn(self.torn, defects)
                self.assertIn(self.outside_defect, defects)
                self.assertIn(self.sleeves, parts)
                self.assertIn(self.outside_part, parts)

    def test_show_all_codes_widens_domain(self):
        nonconformity = self._nonconformity(self.product)
        item = self._item(nonconformity)
        self.assertNotIn(self.outside_defect, self._codes(item)[0])
        nonconformity.qms_show_all_codes = True
        defects, parts = self._codes(item)
        self.assertIn(self.outside_defect, defects)
        self.assertIn(self.outside_part, parts)

    def test_domain_never_returns_groups(self):
        """A group is a heading, in every branch of the compute."""
        nonconformity = self._nonconformity(self.product)
        item = self._item(nonconformity)
        for widened in (False, True):
            with self.subTest(show_all=widened):
                nonconformity.qms_show_all_codes = widened
                defects, parts = self._codes(item)
                self.assertNotIn(self.defect_group, defects)
                self.assertNotIn(self.part_group, parts)

    def test_domain_follows_profile_change(self):
        """The @api.depends path through nonconformity_id to the product."""
        nonconformity = self._nonconformity(self.bare_product)
        item = self._item(nonconformity)
        self.assertIn(self.outside_defect, self._codes(item)[0])
        self.bare_product.qms_profile_ids = self.profile
        self.assertNotIn(self.outside_defect, self._codes(item)[0])
