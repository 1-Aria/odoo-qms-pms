# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .qc_test_question import CHECKLIST_DEFECT_CODE_DOMAIN


class QcTestQuestionValue(models.Model):
    # OCA's model carries only test_line, name and ok ("Correct answer?") --
    # quality_control_oca/models/qc_test.py:103-112.
    _inherit = "qc.test.question.value"

    # ondelete="restrict", as elsewhere: a defect code a checklist uses is
    # archived, not deleted.
    qms_defect_code_id = fields.Many2one(
        comodel_name="qms.defect.code",
        string="Defect Code",
        ondelete="restrict",
        domain=CHECKLIST_DEFECT_CODE_DOMAIN,
        help="The defect this answer records when it is given.",
    )
