# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Step 11: a separate probation contract is taxed progressively unless it runs under 3 months.

The participant types are noupdate data, so an upgrade keeps the stored method (D104).
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    probation = env.ref("l10n_vn_payroll.participant_probation", raise_if_not_found=False)
    if probation:
        probation.pit_method = "progressive"
