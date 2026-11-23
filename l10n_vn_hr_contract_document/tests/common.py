# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import Command

from odoo.addons.l10n_vn_payroll.tests.common import PayrollCase

D = datetime.date


class ContractDocumentCase(PayrollCase):
    """Fixtures for the contract document tests; holds no test methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.director = cls.env["res.partner"].create({"name": "Test Director"})
        cls.company.write(
            {
                "vat": "0000000001",
                "street": "1 Test Street",
                "city": "Test City",
                "state_id": cls.env["res.country.state"]
                .search([("country_id", "=", cls.env.ref("base.vn").id)], limit=1)
                .id,
                "l10n_vn_legal_rep_id": cls.director.id,
                "l10n_vn_legal_rep_title": "Giám đốc",
                "l10n_vn_contract_code": "TC",
            }
        )
        # the statutory limits approval reads (vn.probation.*)
        cls.company._l10n_vn_payroll_ensure_parameters()
        # the fixture's running contract ends before the document contracts start
        cls.contract.write({"date_end": D(2026, 10, 31)})
        cls.workplace = cls.env["res.partner"].create(
            {"name": "Test Factory", "street": "2 Factory Road", "city": "Test City"}
        )
        cls.employee.write(
            {
                "birthday": D(1995, 3, 4),
                "gender": "female",
                "l10n_vn_personal_id": "001195012345",
                "l10n_vn_id_issue_date": D(2021, 5, 6),
                "l10n_vn_id_issue_place": "Cục Cảnh sát QLHC về TTXH",
                "l10n_vn_permanent_address": "Ấp 1, xã Test, An Giang",
                "address_id": cls.workplace.id,
            }
        )
        cls.employee_values = {
            "birthday": D(1995, 3, 4),
            "gender": "female",
            "l10n_vn_personal_id": "001195012345",
            "l10n_vn_id_issue_date": D(2021, 5, 6),
            "l10n_vn_id_issue_place": "Cục Cảnh sát QLHC về TTXH",
            "l10n_vn_permanent_address": "Ấp 1, xã Test, An Giang",
            "address_id": cls.workplace.id,
        }
        cls.job = cls.env["hr.job"].create({"name": "Test Sewer", "company_id": cls.company.id})
        Type = cls.env["hr.contract.type"]
        cls.types = {
            kind: Type.create(
                {
                    "name": f"Test {kind} contract",
                    "code": f"TEST_{kind.upper()}",
                    "l10n_vn_document_kind": kind,
                }
            )
            for kind in ("labour", "probation", "training", "none")
        }
        cls._parameter("vn.policy.probation_rate", [(D(2026, 1, 1), "0.85")])
        cls.base = cls._component(
            "BASE", in_si_base=True, probation_applies=True, sequence=1
        )
        cls.prod = cls._component(
            "PROD",
            legal_nature="variable_salary",
            variable=True,
            attainment_source="supervisor",
            sequence=2,
        )
        cls.train = cls._component("TRAIN", sequence=3)
        cls.phone = cls._component("PHONE", legal_nature="welfare", sequence=4)

    @classmethod
    def _new_employee(cls, name, **values):
        """Another employee with complete contract data, for contracts that must not overlap."""
        return cls.env["hr.employee"].create(
            dict(
                cls.employee_values,
                name=name,
                company_id=cls.company.id,
                department_id=cls.department.id,
                **values,
            )
        )

    @classmethod
    def _doc_contract(cls, kind, **values):
        """A draft contract of ``kind`` from 2026-11-02 with BASE 4,500,000 and PROD 500,000."""
        vals = {
            "name": f"Test {kind} document contract",
            "employee_id": cls.employee.id,
            "company_id": cls.company.id,
            "contract_type_id": cls.types[kind].id,
            "job_id": cls.job.id,
            "date_start": D(2026, 11, 2),
            "wage": 1,
            "resource_calendar_id": cls.calendar.id,
            "state": "draft",
            "l10n_vn_line_ids": [
                Command.create(
                    {
                        "component_id": cls.base.id,
                        "amount": 4500000,
                        "date_from": D(2026, 11, 2),
                    }
                ),
                Command.create(
                    {
                        "component_id": cls.prod.id,
                        "amount": 500000,
                        "date_from": D(2026, 11, 2),
                    }
                ),
            ],
        }
        vals.update(values)
        return cls.env["hr.contract"].create(vals)
