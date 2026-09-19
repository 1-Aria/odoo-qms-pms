# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from .common import CatalogCommon


class TestQmsDefectCode(CatalogCommon, TransactionCase):
    model_name = "qms.defect.code"


class TestQmsObjectPart(CatalogCommon, TransactionCase):
    model_name = "qms.object.part"


class TestCatalogIndependence(TransactionCase):
    def test_ref_code_shared_across_catalogs(self):
        """Each catalog owns its codes: uniqueness is per table."""
        values = {"name": "Shared", "ref_code": "SHARED", "domain_kind": "both"}
        defect_code = self.env["qms.defect.code"].create(values)
        object_part = self.env["qms.object.part"].create(values)
        self.env.flush_all()
        self.assertTrue(defect_code.exists())
        self.assertTrue(object_part.exists())
