# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Step 12: the employee's pay group is now a copy of the current contract's (D113).

Employees whose stored value differs from their current contract's (those without a
current contract) are recomputed; the others already hold the same value.
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Employee = env["hr.employee"].with_context(active_test=False)
    employees = Employee.search([]).filtered(
        lambda e: e.l10n_vn_pay_group != e.contract_id.l10n_vn_pay_group
    )
    if employees:
        env.add_to_compute(Employee._fields["l10n_vn_pay_group"], employees)
        env.flush_all()
