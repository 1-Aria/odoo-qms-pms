# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


class FabricInspectionCase(TransactionCase):
    """Fixtures and helpers shared by the module's tests.

    No test methods of its own, so nothing is collected from it. Subclasses are
    post_install: the fixtures create products and lots, core records later
    modules extend.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prefix = prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]

        cls.fabric_group = defect.create(
            {"name": "Fabric", "ref_code": f"{prefix}-FAB", "domain_kind": "qm"}
        )
        cls.hole = defect.create(
            {
                "name": "Hole",
                "ref_code": f"{prefix}-FAB-02",
                "domain_kind": "qm",
                "parent_id": cls.fabric_group.id,
            }
        )
        cls.slub = defect.create(
            {
                "name": "Slub",
                "ref_code": f"{prefix}-FAB-01",
                "domain_kind": "qm",
                "parent_id": cls.fabric_group.id,
            }
        )
        cls.seam_group = defect.create(
            {"name": "Seam", "ref_code": f"{prefix}-SEAM", "domain_kind": "qm"}
        )
        cls.open_seam = defect.create(
            {
                "name": "Open seam",
                "ref_code": f"{prefix}-SEAM-01",
                "domain_kind": "qm",
                "parent_id": cls.seam_group.id,
            }
        )
        profile = cls.env["qms.catalog.profile"].create(
            {
                "name": "Fabric",
                "domain_kind": "qm",
                "defect_group_ids": [(6, 0, cls.fabric_group.ids)],
            }
        )

        # Odoo 18 has no "product" type: an inventory product is a storable
        # consumable, and lots are offered only for tracked storable products.
        product = cls.env["product.product"]
        storable = {"type": "consu", "is_storable": True, "tracking": "lot"}
        cls.product = product.create(
            dict(storable, name="Fabric", qms_profile_ids=[(6, 0, profile.ids)])
        )
        cls.plain_product = product.create(
            dict(storable, name="Fabric without profile")
        )
        lot = cls.env["stock.lot"]
        cls.lot1, cls.lot2, cls.lot3 = (
            lot.create({"name": f"{prefix}DL-{n}", "product_id": cls.product.id})
            for n in (1, 2, 3)
        )

        cls.roll_test = cls._test(
            "Fabric check",
            qms_roll_inspection=True,
            qms_points_limit=28.0,
            qms_points_cap=4,
            qms_delta_e_max=1.0,
            qms_delta_e_length_max=0.8,
            qms_delta_e_width_max=0.8,
        )
        cls.plain_test = cls._test("Fabric check without rolls")

    @classmethod
    def _test(cls, name, **values):
        test = cls.env["qc.test"].create(dict(values, name=name))
        cls.env["qc.test.question"].create(
            {
                "test": test.id,
                "name": "Hand feel",
                "type": "qualitative",
                "ql_values": [
                    (0, 0, {"name": "OK", "ok": True}),
                    (0, 0, {"name": "Not OK"}),
                ],
            }
        )
        return test

    def _user_without_inventory(self, *groups):
        """A quality-control user holding no Inventory group.

        `groups` are further group XML ids the user should hold.
        """
        xmlids = (
            "base.group_user",
            "quality_control_oca.group_quality_control_user",
            *groups,
        )
        return self.env["res.users"].create(
            {
                "name": "Fabric inspector",
                "login": f"{self.prefix}-inspector",
                "groups_id": [(6, 0, [self.env.ref(xmlid).id for xmlid in xmlids])],
            }
        )

    def _inspect(self, test=None, target=None):
        """A ready inspection of `target`, its question answered OK.

        `target` is the record inspected, the profiled product by default. The
        test is set through the Set test wizard, the path that bypasses
        set_test, so the snapshot is proven on it.
        """
        target = target or self.product
        inspection = self.env["qc.inspection"].create(
            {"object_id": f"{target._name},{target.id}"}
        )
        self.env["qc.inspection.set.test"].with_context(
            active_id=inspection.id
        ).create({"test": (test or self.roll_test).id}).action_create_test()
        inspection.action_todo()
        line = inspection.inspection_lines
        line.qualitative_value = line.possible_ql_values.filtered("ok")
        return inspection

    def _roll(self, inspection, lot, length=0.0, width=0.0, points=(), **values):
        """A roll with one Slub entry per (position, points) pair."""
        return self.env["qms.inspection.roll"].create(
            {
                **values,
                "inspection_id": inspection.id,
                "lot_id": lot.id,
                "length": length,
                "width": width,
                "point_ids": [
                    (
                        0,
                        0,
                        {
                            "position": position,
                            "defect_code_id": self.slub.id,
                            "points": value,
                        },
                    )
                    for position, value in points
                ],
            }
        )
