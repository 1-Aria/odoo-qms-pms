# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.qms_catalog.tests.common import unique_code_prefix


class TestDeterminationRule(TransactionCase):
    """at_install: the fixtures create catalog codes and causes only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        prefix = unique_code_prefix()
        defect = cls.env["qms.defect.code"]
        part = cls.env["qms.object.part"]

        qm_group = defect.create(
            {"name": "Fabric Defect", "ref_code": f"{prefix}-FAB", "domain_kind": "qm"}
        )
        cls.qm_code = defect.create(
            {
                "name": "Torn",
                "ref_code": f"{prefix}-FAB-01",
                "domain_kind": "qm",
                "parent_id": qm_group.id,
            }
        )
        pm_group = defect.create(
            {"name": "Mechanical", "ref_code": f"{prefix}-MECH", "domain_kind": "pm"}
        )
        cls.pm_code = defect.create(
            {
                "name": "Bearing failure",
                "ref_code": f"{prefix}-MECH-01",
                "domain_kind": "pm",
                "parent_id": pm_group.id,
            }
        )
        both_group = defect.create(
            {"name": "Handling", "ref_code": f"{prefix}-HAND", "domain_kind": "both"}
        )
        cls.both_code = defect.create(
            {
                "name": "Dropped",
                "ref_code": f"{prefix}-HAND-01",
                "domain_kind": "both",
                "parent_id": both_group.id,
            }
        )
        part_group = part.create(
            {
                "name": "Machine Assemblies",
                "ref_code": f"{prefix}-MACH",
                "domain_kind": "pm",
            }
        )
        cls.pm_part = part.create(
            {
                "name": "Needle bar",
                "ref_code": f"{prefix}-MA-01",
                "domain_kind": "pm",
                "parent_id": part_group.id,
            }
        )
        cls.cause = cls.env["mgmtsystem.nonconformity.cause"].create(
            {"name": "Machine fault"}
        )
        cls.model = cls.env["qms.determination.rule"]

    @mute_logger("odoo.sql_db")
    def test_rule_requires_condition(self):
        # The case @api.constrains would miss: no condition field is written.
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.model.create({"name": "Catch-all"})
            self.model.flush_model()

    @mute_logger("odoo.sql_db")
    def test_rule_clearing_last_condition(self):
        rule = self.model.create({"name": "Machine fault", "cause_id": self.cause.id})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            rule.write({"cause_id": False})
            self.model.flush_model()

    def test_rule_cause_only_allowed(self):
        rule = self.model.create({"name": "Machine fault", "cause_id": self.cause.id})
        self.assertEqual(rule.cause_id, self.cause)

    def test_domain_kind_clash_defect(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.model.create(
                {
                    "name": "Tear",
                    "domain_kind": "pm",
                    "defect_code_id": self.qm_code.id,
                }
            )

    def test_domain_kind_clash_object_part(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.model.create(
                {
                    "name": "Needle bar",
                    "domain_kind": "qm",
                    "object_part_id": self.pm_part.id,
                }
            )

    def test_domain_kind_both_accepted(self):
        both_rule = self.model.create(
            {
                "name": "Any tear",
                "domain_kind": "both",
                "defect_code_id": self.qm_code.id,
            }
        )
        qm_rule = self.model.create(
            {
                "name": "Dropped",
                "domain_kind": "qm",
                "defect_code_id": self.both_code.id,
            }
        )
        self.assertEqual(both_rule.defect_code_id, self.qm_code)
        self.assertEqual(qm_rule.defect_code_id, self.both_code)

    def test_domain_kind_rule_narrowed(self):
        rule = self.model.create(
            {
                "name": "Bearing",
                "domain_kind": "both",
                "defect_code_id": self.pm_code.id,
            }
        )
        with self.assertRaises(ValidationError), self.cr.savepoint():
            rule.write({"domain_kind": "qm"})

    @mute_logger("odoo.sql_db")
    def test_condition_restrict(self):
        self.model.create({"name": "Tear", "defect_code_id": self.qm_code.id})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.qm_code.unlink()
