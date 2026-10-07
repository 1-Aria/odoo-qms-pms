# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestCapture(TransactionCase):
    """The snapshot on the line and the counts on the inspection.

    post_install: the fixtures create a product.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        severity = cls.env["mgmtsystem.nonconformity.severity"]
        cls.major = severity.create({"name": "Major", "qms_severity_rank": 20})
        cls.minor = severity.create({"name": "Minor", "qms_severity_rank": 10})
        group = defect.create(
            {"name": "Fabric Defect", "ref_code": f"{prefix}-FAB", "domain_kind": "qm"}
        )
        cls.torn = defect.create(
            {
                "name": "Torn",
                "ref_code": f"{prefix}-FAB-01",
                "domain_kind": "qm",
                "parent_id": group.id,
                "default_severity_id": cls.major.id,
            }
        )
        cls.undersize = defect.create(
            {
                "name": "Out of tolerance",
                "ref_code": f"{prefix}-FAB-02",
                "domain_kind": "qm",
                "parent_id": group.id,
            }
        )

        cls.test = cls.env["qc.test"].create({"name": "Shirt inspection"})
        question = cls.env["qc.test.question"]
        cls.question_ql = question.create(
            {
                "test": cls.test.id,
                "name": "Fabric intact?",
                "type": "qualitative",
                "ql_values": [
                    (0, 0, {"name": "Yes", "ok": True}),
                    (0, 0, {"name": "No", "qms_defect_code_id": cls.torn.id}),
                ],
            }
        )
        cls.answer_ok = cls.question_ql.ql_values.filtered("ok")
        cls.answer_fail = cls.question_ql.ql_values - cls.answer_ok
        cls.question_qt = question.create(
            {
                "test": cls.test.id,
                "name": "Seam strength",
                "type": "quantitative",
                "min_value": 10.0,
                "max_value": 20.0,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "qms_defect_code_id": cls.undersize.id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Shirt"})

    def _inspection(self, qty=100.0):
        """A ready inspection, both questions answered within tolerance."""
        inspection = self.env["qc.inspection"].create(
            {
                "object_id": f"product.product,{self.product.id}",
                "test": self.test.id,
                "qty": qty,
            }
        )
        inspection.inspection_lines = inspection._prepare_inspection_lines(self.test)
        inspection.state = "ready"
        line_ql, line_qt = inspection.inspection_lines
        line_ql.qualitative_value = self.answer_ok
        line_qt.quantitative_value = 15.0
        return inspection

    # -- the snapshot on the line ---------------------------------------------

    def test_severity_snapshot(self):
        line = self._inspection().inspection_lines[0]
        line.qualitative_value = self.answer_fail
        self.assertEqual(line.qms_severity_id, self.major)

        self.torn.default_severity_id = self.minor
        line.invalidate_recordset()
        self.assertEqual(line.qms_severity_id, self.major)

    def test_code_kept_when_question_deleted(self):
        """The reason test_line is not a dependency."""
        line = self._inspection().inspection_lines[1]
        line.quantitative_value = 5.0
        self.assertEqual(line.qms_defect_code_id, self.undersize)

        self.question_qt.unlink()
        line.invalidate_recordset()
        self.assertFalse(line.test_line)
        self.assertEqual(line.qms_defect_code_id, self.undersize)

    def test_code_follows_answer(self):
        line = self._inspection().inspection_lines[0]
        self.assertFalse(line.qms_defect_code_id)
        line.qualitative_value = self.answer_fail
        self.assertEqual(line.qms_defect_code_id, self.torn)
        line.qualitative_value = self.answer_ok
        self.assertFalse(line.qms_defect_code_id)

    # -- the counts on the inspection -----------------------------------------

    def test_inspected_follows_qty(self):
        inspection = self._inspection(qty=100.0)
        self.assertEqual(inspection.qms_qty_inspected, 100.0)
        inspection.qty = 120.0
        self.assertEqual(inspection.qms_qty_inspected, 120.0)

        inspection.qms_qty_sampled = 5.0
        self.assertEqual(inspection.qms_qty_inspected, 5.0)
        inspection.qty = 150.0
        self.assertEqual(inspection.qms_qty_inspected, 5.0)

        inspection.qms_qty_sampled = 0.0
        self.assertEqual(inspection.qms_qty_inspected, 150.0)

    def test_confirm_refuses_defective_over_inspected(self):
        """The check reads pieces inspected, not the lot."""
        inspection = self._inspection(qty=100.0)
        inspection.write({"qms_qty_sampled": 5.0, "qms_qty_defective": 6.0})
        with self.assertRaises(UserError):
            inspection.action_confirm()

        inspection.qms_qty_defective = 5.0
        inspection.action_confirm()
        self.assertEqual(inspection.state, "success")
