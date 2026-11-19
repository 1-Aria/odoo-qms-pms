# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Step 12: the pay group moves to the contract (D113).

Before the module loads, each contract without a pay group takes its employee's, whatever
the contract's state; the employee's column still holds the values entered on it.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("ALTER TABLE hr_contract ADD COLUMN IF NOT EXISTS l10n_vn_pay_group varchar")
    cr.execute(
        """
        UPDATE hr_contract c
           SET l10n_vn_pay_group = e.l10n_vn_pay_group
          FROM hr_employee e
         WHERE c.employee_id = e.id
           AND e.l10n_vn_pay_group IS NOT NULL
           AND c.l10n_vn_pay_group IS NULL
        """
    )
