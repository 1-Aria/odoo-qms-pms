# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""TC-P01: the journal entry of a run of G01, G10 and G13 on the garment mapping (step 4).

The expected lines are never typed: they come from posting_cases.json, which
payroll_reference_calc.py writes from the same cases.
"""

import json
from collections import defaultdict

from odoo.tests import tagged
from odoo.tools.misc import file_path

from odoo.addons.l10n_vn_payroll.tests.group_g import STAFF, WORKER, GroupGCases
from odoo.addons.l10n_vn_payroll.tests.payslip_common import PayslipCase

from .common import GarmentMixin, prepare_chart

POSTING_FILE = "l10n_vn_payroll_garment/tests/data/posting_cases.json"


@tagged("post_install", "-at_install")
class TestGarmentPosting(GarmentMixin, GroupGCases, PayslipCase):
    # only the test below: group G itself runs in test_acceptance

    @classmethod
    def _l10n_vn_configure(cls):
        # the chart first: loading it deletes the company's journals and accounts
        cls.accounts = prepare_chart(cls.env, cls.company)
        super()._l10n_vn_configure()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.l10n_vn_payroll_post = True
        groups = {
            group.code: group
            for group in cls.env["l10n_vn.payroll.cost.group"].search(
                [("company_id", "=", cls.company.id)]
            )
        }
        cls.factory = groups["FACTORY"]
        Department = cls.env["hr.department"]
        production = Department.create(
            {"name": "Test Production", "company_id": cls.company.id,
             "l10n_vn_cost_group_id": groups["DIRECT"].id}
        )
        cls.sewing = Department.create(
            {"name": "Test Sewing", "company_id": cls.company.id, "parent_id": production.id}
        )
        cls.administration = Department.create(
            {"name": "Test Administration", "company_id": cls.company.id,
             "l10n_vn_cost_group_id": groups["ADMIN"].id}
        )

    def test_p01(self):
        # each payslip made as group G makes it, in its department
        worker, _c = self._worker("Entry", department_id=self.sewing.id)
        g01 = self._run("G01", worker, WORKER, **self._supervised(
            ot_hours_json={"WD": 20}, lines=[(self.eff, {"amount": 300000})]))
        leader, _c = self._staff(
            {"scale_key": "G2-2"},
            department_id=self.sewing.id,
            l10n_vn_cost_group_id=self.factory.id,
        )
        self._dependents(leader, 1)
        g10 = self._run("G10", leader, STAFF, **self._managed(ot_hours_json={"WD": 30}))
        manager, _c = self._staff({"amount": 45000000}, department_id=self.administration.id)
        self._dependents(manager, 2)
        g13 = self._run("G13", manager, ["BASE", "PERF"], **self._managed())

        run = self.env["hr.payslip.run"].create({"l10n_vn_period_id": self.period.id})
        (g01 | g10 | g13).write({"payslip_run_id": run.id})
        run.state = "approved"
        run._l10n_vn_post()
        move = run.l10n_vn_move_id
        self.assertEqual(move.state, "posted")

        expected = json.load(open(file_path(POSTING_FILE), encoding="utf-8"))["P01"]
        case_of = {worker.work_contact_id: "G01", leader.work_contact_id: "G10",
                   manager.work_contact_id: "G13"}
        want, got = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
        for account, case, debit, credit in expected["lines"]:
            want[(account, case)][0] += debit
            want[(account, case)][1] += credit
        for line in move.line_ids:
            # an account's code is per company: read it in the test company
            key = (line.account_id.with_company(self.company).code, case_of.get(line.partner_id))
            got[key][0] += line.debit
            got[key][1] += line.credit
        self.assertEqual(dict(got), dict(want))

        employee_of = {"G01": worker, "G10": leader, "G13": manager}
        for case, net in expected["residual"].items():
            lines = self.env["account.move.line"].search(
                [("account_id", "=", self.accounts["3341"].id),
                 ("partner_id", "=", employee_of[case].work_contact_id.id)]
            )
            self.assertEqual(sum(lines.mapped("amount_residual")), -net, case)
