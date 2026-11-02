# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import Command
from odoo.tests import TransactionCase

D = datetime.date


class PayrollCase(TransactionCase):
    """Fixtures for l10n_vn_payroll tests; holds no test methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Payroll Test Company VN",
                "country_id": cls.env.ref("base.vn").id,
                "currency_id": cls.env.ref("base.VND").id,
            }
        )
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                allowed_company_ids=[cls.company.id, *cls.env.companies.ids],
            )
        )
        cls.calendar = cls.company.resource_calendar_id
        cls.department = cls.env["hr.department"].create(
            {"name": "Payroll Test Department", "company_id": cls.company.id}
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Payroll Test Employee",
                "company_id": cls.company.id,
                "department_id": cls.department.id,
            }
        )
        cls.contract = cls.env["hr.contract"].create(
            {
                "name": "Payroll Test Contract",
                "employee_id": cls.employee.id,
                "company_id": cls.company.id,
                "date_start": D(2026, 1, 1),
                "wage": 1,
                "resource_calendar_id": cls.calendar.id,
                "state": "open",
            }
        )

    @classmethod
    def _component(cls, code, **values):
        vals = {
            "code": f"TEST_{code}",
            "name": code,
            "company_id": cls.company.id,
            "kind": "earning",
            "legal_nature": "job_salary",
            "pit_treatment": "taxable",
            "proration": "paid_days",
            "amount_source": "line",
        }
        vals.update(values)
        return cls.env["l10n_vn.payroll.component"].create(vals)

    @classmethod
    def _scale(cls, code, kind, versions):
        return cls.env["l10n_vn.payroll.scale"].create(
            {
                "code": f"TEST_{code}",
                "name": code,
                "kind": kind,
                "company_id": cls.company.id,
                "version_ids": [
                    Command.create(
                        {
                            "date_from": date_from,
                            "cell_ids": [
                                Command.create({"key": key, "amount": amount})
                                for key, amount in cells.items()
                            ],
                        }
                    )
                    for date_from, cells in versions.items()
                ],
            }
        )

    @classmethod
    def _line(cls, component, contract=None, **values):
        vals = {
            "contract_id": (contract or cls.contract).id,
            "component_id": component.id,
            "date_from": D(2026, 1, 1),
        }
        vals.update(values)
        return cls.env["l10n_vn.payroll.contract.line"].create(vals)

    @classmethod
    def _parameter(cls, code, versions):
        return cls.env["base.time.parameter"].create(
            {
                "name": code,
                "code": code,
                "type": "float",
                "company_id": cls.company.id,
                "version_ids": [
                    Command.create({"date_from": date_from, "value": value})
                    for date_from, value in versions
                ],
            }
        )

    def _as(self, user):
        """An environment for ``user``, working in the test company only.

        The fixtures' environment also allows the superuser's companies, which
        test users do not belong to; ``with_user`` alone would keep them.
        """
        return self.env(user=user, context=dict(self.env.context, allowed_company_ids=[self.company.id]))

    @classmethod
    def _user(cls, login, groups):
        group_ids = [cls.env.ref("base.group_user").id] + [cls.env.ref(g).id for g in groups]
        return cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "company_id": cls.company.id,
                "company_ids": [Command.set([cls.company.id])],
                "groups_id": [Command.set(group_ids)],
            }
        )
