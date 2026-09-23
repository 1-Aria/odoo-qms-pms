# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# Both checklist fields offer the same codes. A group is a heading, never a
# finding, so only leaf codes qualify -- the item's own dropdown gets that for
# free from the 7.6 domain, but Populate Defect creates items in code and
# bypasses it, so the restriction sits where the code is chosen. domain_kind
# keeps a maintenance-only code off a quality checklist (D14); a "both" code
# qualifies. A domain filters the dropdown only: it is not enforced against an
# import or a write from code, which is deliberate -- a checklist is written by
# hand in a form.
CHECKLIST_DEFECT_CODE_DOMAIN = [
    ("parent_id", "!=", False),
    ("domain_kind", "in", ("qm", "both")),
]


class QcTestQuestion(models.Model):
    _inherit = "qc.test.question"

    # Read only for a quantitative question, which has no answer record to
    # carry a code although qc.inspection.line.success still reports it failed
    # (quality_control_oca/models/qc_inspection.py:271-285). A qualitative
    # question carries its codes on its answers, where they are more precise:
    # two wrong answers can be two different defects.
    qms_defect_code_id = fields.Many2one(
        comodel_name="qms.defect.code",
        string="Defect Code",
        ondelete="restrict",
        domain=CHECKLIST_DEFECT_CODE_DOMAIN,
        help="The defect an out-of-tolerance measurement records. Quantitative "
        "questions only -- a qualitative question carries its defect codes on "
        "its answers.",
    )
