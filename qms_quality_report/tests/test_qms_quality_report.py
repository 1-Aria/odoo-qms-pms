# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.qms_catalog.tests.common import unique_code_prefix
from odoo.addons.qms_quality_control.models.mgmtsystem_nonconformity import (
    INSPECTION_DONE_STATES,
)


@tagged("post_install", "-at_install")
class TestQualityReport(TransactionCase):
    """The figures the analyses sum, and the domains that choose the rows.

    post_install: the fixtures create products, a production order and work
    centres.
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
        cls.test = cls._test("Shirt inspection", ("Seams intact?", "Fabric intact?"))
        cls.roll_test = cls._test(
            "Fabric check", ("Hand feel",), qms_roll_inspection=True
        )
        cls.product = cls.env["product.product"].create({"name": "Shirt"})
        workcenter = cls.env["mrp.workcenter"]
        cls.sewing = workcenter.create({"name": f"{prefix} Sewing"})
        cls.finishing = workcenter.create({"name": f"{prefix} Finishing"})

    @classmethod
    def _test(cls, name, questions, **values):
        """A test of qualitative questions, each failing answer carrying Torn."""
        return cls.env["qc.test"].create(
            dict(
                values,
                name=name,
                test_lines=[
                    (
                        0,
                        0,
                        {
                            "name": question,
                            "type": "qualitative",
                            "ql_values": [
                                (0, 0, {"name": "OK", "ok": True}),
                                (
                                    0,
                                    0,
                                    {
                                        "name": "Not OK",
                                        "qms_defect_code_id": cls.torn.id,
                                    },
                                ),
                            ],
                        },
                    )
                    for question in questions
                ],
            )
        )

    def _production(self, *workcenters):
        """A production order without a BoM, one work order per work centre."""
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product.id,
                "product_qty": 10.0,
                "product_uom_id": self.product.uom_id.id,
            }
        )
        for workcenter in workcenters:
            self._workorder(production, workcenter)
        return production

    def _workorder(self, production, workcenter):
        return self.env["mrp.workorder"].create(
            {
                "name": workcenter.name,
                "workcenter_id": workcenter.id,
                "product_uom_id": self.product.uom_id.id,
                "production_id": production.id,
            }
        )

    def _inspection(self, test=None, production=None, state="ready"):
        """An inspection with every question answered OK, in `state`.

        On the production order when one is given: the MRP bridge sets
        production_id from object_id only, and the product then comes from the
        order.
        """
        test = test or self.test
        target = production or self.product
        inspection = self.env["qc.inspection"].create(
            {"object_id": f"{target._name},{target.id}", "test": test.id}
        )
        inspection.inspection_lines = inspection._prepare_inspection_lines(test)
        for line in inspection.inspection_lines:
            line.qualitative_value = line.possible_ql_values.filtered("ok")
        inspection.state = state
        return inspection

    def _fail(self, line, qty=0.0):
        line.qualitative_value = line.possible_ql_values.filtered(
            lambda value: not value.ok
        )
        line.qms_qty_failed = qty

    # -- defects on the line and the inspection -------------------------------

    def test_line_defects_entered(self):
        line = self._inspection().inspection_lines[0]
        self._fail(line, 3.0)
        self.assertEqual(line.qms_qty_defects, 3.0)

    def test_line_defects_at_least_one(self):
        line = self._inspection().inspection_lines[0]
        self._fail(line)
        self.assertEqual(line.qms_qty_defects, 1.0)

    def test_line_defects_passing_ignored(self):
        line = self._inspection().inspection_lines[0]
        line.qms_qty_failed = 2.0
        self.assertEqual(line.qms_qty_defects, 0.0)
        self._fail(line, 2.0)
        self.assertEqual(line.qms_qty_defects, 2.0)

    def test_inspection_defects_sum(self):
        inspection = self._inspection()
        first, second = inspection.inspection_lines
        self._fail(first, 3.0)
        self._fail(second)
        self.assertEqual(inspection.qms_qty_defects, 4.0)
        first.qms_qty_failed = 5.0
        self.assertEqual(inspection.qms_qty_defects, 6.0)

    def test_defect_free_follows_success(self):
        inspection = self._inspection()
        self.assertEqual(inspection.qms_defect_free, 100.0)
        self._fail(inspection.inspection_lines[0])
        self.assertEqual(inspection.qms_defect_free, 0.0)

    # -- work centre ----------------------------------------------------------

    def test_workcenter_single(self):
        production = self._production(self.sewing, self.sewing)
        inspection = self._inspection(production=production)
        self.assertEqual(inspection.production_id, production)
        self.assertEqual(inspection.qms_workcenter_id, self.sewing)

    def test_workcenter_several_or_none(self):
        production = self._production(self.sewing)
        inspection = self._inspection(production=production)
        self.assertEqual(inspection.qms_workcenter_id, self.sewing)
        self._workorder(production, self.finishing)
        self.assertFalse(inspection.qms_workcenter_id)

        self.assertFalse(self._inspection().qms_workcenter_id)

    # -- grouping by related fields --------------------------------------------

    def test_related_dimensions_group(self):
        """Non-stored related fields group by joining along their path."""
        inspection = self._inspection()
        lines = self.env["qc.inspection.line"]
        domain = [("id", "in", inspection.inspection_lines.ids)]
        for groupby in (
            "qms_partner_id",
            "qms_workcenter_id",
            "qms_test_category_id",
            "qms_inspection_date:month",
        ):
            with self.subTest(groupby=groupby):
                groups = lines._read_group(domain, [groupby], ["__count"])
                self.assertEqual(sum(count for __, count in groups), 2)
        groups = self.env["qc.inspection"]._read_group(
            [("id", "=", inspection.id)], ["qms_partner_id"], ["__count"]
        )
        self.assertEqual(sum(count for __, count in groups), 1)

    # -- the actions' domains --------------------------------------------------

    def test_inspection_action_domain(self):
        action = self.env.ref("qms_quality_report.qc_inspection_report_action")
        domain = safe_eval(action.domain)
        self.assertEqual(
            domain,
            [
                ("state", "in", INSPECTION_DONE_STATES),
                ("qms_roll_inspection", "=", False),
            ],
        )

        by_state = {
            state: self._inspection(state=state)
            for state in ("ready", "waiting", "success", "failed")
        }
        roll = self._inspection(test=self.roll_test, state="success")
        candidates = roll.browse([i.id for i in by_state.values()] + [roll.id])
        found = self.env["qc.inspection"].search(
            domain + [("id", "in", candidates.ids)]
        )
        self.assertEqual(
            found, by_state["waiting"] | by_state["success"] | by_state["failed"]
        )

    def test_defect_action_domain(self):
        action = self.env.ref("qms_quality_report.qc_inspection_line_report_action")
        domain = safe_eval(action.domain)

        finished = self._inspection(state="failed")
        failed_line, passing_line = finished.inspection_lines
        self._fail(failed_line)
        unfinished = self._inspection(state="ready")
        self._fail(unfinished.inspection_lines[0])

        candidates = finished.inspection_lines | unfinished.inspection_lines
        found = self.env["qc.inspection.line"].search(
            domain + [("id", "in", candidates.ids)]
        )
        self.assertEqual(found, failed_line)

    # -- access --------------------------------------------------------------

    def test_menu_for_managers(self):
        menu = self.env.ref("qms_quality_report.menu_qms_quality_report")
        self.assertEqual(
            menu.groups_id,
            self.env.ref("quality_control_oca.group_quality_control_manager"),
        )
