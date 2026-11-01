# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

D = datetime.date


@tagged("post_install", "-at_install")
class TestStrictGet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Param = cls.env["base.time.parameter"]
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Strict Reader Test B"})
        cls.plain_user = cls.env["res.users"].create(
            {
                "name": "Strict Reader Plain User",
                "login": "test.strict.plain.user",
                "groups_id": [Command.set([cls.env.ref("base.group_user").id])],
                "company_id": cls.company_a.id,
                "company_ids": [Command.set([cls.company_a.id, cls.company_b.id])],
            }
        )

    def _param(self, code, kind, versions, company=False):
        return self.Param.create(
            {
                "name": code,
                "code": f"test.strict.{code}",
                "type": kind,
                "company_id": company.id if company else False,
                "version_ids": [
                    Command.create({"date_from": date_from, "value": value})
                    for date_from, value in versions
                ],
            }
        )

    def _get(self, code, date, company=None):
        return self.Param._strict_get(f"test.strict.{code}", date, company=company)

    def test_zero_float_is_value(self):
        self._param("zero", "float", [(D(2026, 1, 1), "0.0")])
        self.assertEqual(self._get("zero", D(2026, 6, 1)), 0.0)

    def test_false_boolean_is_value(self):
        self._param("flag", "boolean", [(D(2026, 1, 1), "False")])
        self.assertIs(self._get("flag", D(2026, 6, 1)), False)

    def test_latest_version_before_date(self):
        self._param(
            "ref",
            "float",
            [(D(2026, 1, 1), "2340000"), (D(2026, 7, 1), "2530000")],
        )
        self.assertEqual(self._get("ref", D(2026, 6, 30)), 2340000.0)
        self.assertEqual(self._get("ref", D(2026, 7, 1)), 2530000.0)
        self.assertEqual(self._get("ref", D(2026, 12, 31)), 2530000.0)

    def test_before_first_version_raises(self):
        self._param("ref", "float", [(D(2026, 1, 1), "2340000")])
        with self.assertRaises(UserError):
            self._get("ref", D(2025, 12, 31))

    def test_missing_code_raises(self):
        with self.assertRaises(UserError) as caught:
            self._get("nowhere", D(2026, 6, 1))
        self.assertIn("test.strict.nowhere", str(caught.exception))

    def test_company_overrides_no_company(self):
        self._param("rate", "float", [(D(2026, 1, 1), "1.0")], company=self.company_b)
        self._param("rate", "float", [(D(2026, 1, 1), "2.0")])
        self.assertEqual(self._get("rate", D(2026, 6, 1), company=self.company_b), 1.0)
        self.assertEqual(self._get("rate", D(2026, 6, 1), company=self.company_a), 2.0)
        self.assertEqual(self._get("rate", D(2026, 6, 1)), 2.0)

    def test_ambiguous_no_company_raises(self):
        self._param("twice", "float", [(D(2026, 1, 1), "1.0")])
        self._param("twice", "float", [(D(2026, 1, 1), "2.0")])
        with self.assertRaises(UserError):
            self._get("twice", D(2026, 6, 1))

    def test_types(self):
        self._param("int", "integer", [(D(2026, 1, 1), "26")])
        self._param("int_float", "integer", [(D(2026, 1, 1), "26.0")])
        self._param("date", "date", [(D(2026, 1, 1), "2026-10-24")])
        self._param("json", "json", [(D(2026, 1, 1), '{"IV": 3700000}')])
        self._param("text", "string", [(D(2026, 1, 1), "IV")])
        on = D(2026, 6, 1)
        self.assertEqual(self._get("int", on), 26)
        self.assertIsInstance(self._get("int", on), int)
        self.assertEqual(self._get("int_float", on), 26)
        self.assertEqual(self._get("date", on), D(2026, 10, 24))
        self.assertEqual(self._get("json", on), {"IV": 3700000})
        self.assertEqual(self._get("text", on), "IV")

    def test_record_type(self):
        # value_reference has an empty selection in OCA, so the ORM refuses any
        # value; a module adding its model to the selection could store one.
        # The test writes it through SQL, which is how such a value is read back.
        param = self._param("record", "record", [(D(2026, 1, 1), False)])
        version = param.version_ids
        with self.assertRaises(UserError):
            self._get("record", D(2026, 6, 1))
        self.env.cr.execute(
            "UPDATE base_time_parameter_version SET value_reference = %s WHERE id = %s",
            (f"res.company,{self.company_b.id}", version.id),
        )
        version.invalidate_recordset(["value_reference"])
        self.assertEqual(self._get("record", D(2026, 6, 1)), self.company_b)

    def test_invalid_values_raise(self):
        cases = [
            ("bad_float", "float", "abc"),
            ("bad_int", "integer", "26.5"),
            ("bad_bool", "boolean", "yes"),
            ("bad_date", "date", "24/10/2026"),
            ("bad_json", "json", "{IV: 1}"),
        ]
        for code, kind, value in cases:
            self._param(code, kind, [(D(2026, 1, 1), value)])
        for code, kind, _value in cases:
            with self.subTest(kind=kind), self.assertRaises(UserError):
                self._get(code, D(2026, 6, 1))

    def test_empty_value_raises(self):
        self._param("empty", "float", [(D(2026, 1, 1), False)])
        with self.assertRaises(UserError):
            self._get("empty", D(2026, 6, 1))

    def test_datetime_date(self):
        self._param("ref", "float", [(D(2026, 1, 1), "1.5")])
        self.assertEqual(self._get("ref", datetime.datetime(2026, 6, 1, 23, 59)), 1.5)
        with self.assertRaises(TypeError):
            self._get("ref", "2026-06-01")

    def test_plain_user_reads(self):
        self._param("rate", "float", [(D(2026, 1, 1), "0.08")])
        as_user = self.Param.with_user(self.plain_user)
        with self.assertRaises(AccessError):
            as_user.search([("code", "=", "test.strict.rate")])
        self.assertEqual(as_user._strict_get("test.strict.rate", D(2026, 6, 1)), 0.08)
