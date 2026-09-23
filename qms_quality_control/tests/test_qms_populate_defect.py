# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


@tagged("post_install", "-at_install")
class TestPopulateDefect(TransactionCase):
    """Defect resolution on the line, the gate, and Populate Defect.

    post_install: the fixtures create a product and a nonconformity, core
    models later modules extend.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]

        cls.major = cls.env["mgmtsystem.nonconformity.severity"].create(
            {"name": "Major", "qms_severity_rank": 20}
        )
        group = defect.create(
            {
                "name": "Fabric Defect",
                "ref_code": f"{cls.prefix}-FAB",
                "domain_kind": "qm",
            }
        )
        cls.torn = defect.create(
            {
                "name": "Torn",
                "ref_code": f"{cls.prefix}-FAB-01",
                "domain_kind": "qm",
                "parent_id": group.id,
                "default_severity_id": cls.major.id,
            }
        )
        cls.undersize = defect.create(
            {
                "name": "Out of tolerance",
                "ref_code": f"{cls.prefix}-FAB-02",
                "domain_kind": "qm",
                "parent_id": group.id,
            }
        )
        cls.other = defect.create(
            {
                "name": "Stained",
                "ref_code": f"{cls.prefix}-FAB-03",
                "domain_kind": "qm",
                "parent_id": group.id,
            }
        )

        # A checklist with all three shapes: a coded qualitative question, a
        # coded quantitative one, and a qualitative one with no code at all.
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
                "qms_defect_code_id": cls.undersize.id,
            }
        )
        cls.question_uncoded = question.create(
            {
                "test": cls.test.id,
                "name": "Zipper present?",
                "type": "qualitative",
                "ql_values": [
                    (0, 0, {"name": "Yes", "ok": True}),
                    (0, 0, {"name": "No"}),
                ],
            }
        )
        answer_uncoded_fail = cls.question_uncoded.ql_values.filtered(
            lambda value: not value.ok
        )

        cls.product = cls.env["product.product"].create({"name": "Shirt"})
        cls.inspection = cls.env["qc.inspection"].create(
            {
                "object_id": f"product.product,{cls.product.id}",
                "test": cls.test.id,
                "inspection_lines": [
                    (
                        0,
                        0,
                        {
                            "name": cls.question_ql.name,
                            "test_line": cls.question_ql.id,
                            "question_type": "qualitative",
                            "possible_ql_values": [
                                (6, 0, cls.question_ql.ql_values.ids)
                            ],
                            "qualitative_value": cls.answer_fail.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": cls.question_qt.name,
                            "test_line": cls.question_qt.id,
                            "question_type": "quantitative",
                            "min_value": 10.0,
                            "max_value": 20.0,
                            "quantitative_value": 5.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": cls.question_uncoded.name,
                            "test_line": cls.question_uncoded.id,
                            "question_type": "qualitative",
                            "possible_ql_values": [
                                (6, 0, cls.question_uncoded.ql_values.ids)
                            ],
                            "qualitative_value": answer_uncoded_fail.id,
                        },
                    ),
                ],
            }
        )
        # Confirmed, by writing the state: action_confirm's own validation is
        # OCA's business and would drag fixtures along with it.
        cls.inspection.state = "failed"
        cls.line_ql, cls.line_qt, cls.line_uncoded = cls.inspection.inspection_lines

        cls.nonconformity = cls._nonconformity(inspection=cls.inspection)

    @classmethod
    def _nonconformity(cls, inspection=None):
        user = cls.env.user
        return cls.env["mgmtsystem.nonconformity"].create(
            {
                "description": "Populate Defect",
                "origin_ids": [
                    (6, 0, cls.env.ref("mgmtsystem_nonconformity.nc_origin_qc").ids)
                ],
                "responsible_user_id": user.id,
                "manager_user_id": user.id,
                "user_id": user.id,
                "qc_inspection_id": inspection and inspection.id or False,
                "stage_id": cls.env.ref(
                    "mgmtsystem_nonconformity.stage_analysis"
                ).id,
            }
        )

    def _item(self, **values):
        values.setdefault("defect_code_id", self.torn.id)
        values.setdefault("nonconformity_id", self.nonconformity.id)
        return self.env["qms.nonconformity.item"].create(values)

    # -- resolution on the line -------------------------------------------

    def test_resolves_qualitative_code(self):
        self.assertEqual(self.line_ql.qms_defect_code_id, self.torn)

    def test_resolves_quantitative_code(self):
        self.assertEqual(self.line_qt.qms_defect_code_id, self.undersize)

    def test_passing_line_resolves_nothing(self):
        self.line_ql.qualitative_value = self.answer_ok
        self.assertFalse(self.line_ql.qms_defect_code_id)
        self.line_qt.quantitative_value = 15.0
        self.assertFalse(self.line_qt.qms_defect_code_id)

    def test_unanswered_quantitative_resolves_code(self):
        """The residue the state gate does not remove.

        action_confirm asks only for a unit of measure on a quantitative
        question, so a confirmed inspection can hold a line nobody measured.
        It reads 0.0 and fails its minimum.
        """
        line = self.env["qc.inspection.line"].create(
            {
                "inspection_id": self.inspection.id,
                "name": "Unmeasured",
                "test_line": self.question_qt.id,
                "question_type": "quantitative",
                "min_value": 10.0,
                "max_value": 20.0,
            }
        )
        self.assertFalse(line.quantitative_value)
        self.assertEqual(line.qms_defect_code_id, self.undersize)

    def test_code_follows_checklist_edit(self):
        """Not stored: the line shows the checklist's current code."""
        self.answer_fail.qms_defect_code_id = self.other
        self.assertEqual(self.line_ql.qms_defect_code_id, self.other)

    # -- Populate Defect --------------------------------------------------

    def test_populate_creates_one_item_per_line(self):
        self.nonconformity.action_populate_defect()
        items = self.nonconformity.item_ids.sorted(
            lambda item: (item.sequence, item.id)
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(
            [item.defect_code_id for item in items], [self.torn, self.undersize]
        )
        self.assertEqual(items.mapped("sequence"), [10, 20])

    def test_populate_carries_note_and_severity(self):
        self.nonconformity.action_populate_defect()
        item = self.nonconformity.item_ids.filtered(
            lambda item: item.defect_code_id == self.torn
        )
        self.assertEqual(item.note, self.question_ql.name)
        self.assertEqual(item.severity_id, self.major)

    def test_populate_carries_quantity(self):
        """The failed quantity reaches the item; an uncoded line carries none."""
        self.line_ql.qms_qty_failed = 3.0
        self.line_qt.qms_qty_failed = 2.0
        self.line_uncoded.qms_qty_failed = 7.0
        self.nonconformity.action_populate_defect()
        quantities = {
            item.defect_code_id: item.qty_affected
            for item in self.nonconformity.item_ids
        }
        self.assertEqual(quantities, {self.torn: 3.0, self.undersize: 2.0})

    def test_populate_skips_uncoded_lines(self):
        self.assertFalse(self.line_uncoded.qms_defect_code_id)
        self.nonconformity.action_populate_defect()
        self.assertEqual(len(self.nonconformity.item_ids), 2)
        self.assertNotIn(
            self.question_uncoded.name, self.nonconformity.item_ids.mapped("note")
        )

    def test_populate_nothing_notifies(self):
        self.answer_fail.qms_defect_code_id = False
        self.question_qt.qms_defect_code_id = False
        result = self.nonconformity.action_populate_defect()
        self.assertFalse(self.nonconformity.item_ids)
        self.assertEqual(result["tag"], "display_notification")

    def test_populate_without_inspection(self):
        """Safe even where the button is hidden."""
        nonconformity = self._nonconformity()
        result = nonconformity.action_populate_defect()
        self.assertFalse(nonconformity.item_ids)
        self.assertEqual(result["tag"], "display_notification")

    # -- the gate ---------------------------------------------------------

    def test_gate_open_after_confirm(self):
        for state in ("waiting", "success", "failed"):
            with self.subTest(state=state):
                self.inspection.state = state
                self.assertTrue(self.nonconformity.qms_can_populate_defect)

    def test_gate_closed_before_confirm(self):
        for state in ("plan", "draft", "ready", "canceled"):
            with self.subTest(state=state):
                self.inspection.state = state
                self.assertFalse(self.nonconformity.qms_can_populate_defect)
        self.assertFalse(self._nonconformity().qms_can_populate_defect)

    def test_gate_closed_once_items_exist(self):
        item = self._item()
        self.assertFalse(self.nonconformity.qms_can_populate_defect)
        item.unlink()
        self.nonconformity.stage_id = self.env.ref(
            "mgmtsystem_nonconformity.stage_pending"
        )
        self.assertFalse(self.nonconformity.qms_can_populate_defect)

    def _mgmtsystem_user(self):
        """A management-system user with no quality-control group."""
        return self.env["res.users"].create(
            {
                "name": "Management system user",
                "login": f"ms-user-{self.prefix.lower()}",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("mgmtsystem.group_mgmtsystem_user").id,
                        ],
                    )
                ],
            }
        )

    def test_gate_requires_quality_control_group(self):
        """qc.inspection is readable by the quality-control group alone.

        The positive control matters: without it this test would pass for a
        user who cannot read the nonconformity either.
        """
        nonconformity = self.nonconformity.with_user(self._mgmtsystem_user())
        self.assertEqual(nonconformity.description, "Populate Defect")
        with self.assertRaises(AccessError):
            nonconformity.qms_can_populate_defect  # noqa: B018

    def test_view_hides_gate_without_quality_control(self):
        """The arch, not the compute.

        The test above proves the field is dangerous for this user; this one
        proves the view keeps it away from them, which is the only thing that
        stops the form raising on load. A comma in `groups` means "member of at
        least one", so a list naming the management-system group would pass
        this user through and read as a gate while gating nothing.
        """
        model = self.env["mgmtsystem.nonconformity"]
        form = self.env.ref(
            "mgmtsystem_nonconformity.view_mgmtsystem_nonconformity_form"
        )
        self.assertIn(
            "qms_can_populate_defect", model.get_view(form.id, "form")["arch"]
        )
        arch = (
            model.with_user(self._mgmtsystem_user())
            .get_view(form.id, "form")["arch"]
        )
        self.assertNotIn("qms_can_populate_defect", arch)
