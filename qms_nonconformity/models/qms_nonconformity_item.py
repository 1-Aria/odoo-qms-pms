# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QmsNonconformityItem(models.Model):
    """One line of analysis: what is wrong, where, and why.

    A nonconformity carries many items. ondelete="restrict" on the catalog
    and cause links keeps anything used in analysis from being deleted.
    Defect codes and object parts are archived instead; OCA gives causes no
    active field, so a cause in use stays until no item refers to it.
    """

    _name = "qms.nonconformity.item"
    _description = "Nonconformity Item"
    _order = "nonconformity_id, sequence, id"

    nonconformity_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity",
        string="Nonconformity",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10, help="Defines the order to present items")
    defect_code_id = fields.Many2one(
        comodel_name="qms.defect.code",
        string="Defect Code",
        required=True,
        ondelete="restrict",
    )
    object_part_id = fields.Many2one(
        comodel_name="qms.object.part",
        string="Object Part",
        ondelete="restrict",
    )
    cause_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.cause",
        string="Cause",
        ondelete="restrict",
    )
    severity_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.severity",
        string="Severity",
        ondelete="restrict",
        compute="_compute_severity_id",
        store=True,
        readonly=False,
    )
    qty_affected = fields.Float(string="Quantity Affected")
    note = fields.Char()

    @api.depends("defect_code_id.name", "object_part_id.name")
    def _compute_display_name(self):
        """Show as "Torn · Sleeves": what is wrong, then where, when known.

        Leaf names rather than the codes' full "Group / Code" display names,
        which would crowd a Many2one column.
        """
        for item in self:
            parts = [item.defect_code_id.name, item.object_part_id.name]
            item.display_name = " · ".join(part for part in parts if part)

    @api.depends("defect_code_id")
    def _compute_severity_id(self):
        """Take the defect code's default severity.

        A compute rather than the onchange plan 7.4 names, so items created in
        code -- the inspection prefill -- get a severity too. Editable: a
        manual value stands until the defect code changes, when the item is
        about a different defect and re-deriving is the right answer.
        """
        for item in self:
            item.severity_id = item.defect_code_id.default_severity_id
