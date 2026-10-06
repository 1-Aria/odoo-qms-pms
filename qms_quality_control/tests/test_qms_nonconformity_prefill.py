# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestNonconformityPrefill(TransactionCase):
    """What the inspection's Nonconformities button hands the client.

    That dictionary is the whole of step 4, so every test reads it.
    post_install: the fixtures create a product and nonconformities.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test = cls.env["qc.test"].create(
            {
                "name": "Shirt inspection",
                "test_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Fabric intact?",
                            "type": "qualitative",
                            "ql_values": [(0, 0, {"name": "Yes", "ok": True})],
                        },
                    )
                ],
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Shirt"})
        cls.inspection = cls.env["qc.inspection"].create(
            {
                "object_id": f"product.product,{cls.product.id}",
                "test": cls.test.id,
            }
        )
        cls.inspection.state = "failed"

    def _nonconformity(self, inspection=None):
        user = self.env.user
        return self.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Prefill",
                "origin_ids": [
                    (6, 0, self.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
                "qc_inspection_id": inspection and inspection.id or False,
            }
        )

    def _expected_context(self, inspection=None, product=True):
        inspection = inspection or self.inspection
        return {
            "search_default_qc_inspection_id": inspection.id,
            "default_qc_inspection_id": inspection.id,
            "default_product_id": self.product.id if product else False,
            "default_name": inspection.name,
            "default_company_id": inspection.company_id.id,
        }

    def test_defaults_with_no_nonconformity(self):
        """A new form, carrying the defaults."""
        result = self.inspection.action_view_nonconformities()
        self.assertFalse(result["res_id"])
        self.assertEqual(result["context"], self._expected_context())

    def test_defaults_with_one_nonconformity(self):
        nonconformity = self._nonconformity(self.inspection)
        result = self.inspection.action_view_nonconformities()
        self.assertEqual(result["res_id"], nonconformity.id)
        self.assertEqual(result["context"], self._expected_context())

    def test_defaults_with_several_nonconformities(self):
        """The OCA gap: a domain but no defaults, so New prefilled nothing."""
        first = self._nonconformity(self.inspection)
        second = self._nonconformity(self.inspection)
        result = self.inspection.action_view_nonconformities()
        self.assertEqual(result["domain"], [("id", "in", (first | second).ids)])
        self.assertEqual(result["context"], self._expected_context())

    def test_product_default_from_inspection(self):
        """What makes the 7.6 dropdowns work on the new record."""
        result = self.inspection.action_view_nonconformities()
        self.assertEqual(result["context"]["default_product_id"], self.product.id)

    def test_no_product_default_without_object(self):
        """The same result a picking-based inspection gives, and by design."""
        inspection = self.env["qc.inspection"].create({"test": self.test.id})
        self.assertFalse(inspection.product_id)
        result = inspection.action_view_nonconformities()
        self.assertEqual(
            result["context"], self._expected_context(inspection, product=False)
        )

    def test_user_filter_dropped(self):
        """The list shows the inspection's nonconformities, not only mine."""
        self._nonconformity(self.inspection)
        self._nonconformity(self.inspection)
        result = self.inspection.action_view_nonconformities()
        self.assertNotIn("search_default_user_id", result["context"])

    # -- users outside Settings (step 6) --------------------------------------

    def _user_outside_settings(self):
        """A quality and management-system user, no administrator."""
        xmlids = (
            "base.group_user",
            "quality_control_oca.group_quality_control_user",
            "mgmtsystem.group_mgmtsystem_user",
        )
        return self.env["res.users"].create(
            {
                "name": "Inspector",
                "login": f"{unique_code_prefix()}-inspector",
                "groups_id": [(6, 0, [self.env.ref(xmlid).id for xmlid in xmlids])],
            }
        )

    def test_button_for_user_outside_settings(self):
        user = self._user_outside_settings()
        result = self.inspection.with_user(user).action_view_nonconformities()
        self.assertEqual(
            result["context"]["default_qc_inspection_id"], self.inspection.id
        )

        # The control: the read OCA's method makes, refused to this user.
        action = self.env.ref(
            "mgmtsystem_nonconformity.open_mgmtsystem_nonconformity_list"
        )
        with self.assertRaises(AccessError):
            action.with_user(user).read(["name"])

    def test_button_ignores_other_company(self):
        """A superuser count would open a record the user cannot read."""
        other = self.env["res.company"].create(
            {"name": f"{unique_code_prefix()} Other company"}
        )
        nonconformity = self._nonconformity(self.inspection)
        nonconformity.company_id = other
        user = self._user_outside_settings()
        self.assertNotIn(other, user.company_ids)

        result = self.inspection.with_user(user).action_view_nonconformities()
        self.assertFalse(result["res_id"])
