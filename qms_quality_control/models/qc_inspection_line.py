# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QcInspectionLine(models.Model):
    _inherit = "qc.inspection.line"

    # The one place the resolution rule lives: Populate Defect reads this field
    # rather than repeating the rule, so the inspection and the items it
    # generates can never disagree.
    #
    # A stored snapshot of the answer (step 7). The QM report groups defects by
    # code, and a checklist edit must not rewrite its history, so the field
    # depends on the line's own answer only and reads the checklist's code
    # without depending on it: the code is taken when the line is answered.
    qms_defect_code_id = fields.Many2one(
        comodel_name="qms.defect.code",
        string="Defect Code",
        compute="_compute_qms_defect_code_id",
        store=True,
        index=True,
        help="The defect this line records. Empty while the line passes.",
    )
    # Frozen the same way, from the code.
    qms_severity_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.severity",
        string="Severity",
        compute="_compute_qms_severity_id",
        store=True,
        help="The defect code's default severity when the line was answered.",
    )

    # How many units the defect affected, which the inspection had no way to
    # say: the header's qty is the quantity inspected in the lot, one number for
    # the whole inspection. Populate Defect copies this to the item's
    # qty_affected.
    #
    # No unit of measure of its own -- uom_id above describes the measurement on
    # a quantitative question, not a count of affected units, so this is in the
    # same unit as the header's qty and nothing converts. No constraint against
    # that qty either: one garment with a torn sleeve and a broken stitch is two
    # lines of quantity 1 against a header quantity of 1, so defects overlap on
    # units and the sum is not bounded by the size of the inspection. A plain
    # Float, matching qty_affected on the item so the copy is lossless.
    qms_qty_failed = fields.Float(
        string="Quantity Failed",
        help="How many units this defect affected. Carried to the "
        "nonconformity item when defects are populated.",
    )

    # Not test_line: a question is a plain Many2one with ondelete "set null"
    # (quality_control_oca/models/qc_inspection.py:308), so depending on it
    # would wipe the codes of every line that asked a question someone deleted.
    # test_line is set at creation and never changes otherwise, and a stored
    # compute is computed at creation, so nothing is lost by leaving it out.
    @api.depends("success", "question_type", "qualitative_value")
    def _compute_qms_defect_code_id(self):
        """The defect a failed line records.

        Gated on ``success``, so the field means "the defect this line records"
        rather than "the defect it would record if it failed": blank on every
        passing row. An answer misconfigured as correct while carrying a code
        therefore shows nothing here, which is acceptable -- the answers list
        puts ``ok`` and the code side by side, where the mistake was made.

        A qualitative line takes the code from the answer that was given; a
        quantitative one has no answer record, so it takes the code from the
        question. ``test_line`` may be empty if the question was deleted, and
        the line then records nothing rather than a guess.
        """
        for line in self:
            if line.success:
                line.qms_defect_code_id = False
            elif line.question_type == "qualitative":
                line.qms_defect_code_id = line.qualitative_value.qms_defect_code_id
            else:
                line.qms_defect_code_id = line.test_line.qms_defect_code_id

    @api.depends("qms_defect_code_id")
    def _compute_qms_severity_id(self):
        for line in self:
            line.qms_severity_id = line.qms_defect_code_id.default_severity_id
