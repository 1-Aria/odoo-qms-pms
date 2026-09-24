# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestQmsMaintenance(TransactionCase):
    """The nonconformity link, the prefill, and the widened action count.

    post_install: the fixtures create a product, equipment, nonconformities and
    users.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prefix = unique_code_prefix()

        # A product carrying a catalog profile, so the prefill can be shown to
        # reach the same catalogs the quality side uses.
        defect = cls.env["qms.defect.code"]
        group = defect.create(
            {"name": "Mechanical", "ref_code": f"{cls.prefix}-MECH", "domain_kind": "pm"}
        )
        defect.create(
            {
                "name": "Bearing failure",
                "ref_code": f"{cls.prefix}-MECH-01",
                "domain_kind": "pm",
                "parent_id": group.id,
            }
        )
        cls.profile = cls.env["qms.catalog.profile"].create(
            {
                "name": f"Sewing machine {cls.prefix}",
                "domain_kind": "pm",
                "defect_group_ids": [(6, 0, group.ids)],
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Sewing machine", "qms_profile_ids": [(6, 0, cls.profile.ids)]}
        )
        cls.equipment = cls.env["maintenance.equipment"].create(
            {"name": f"Machine {cls.prefix}", "product_id": cls.product.id}
        )
        cls.request = cls._request()

    @classmethod
    def _request(cls, equipment=None):
        return cls.env["maintenance.request"].create(
            {
                "name": "Needle bar seized",
                "equipment_id": (
                    equipment.id if equipment is not None else cls.equipment.id
                ),
            }
        )

    def _nonconformity(self, request=None, **values):
        user = self.env.user
        values.setdefault("description", "Machine down")
        values.setdefault(
            "origin_ids",
            [(6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)],
        )
        values.setdefault("responsible_user_id", user.id)
        values.setdefault("manager_user_id", user.id)
        values.setdefault("user_id", user.id)
        if request is not None:
            values.setdefault("qms_maintenance_request_id", request.id)
        return self.env["mgmtsystem.nonconformity"].create(values)

    def _action(self, **values):
        values.setdefault("name", "Replace the bearing")
        values.setdefault("type_action", "correction")
        return self.env["mgmtsystem.action"].create(values)

    def _user(self, *group_refs):
        return self.env["res.users"].create(
            {
                "name": "Test user",
                "login": f"qmsm-{self.prefix.lower()}-{len(group_refs)}",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref(ref).id
                            for ref in ("base.group_user",) + group_refs
                        ],
                    )
                ],
            }
        )

    # -- the link ---------------------------------------------------------

    def test_link_visible_both_ways(self):
        nonconformity = self._nonconformity(self.request)
        self.assertEqual(self.request.qms_nonconformity_ids, nonconformity)
        self.assertEqual(self.request.qms_nonconformity_count, 1)
        self._nonconformity(self.request)
        self.assertEqual(self.request.qms_nonconformity_count, 2)

    def test_request_delete_keeps_nonconformity(self):
        """The nonconformity outlives the request -- ondelete="set null"."""
        request = self._request()
        nonconformity = self._nonconformity(request)
        request.unlink()
        # The FK is cleared in the database; drop the cached value to read it.
        nonconformity.invalidate_recordset(["qms_maintenance_request_id"])
        self.assertTrue(nonconformity.exists())
        self.assertFalse(nonconformity.qms_maintenance_request_id)

    # -- the prefill ------------------------------------------------------

    def test_prefill_product_from_equipment(self):
        context = self.request._qms_nonconformity_context()
        self.assertEqual(context["default_product_id"], self.product.id)

        bare_equipment = self.env["maintenance.equipment"].create(
            {"name": f"Bare {self.prefix}"}
        )
        self.assertFalse(
            self._request(bare_equipment)._qms_nonconformity_context()[
                "default_product_id"
            ]
        )

        no_equipment = self.env["maintenance.request"].create({"name": "No equipment"})
        self.assertFalse(
            no_equipment._qms_nonconformity_context()["default_product_id"]
        )

    def test_view_nonconformities_domain_and_context(self):
        result = self.request.action_view_qms_nonconformities()
        self.assertEqual(result["res_model"], "mgmtsystem.nonconformity")
        self.assertEqual(result["view_mode"], "list,form")
        self.assertEqual(
            result["domain"],
            [("qms_maintenance_request_id", "=", self.request.id)],
        )
        self.assertEqual(
            result["context"],
            {
                "default_qms_maintenance_request_id": self.request.id,
                "default_equipment_id": self.equipment.id,
                "default_product_id": self.product.id,
                "default_name": self.request.name,
                "default_company_id": self.request.company_id.id,
            },
        )

    def test_prefill_scopes_catalog_dropdowns(self):
        """End to end: the maintenance side reaches the same catalogs.

        A nonconformity created through the button's context resolves the
        product's profiles, which is what 7.6 filters the defect and object-part
        dropdowns by.
        """
        context = self.request.action_view_qms_nonconformities()["context"]
        nonconformity = self.env["mgmtsystem.nonconformity"].with_context(
            **context
        ).create(
            {
                "description": "Bearing failure",
                "origin_ids": [
                    (6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "manager_user_id": self.env.user.id,
                "user_id": self.env.user.id,
            }
        )
        self.assertEqual(nonconformity.qms_maintenance_request_id, self.request)
        self.assertEqual(nonconformity.equipment_id, self.equipment)
        self.assertEqual(nonconformity.product_id, self.product)
        self.assertEqual(nonconformity.qms_effective_profile_ids, self.profile)

    # -- the widened action count ------------------------------------------

    def test_direct_action_counts(self):
        self._action(maintenance_request_id=self.request.id)
        self.assertEqual(self.request.action_count, 1)

    def test_nonconformity_action_counts(self):
        nonconformity = self._nonconformity(self.request)
        action = self._action(nonconformity_ids=[(4, nonconformity.id)])
        self.assertFalse(action.maintenance_request_id)
        self.assertEqual(self.request.action_count, 1)

    def test_immediate_action_counts(self):
        nonconformity = self._nonconformity(self.request)
        nonconformity.immediate_action_id = self._action()
        self.assertEqual(self.request.action_count, 1)

    def test_unrelated_action_does_not_count(self):
        other_request = self._request()
        self._action(
            nonconformity_ids=[(4, self._nonconformity(other_request).id)]
        )
        self._action(nonconformity_ids=[(4, self._nonconformity().id)])
        self.assertEqual(self.request.action_count, 0)
        self.assertEqual(other_request.action_count, 1)

    def test_action_reachable_twice_counts_once(self):
        nonconformity = self._nonconformity(self.request)
        self._action(
            maintenance_request_id=self.request.id,
            nonconformity_ids=[(4, nonconformity.id)],
        )
        self.assertEqual(self.request.action_count, 1)

    def test_action_count_refreshes_on_every_arm(self):
        """All three arms invalidate the count.

        The inherited action_ids dependency merges with the two declared here
        (fields.py:575-586), so this does not police the dependency list -- it
        proves each path reaches the count.
        """
        nonconformity = self._nonconformity(self.request)
        self.assertEqual(self.request.action_count, 0)
        self._action(maintenance_request_id=self.request.id)
        self.assertEqual(self.request.action_count, 1)
        self._action(nonconformity_ids=[(4, nonconformity.id)])
        self.assertEqual(self.request.action_count, 2)
        nonconformity.immediate_action_id = self._action()
        self.assertEqual(self.request.action_count, 3)

    # -- access (D31) -----------------------------------------------------

    def test_nonconformity_button_hidden_without_mgmtsystem(self):
        form = self.env.ref("maintenance.hr_equipment_request_view_form")
        model = self.env["maintenance.request"]
        viewer = self._user("mgmtsystem.group_mgmtsystem_viewer")
        self.assertIn(
            "qms_nonconformity_count",
            model.with_user(viewer).get_view(form.id, "form")["arch"],
        )
        plain = self._user()
        arch = model.with_user(plain).get_view(form.id, "form")["arch"]
        self.assertNotIn("qms_nonconformity_count", arch)
