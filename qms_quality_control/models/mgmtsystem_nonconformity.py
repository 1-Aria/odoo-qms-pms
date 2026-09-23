# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# The three states qc.inspection reaches once it has been confirmed
# (quality_control_oca/models/qc_inspection.py:70-81, 145-172): action_confirm
# sends a failing inspection to "waiting" for supervisor approval and a passing
# one straight to "success", and action_approve resolves "waiting" into
# "success" or "failed". Excluded: plan, draft and ready, where nothing has been
# confirmed, and canceled, a voided inspection.
INSPECTION_DONE_STATES = ("waiting", "success", "failed")


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    # The whole visibility rule for the Populate Defect button, in Python where
    # a test can assert it state by state, leaving the view one term.
    #
    # The view gives this field and the button
    # quality_control_oca.group_quality_control_user, and that gate is
    # load-bearing: qc.inspection grants read to that group alone
    # (quality_control_oca/security/ir.model.access.csv:2-3), while the OCA
    # bridge's qc_inspection_id displays for anyone because web_read takes a
    # Many2one's label as superuser (web/models/models.py:122-123) and skips the
    # comodel read entirely (:79-84). A plain compute runs as the user
    # (compute_sudo defaults to store, so False here -- fields.py:443, 309), so
    # reading the inspection's state here would be the first thing to raise
    # AccessError for a management-system user outside quality control. A field
    # the client never requests is never computed.
    qms_can_populate_defect = fields.Boolean(
        string="Can Populate Defect",
        compute="_compute_qms_can_populate_defect",
        help="Whether the analysis can be filled from the source inspection.",
    )

    @api.depends("state", "item_ids", "qc_inspection_id.state")
    def _compute_qms_can_populate_defect(self):
        """In Analysis, nothing analysed yet, and a confirmed inspection.

        The empty-analysis term is what makes the button add-only: it
        disappears once an item exists, so nothing a person entered can be
        deleted and no Python guard is needed.
        """
        for nonconformity in self:
            nonconformity.qms_can_populate_defect = bool(
                nonconformity.state == "analysis"
                and not nonconformity.item_ids
                and nonconformity.qc_inspection_id.state in INSPECTION_DONE_STATES
            )

    def action_populate_defect(self):
        """Fill the analysis from the source inspection's recorded defects.

        One item per inspection line that resolves a defect code, in line
        order. Creates only -- never deletes, because the button is gone once
        the nonconformity holds an item.

        The item's severity is not set here: qms_nonconformity derives it from
        the defect code in a stored compute, for items created in code as well.
        The failed quantity is carried across. Object part and cause are left
        for the analyst, and the determination engine matches a partial item
        natively.

        Line order needs no sorting: qc.inspection.line declares no _order, so
        it is id, and the lines are created by walking test.test_lines
        (quality_control_oca/models/qc_inspection.py:217-224), which is ordered
        sequence, id.
        """
        values = []
        for nonconformity in self:
            lines = nonconformity.qc_inspection_id.inspection_lines.filtered(
                "qms_defect_code_id"
            )
            for index, line in enumerate(lines, start=1):
                values.append(
                    {
                        "nonconformity_id": nonconformity.id,
                        "sequence": index * 10,
                        "defect_code_id": line.qms_defect_code_id.id,
                        # The quantity the inspector recorded against this
                        # defect. Unfilled copies 0.0, which is the item's own
                        # default, so there is no special case.
                        "qty_affected": line.qms_qty_failed,
                        # The question, so an item does not read "Torn" with no
                        # trace of which check raised it.
                        "note": line.name,
                    }
                )
        if self.env["qms.nonconformity.item"].create(values):
            return True
        # The button is visible exactly when the analysis is empty, so a click
        # that creates nothing would otherwise look broken. No params.next:
        # nothing changed, so there is nothing to reload.
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "warning",
                "title": self.env._("No defects to populate"),
                "message": self.env._(
                    "No line on this inspection records a defect code. Codes "
                    "are set on the test's questions and answers."
                ),
            },
        }
