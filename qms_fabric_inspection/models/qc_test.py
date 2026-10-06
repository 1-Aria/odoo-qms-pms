# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QcTest(models.Model):
    _inherit = "qc.test"

    # Copied onto each inspection when its test is set (qc_inspection.py), so
    # editing these changes the inspections made afterwards, never past ones.
    qms_roll_inspection = fields.Boolean(
        string="Roll Inspection",
        help="Inspections from this test list the rolls of the receipt line, "
        "each scored by the 4-point system.",
    )
    qms_points_limit = fields.Float(
        string="Points Limit (per 100 m²)",
        help="The highest score a scored roll may have and pass; 0 means the "
        "score is not judged. If the buyer's standard gives the limit per "
        "100 yd², multiply it by 1.196.",
    )
    qms_points_cap = fields.Integer(
        string="Points Cap per Metre",
        default=4,
        help="The most points one metre of roll can score, 4 under the 4-point "
        "system; 0 means no cap.",
    )
