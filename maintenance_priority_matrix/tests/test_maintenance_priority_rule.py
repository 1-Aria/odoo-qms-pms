# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestPriorityRule(TransactionCase):
    """The rule grid, its lookup, and criticality on equipment.

    post_install: the fixtures create equipment and a second company.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule_model = cls.env["maintenance.priority.rule"]
        cls.company = cls.env.company
        cls.other_company = cls.env["res.company"].create({"name": "Second plant"})
        cls.critical_category = cls.env["maintenance.equipment.category"].create(
            {"name": "Sewing machines", "criticality": "a"}
        )
        cls.important_category = cls.env["maintenance.equipment.category"].create(
            {"name": "Cutting tables", "criticality": "b"}
        )
        cls.plain_category = cls.env["maintenance.equipment.category"].create(
            {"name": "Office equipment"}
        )

    def _rule(self, **values):
        values.setdefault("criticality", "a")
        values.setdefault("urgency", "line_stopped")
        values.setdefault("priority", "3")
        return self.rule_model.create(values)

    # -- the grid ---------------------------------------------------------

    @mute_logger("odoo.sql_db")
    def test_rule_uniqueness_global(self):
        """Two company-less rows for one pair.

        The case a plain unique constraint missed: PostgreSQL treats NULL
        company_ids as distinct, so nothing was refused. The index over
        COALESCE(company_id, -1) is what refuses it, at the INSERT.
        """
        self._rule()
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._rule(priority="2")

    @mute_logger("odoo.sql_db")
    def test_rule_uniqueness_within_company(self):
        self._rule(company_id=self.company.id)
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._rule(priority="2", company_id=self.company.id)

    @mute_logger("odoo.sql_db")
    def test_rule_uniqueness_ignores_archived(self):
        """A retired row still occupies its pair."""
        archived = self._rule()
        archived.active = False
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self._rule(priority="2")

    @mute_logger("odoo.sql_db")
    def test_duplicate_by_write_refused(self):
        """Editing a row in the grid into a duplicate is refused too.

        By the database, not by a Python constraint: a constraint's own search()
        flushes the pending row first (models.py:5795), so the index raises
        before any check could compare anything. The message is therefore the
        raw duplicate-key one on every path.
        """
        self._rule(urgency="line_stopped")
        other = self._rule(urgency="degraded", priority="1")
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            other.urgency = "line_stopped"

    def test_rule_per_company_allowed(self):
        """Two companies may disagree about the same pair."""
        self._rule()
        other = self._rule(priority="2", company_id=self.other_company.id)
        self.assertEqual(other.priority, "2")

    def test_rule_priority_selection_is_the_requests(self):
        """The rule cannot offer a value a request could not hold."""
        rule_values = dict(
            self.rule_model._fields["priority"]._description_selection(self.env)
        )
        request_values = dict(
            self.env["maintenance.request"]
            ._fields["priority"]
            ._description_selection(self.env)
        )
        self.assertEqual(rule_values, request_values)

    # -- the lookup -------------------------------------------------------

    def test_priority_for_match(self):
        self._rule(criticality="b", urgency="degraded", priority="1")
        self.assertEqual(
            self.rule_model._priority_for("b", "degraded"),
            "1",
        )

    def test_priority_for_no_match(self):
        """The unconfigured state: no row, or an incomplete pair, gives False."""
        self._rule(criticality="b", urgency="degraded", priority="1")
        self.assertFalse(self.rule_model._priority_for("c", "no_impact"))
        self.assertFalse(self.rule_model._priority_for(False, "degraded"))
        self.assertFalse(self.rule_model._priority_for("b", False))

    def test_priority_for_prefers_company_row(self):
        """A company's own row wins over the grid everyone shares."""
        self._rule(criticality="c", urgency="safety", priority="1")
        self._rule(
            criticality="c",
            urgency="safety",
            priority="3",
            company_id=self.company.id,
        )
        self.assertEqual(self.rule_model._priority_for("c", "safety"), "3")
        self.assertEqual(
            self.rule_model._priority_for(
                "c", "safety", company=self.other_company
            ),
            "1",
        )

    # -- criticality on equipment -----------------------------------------

    def test_equipment_criticality_from_category(self):
        equipment = self.env["maintenance.equipment"].create(
            {"name": "Overlock 1", "category_id": self.critical_category.id}
        )
        self.assertEqual(equipment.criticality, "a")

        # A value set by hand stands.
        equipment.criticality = "c"
        equipment.name = "Overlock 1 (rebuilt)"
        self.assertEqual(equipment.criticality, "c")

        # Re-categorising re-derives it: the machine is being reclassified.
        equipment.category_id = self.important_category
        self.assertEqual(equipment.criticality, "b")

        # A category with no criticality assigns nothing rather than clearing.
        equipment.category_id = self.plain_category
        self.assertEqual(equipment.criticality, "b")
