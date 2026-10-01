# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestSlaRule(TransactionCase):
    """SLA rules, their constraints, and the cancel flag on stages.

    at_install: the fixtures create stages and rules only, neither of which a
    later module extends with a required column.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule_model = cls.env["maintenance.sla"]
        # The fixtures create their own stages and never read the instance's:
        # the stage list is configuration a site owns, and requests point at it,
        # so it cannot be cleared the way the priority grid's tests clear theirs.
        cls.stage_new, cls.stage_progress, cls.stage_waiting, cls.stage_scrap = (
            cls.env["maintenance.stage"].create(
                [
                    {"name": "SLA test: new", "sequence": 901},
                    {"name": "SLA test: in progress", "sequence": 902},
                    {"name": "SLA test: waiting", "sequence": 903},
                    {
                        "name": "SLA test: scrap",
                        "sequence": 904,
                        "sla_cancel": True,
                    },
                ]
            )
        )

    def _rule(self, **values):
        values.setdefault("name", "Response")
        values.setdefault("maintenance_type", "corrective")
        values.setdefault("target_stage_id", self.stage_progress.id)
        values.setdefault("duration", 1.0)
        return self.rule_model.create(values)

    # -- the target -------------------------------------------------------

    @mute_logger("odoo.sql_db")
    def test_rule_requires_a_target(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.rule_model.create(
                {"name": "No target", "maintenance_type": "corrective", "duration": 1.0}
            )

    def test_target_may_not_be_a_cancel_stage(self):
        with self.assertRaises(ValidationError):
            self._rule(target_stage_id=self.stage_scrap.id)
        rule = self._rule()
        with self.assertRaises(ValidationError):
            rule.target_stage_id = self.stage_scrap

    def test_cancel_flag_refused_on_a_target(self):
        """The constraint read from the stage's end, archived rules included."""
        # Positive control: a stage no rule targets may be flagged.
        self.stage_new.sla_cancel = True
        self.assertTrue(self.stage_new.sla_cancel)
        self._rule()
        with self.assertRaises(ValidationError):
            self.stage_progress.sla_cancel = True
        self._rule(target_stage_id=self.stage_waiting.id, active=False)
        with self.assertRaises(ValidationError):
            self.stage_waiting.sla_cancel = True

    # -- stages a rule depends on -----------------------------------------

    @mute_logger("odoo.sql_db")
    def test_target_stage_delete_restricted(self):
        self._rule()
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.stage_progress.unlink()
        # Positive control: a stage no rule uses can be deleted.
        self.stage_new.unlink()
        self.assertFalse(self.stage_new.exists())

    @mute_logger("odoo.sql_db")
    def test_pause_stage_delete_restricted(self):
        self._rule(pause_stage_ids=[Command.set(self.stage_waiting.ids)])
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.stage_waiting.unlink()

    # -- the domain -------------------------------------------------------

    def test_domain_refused_when_malformed(self):
        with self.assertRaises(ValidationError):
            self._rule(domain="[('priority', '=', '3'")

    def test_domain_refused_when_dynamic(self):
        with self.assertRaises(ValidationError) as caught:
            self._rule(domain="[('user_id', '=', uid)]")
        # literal_eval's own failure, passed through to the message.
        self.assertIn("malformed", str(caught.exception))

    def test_domain_refused_on_unknown_field(self):
        """Parses as a literal, so only the expression check catches it."""
        with self.assertRaises(ValidationError):
            self._rule(domain="[('no_such_field', '=', 1)]")
        # Positive control, and the write path.
        rule = self._rule(domain="[('priority', '=', '3')]")
        with self.assertRaises(ValidationError):
            rule.domain = "[('no_such_field', '=', 1)]"

    def test_parsed_domain(self):
        rule = self._rule(domain="[('priority', '=', '3')]")
        self.assertEqual(rule._parsed_domain(), [("priority", "=", "3")])
        self.assertEqual(self._rule()._parsed_domain(), [])

    # -- the selections ---------------------------------------------------

    def test_selections_are_the_requests(self):
        """A rule cannot key on a value a request could not hold."""
        request_fields = self.env["maintenance.request"]._fields
        for name in ("priority", "maintenance_type"):
            with self.subTest(field=name):
                self.assertEqual(
                    dict(self.rule_model._fields[name]._description_selection(self.env)),
                    dict(request_fields[name]._description_selection(self.env)),
                )
