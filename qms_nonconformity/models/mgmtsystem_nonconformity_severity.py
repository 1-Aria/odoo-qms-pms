# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MgmtsystemNonconformitySeverity(models.Model):
    _inherit = "mgmtsystem.nonconformity.severity"

    # Not OCA's `sequence`: that is an editable display order on the severity
    # form, and tidying a list must not silently re-rank analysis. No ranks are
    # seeded -- each implementation defines its own severities and their order.
    qms_severity_rank = fields.Integer(
        string="Severity Rank",
        default=0,
        help="Higher is more severe. A nonconformity takes the severity of its "
        "most severe item, so ranks must be set for that to mean anything.",
    )
