# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QmsNonconformityResponse(models.Model):
    """One suggestion on a nonconformity: a rule, and the item that fired it.

    A pointer to the rule, not a copy: every rule field shown here is a
    non-stored related field, so editing the rule changes what every line
    shows (O5, accepted for v1). A line with no item was added by hand.
    """

    _name = "qms.nonconformity.response"
    _description = "Nonconformity Response"
    # Creation order: Suggest Response writes item by item, rule by rule, and a
    # line added by hand goes to the end.
    _order = "nonconformity_id, id"

    nonconformity_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity",
        string="Nonconformity",
        required=True,
        ondelete="cascade",
        index=True,
    )
    item_id = fields.Many2one(
        comodel_name="qms.nonconformity.item",
        string="Item",
        ondelete="cascade",
        readonly=True,
    )
    rule_id = fields.Many2one(
        comodel_name="qms.determination.rule",
        string="Rule",
        required=True,
        ondelete="restrict",
    )

    # Why the line was suggested.
    rule_defect_code_id = fields.Many2one(
        related="rule_id.defect_code_id", string="Rule Defect Code"
    )
    rule_object_part_id = fields.Many2one(
        related="rule_id.object_part_id", string="Rule Object Part"
    )
    rule_cause_id = fields.Many2one(related="rule_id.cause_id", string="Rule Cause")

    # What it suggests.
    suggested_severity_id = fields.Many2one(
        related="rule_id.severity_id", string="Suggested Severity"
    )
    action_template_ids = fields.Many2many(related="rule_id.action_template_ids")
    # related_sudo=False: computed as the user, so Many2many.read applies their
    # record rules and pages they may not read drop out. The default, True,
    # would compute as superuser and hand them over.
    document_ids = fields.Many2many(related="rule_id.document_ids", related_sudo=False)
