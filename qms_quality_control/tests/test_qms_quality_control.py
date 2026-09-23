# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


class TestChecklistDefectCode(TransactionCase):
    """at_install: the fixtures create catalog codes and QC test records only.

    The two field domains are dropdown filters, so they are checked in the UI
    rather than here -- a search domain constrains nothing a test does.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]

        group = defect.create(
            {"name": "Fabric Defect", "ref_code": f"{prefix}-FAB", "domain_kind": "qm"}
        )
        cls.torn = defect.create(
            {
                "name": "Torn",
                "ref_code": f"{prefix}-FAB-01",
                "domain_kind": "qm",
                "parent_id": group.id,
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
        # A qualitative question needs at least one answer marked ok
        # (qc.test.question._check_valid_answers).
        cls.question_ql = cls.env["qc.test.question"].create(
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
        cls.answer_fail = cls.question_ql.ql_values.filtered(lambda v: not v.ok)
        cls.question_qt = cls.env["qc.test.question"].create(
            {
                "test": cls.test.id,
                "name": "Seam strength",
                "type": "quantitative",
                "min_value": 10.0,
                "max_value": 20.0,
                "qms_defect_code_id": cls.undersize.id,
            }
        )

    def test_answer_takes_defect_code(self):
        self.assertEqual(self.answer_fail.qms_defect_code_id, self.torn)
        # The correct answer carries none: only a failure is a defect.
        correct = self.question_ql.ql_values.filtered("ok")
        self.assertFalse(correct.qms_defect_code_id)

    def test_question_takes_defect_code(self):
        self.assertEqual(self.question_qt.qms_defect_code_id, self.undersize)

    @mute_logger("odoo.sql_db")
    def test_answer_defect_code_restrict(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.torn.unlink()

    @mute_logger("odoo.sql_db")
    def test_question_defect_code_restrict(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.undersize.unlink()
