# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger

DAY = datetime.timedelta(days=1)


@tagged("post_install", "-at_install")
class TestConversionCost(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A company of its own keeps the tests apart from rates on the instance.
        cls.company = cls.env["res.company"].create(
            {
                "name": "Conversion Cost Test Co",
                "currency_id": cls.env.ref("base.VND").id,
            }
        )
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                allowed_company_ids=[cls.company.id, *cls.env.companies.ids],
            )
        )
        cls.Rate = cls.env["mrp.conversion.cost.rate"]
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.today = fields.Date.context_today(cls.Rate)
        cls.rate_1 = cls._rate(cls.today, 1500.0)
        cls.categ = cls.env["product.category"].create(
            {
                "name": "Conversion Cost Test",
                "property_cost_method": "average",
                "property_valuation": "manual_periodic",
            }
        )
        product_vals = {"is_storable": True, "categ_id": cls.categ.id}
        cls.component = cls.env["product.product"].create(
            dict(product_vals, name="Conversion Cost Component", standard_price=10000.0)
        )
        cls.garment = cls.env["product.product"].create(
            dict(product_vals, name="Conversion Cost Garment")
        )
        cls.garment_b = cls.env["product.product"].create(
            dict(product_vals, name="Conversion Cost Garment B")
        )
        cls.bom = cls._bom(cls.garment, conversion_minutes=12.5)
        cls.bom_b = cls._bom(cls.garment_b)
        cls.mrp_user = cls._user("test.conversion.mrp.user", "mrp.group_mrp_user")
        cls.mrp_manager = cls._user("test.conversion.mrp.manager", "mrp.group_mrp_manager")
        cls.account_manager = cls._user(
            "test.conversion.account.manager", "account.group_account_manager"
        )

    @classmethod
    def _rate(cls, date_from, rate, approve=True):
        record = cls.env["mrp.conversion.cost.rate"].create(
            {"company_id": cls.company.id, "date_from": date_from, "rate": rate}
        )
        if approve:
            record.action_approve()
        return record

    @classmethod
    def _bom(cls, product, **vals):
        return cls.env["mrp.bom"].create(
            dict(
                {
                    "product_tmpl_id": product.product_tmpl_id.id,
                    "product_id": product.id,
                    "product_qty": 1.0,
                    "type": "normal",
                    # mrp_bom_version creates BoMs archived outside test runs
                    "active": True,
                    "bom_line_ids": [
                        Command.create({"product_id": cls.component.id, "product_qty": 2.0})
                    ],
                },
                **vals,
            )
        )

    @classmethod
    def _user(cls, login, group):
        return cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "groups_id": [Command.set(cls.env.ref(group).ids)],
            }
        )

    def _as(self, user):
        return self.env(
            user=user,
            context=dict(self.env.context, allowed_company_ids=[self.company.id]),
        )

    def _mo(self, product, qty=1, **vals):
        stock = self.warehouse.lot_stock_id
        return self.env["mrp.production"].create(
            dict(
                {
                    "product_id": product.id,
                    "product_qty": qty,
                    "location_src_id": stock.id,
                    "location_dest_id": stock.id,
                },
                **vals,
            )
        )

    def _done(self, mo, **ctx):
        mo.action_confirm()
        mo_form = Form(mo)
        mo_form.qty_producing = mo.product_qty
        mo = mo_form.save()
        mo.move_raw_ids.picked = True
        mo.with_context(**ctx).button_mark_done()
        return mo

    def _finished_value(self, mo):
        finished = mo.move_finished_ids.filtered(lambda m: m.product_id == mo.product_id)
        return sum(finished.stock_valuation_layer_ids.mapped("value"))

    def _unapprove_rate_1(self):
        self.env.cr.execute(
            "UPDATE mrp_conversion_cost_rate SET state = 'draft' WHERE id = %s",
            [self.rate_1.id],
        )
        self.rate_1.invalidate_recordset(["state"])

    def test_rate_on_latest_before_date(self):
        rate_2 = self._rate(self.today + 10 * DAY, 2000.0)

        def rate_on(date):
            return self.Rate._rate_on(self.company, date)

        self.assertEqual(rate_on(self.today), self.rate_1)
        self.assertEqual(rate_on(self.today + 9 * DAY), self.rate_1)
        self.assertEqual(rate_on(self.today + 10 * DAY), rate_2)
        self.assertFalse(rate_on(self.today - DAY))

    def test_approved_rate_locked(self):
        with self.assertRaises(UserError):
            self.rate_1.rate = 2000.0
        with self.assertRaises(UserError):
            self.rate_1.date_from = self.today + 5 * DAY
        with self.assertRaises(UserError):
            self.rate_1.unlink()
        # positive control: the basis stays editable
        self.rate_1.note = "Q4 budget"
        self.assertEqual(self.rate_1.note, "Q4 budget")
        draft = self._rate(self.today + 30 * DAY, 1000.0, approve=False)
        draft.rate = 1100.0
        self.assertEqual(draft.rate, 1100.0)
        draft.unlink()
        self.assertFalse(draft.exists())

    def test_no_backdated_approval(self):
        rate = self._rate(self.today - DAY, 1000.0, approve=False)
        with self.assertRaises(UserError):
            rate.action_approve()
        self.assertEqual(rate.state, "draft")

    def test_rate_constraints(self):
        with (
            self.assertRaises(IntegrityError),
            mute_logger("odoo.sql_db"),
            self.env.cr.savepoint(),
        ):
            self._rate(self.today + 40 * DAY, 0.0, approve=False)
            self.env.flush_all()
        with (
            self.assertRaises(IntegrityError),
            mute_logger("odoo.sql_db"),
            self.env.cr.savepoint(),
        ):
            self._rate(self.today, 1600.0, approve=False)
            self.env.flush_all()

    def test_estimate_before_done(self):
        mo = self._mo(self.garment)
        self.assertAlmostEqual(mo.conversion_cost_estimate, 18750.0)
        self.assertEqual(mo.extra_cost, 0.0)
        self.assertFalse(mo.conversion_rate_id)

    def test_valuation_at_done(self):
        mo = self._done(self._mo(self.garment, qty=2))
        self.assertEqual(mo.state, "done")
        self.assertAlmostEqual(mo.extra_cost, 18750.0)
        self.assertEqual(mo.conversion_rate_id, self.rate_1)
        self.assertAlmostEqual(mo.conversion_minutes, 12.5)
        # 2 garments × (2 components × 10,000 + 12.5 min × 1,500)
        self.assertAlmostEqual(self._finished_value(mo), 77500.0)

    def test_valuation_date_decides_rate(self):
        rate_2 = self._rate(self.today + 10 * DAY, 2000.0)
        mo = self._done(
            self._mo(self.garment, qty=2), force_period_date=self.today + 10 * DAY
        )
        self.assertEqual(mo.state, "done")
        self.assertAlmostEqual(mo.extra_cost, 25000.0)
        self.assertEqual(mo.conversion_rate_id, rate_2)
        self.assertAlmostEqual(self._finished_value(mo), 90000.0)

    def test_snapshot_survives_bom_change(self):
        mo = self._done(self._mo(self.garment))
        self.bom.conversion_minutes = 20.0
        self.assertAlmostEqual(mo.conversion_minutes, 12.5)
        self.assertAlmostEqual(mo.extra_cost, 18750.0)

    def test_no_rate_blocks_done(self):
        self._unapprove_rate_1()
        mo = self._mo(self.garment)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self._done(mo)
        self.env.invalidate_all()
        self.assertNotEqual(mo.state, "done")

    def test_uncovered_mo_untouched(self):
        self._unapprove_rate_1()
        mo = self._done(self._mo(self.garment_b, extra_cost=5000.0))
        self.assertEqual(mo.state, "done")
        self.assertAlmostEqual(mo.extra_cost, 5000.0)
        self.assertFalse(mo.conversion_rate_id)
        # 1 garment × (2 components × 10,000 + 5,000)
        self.assertAlmostEqual(self._finished_value(mo), 25000.0)

    def test_subcontract_bom_not_covered(self):
        types = [value for value, _label in self.env["mrp.bom"]._fields["type"].selection]
        if "subcontract" not in types:
            self.skipTest("mrp_subcontracting is not installed")
        partner = self.env["res.partner"].create({"name": "Conversion Cost Subcontractor"})
        bom = self._bom(
            self.garment_b,
            type="subcontract",
            subcontractor_ids=[Command.set(partner.ids)],
            conversion_minutes=12.5,
        )
        mo = self._mo(self.garment_b, bom_id=bom.id)
        self.assertEqual(mo.bom_id, bom)
        self.assertFalse(mo._conversion_cost_bom())
        self.assertEqual(mo.conversion_cost_estimate, 0.0)

    def test_negative_minutes_refused(self):
        with (
            self.assertRaises(IntegrityError),
            mute_logger("odoo.sql_db"),
            self.env.cr.savepoint(),
        ):
            self.bom.conversion_minutes = -1.0
            self.bom.flush_recordset()
        self.bom.invalidate_recordset()

    def test_access(self):
        user_rates = self._as(self.mrp_user)["mrp.conversion.cost.rate"]
        # positive control: manufacturing users read rates
        self.assertAlmostEqual(user_rates.browse(self.rate_1.id).rate, 1500.0)
        with self.assertRaises(AccessError):
            user_rates.create(
                {
                    "company_id": self.company.id,
                    "date_from": self.today + 20 * DAY,
                    "rate": 1.0,
                }
            )
        draft = self._rate(self.today + 21 * DAY, 1000.0, approve=False)
        with self.assertRaises(AccessError):
            draft.with_env(self._as(self.mrp_manager)).action_approve()
        # positive control: accounting administrators create and approve
        rate = self._as(self.account_manager)["mrp.conversion.cost.rate"].create(
            {
                "company_id": self.company.id,
                "date_from": self.today + 20 * DAY,
                "rate": 1800.0,
            }
        )
        rate.action_approve()
        self.assertEqual(rate.state, "approved")
        self.assertEqual(rate.approved_by_id, self.account_manager)

    def test_manager_form(self):
        mo_form = Form(self._as(self.mrp_manager)["mrp.production"])
        mo_form.product_id = self.garment
        self.assertAlmostEqual(mo_form.conversion_cost_estimate, 18750.0)
        with self.assertRaises(AssertionError):
            mo_form.extra_cost = 1.0
