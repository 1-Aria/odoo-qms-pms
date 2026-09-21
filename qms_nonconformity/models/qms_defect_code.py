# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QmsDefectCode(models.Model):
    # Here rather than in qms_catalog, which knows nothing of the severity
    # model (plan 7.1).
    _inherit = "qms.defect.code"

    default_severity_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.severity",
        string="Default Severity",
        ondelete="restrict",
        help="Severity an analysis item takes when this defect is recorded. "
        "It can be changed on the item.",
    )
