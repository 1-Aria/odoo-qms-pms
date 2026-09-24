# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# A group is a heading, never a finding, so only leaf codes are ever offered.
# Step 1 got this as a side effect of the profile term -- a group's
# parent_id.profile_ids is empty -- which is why it is stated on its own now:
# the unfiltered branch below has no profile term to lean on.
LEAF_ONLY_DOMAIN = [("parent_id", "!=", False)]


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
    # Origin is analysis, and analysis is per item: one nonconformity can carry
    # defects found different ways, and a determination rule matches an item, so
    # a condition read from the header would give the rule table two subjects.
    # The header's own origin_ids is relaxed and hidden, as cause_ids is.
    #
    # ondelete="restrict" with archiving as the way out -- unlike causes,
    # origins have an active field, so a retired origin can be archived while
    # the items that used it keep it.
    origin_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.origin",
        string="Origin",
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

    # The catalog dropdowns read these through domain="<field>", core's idiom
    # for a domain that has to be computed (account.tax.tag_ids_domain,
    # account/models/account_tax.py:4621, used at
    # account/views/account_tax_views.xml:49).
    #
    # Step 1 wrote the domain statically in the view, which made it
    # inescapable: a field domain also governs the "Search More..." dialog, so a
    # product with no profile offered nothing at all. Profiles reduce noise;
    # they never decide which codes are legitimate.
    qms_defect_code_domain = fields.Binary(
        string="Defect Code Domain",
        compute="_compute_qms_code_domains",
    )
    qms_object_part_domain = fields.Binary(
        string="Object Part Domain",
        compute="_compute_qms_code_domains",
    )

    @api.depends(
        "nonconformity_id.qms_effective_profile_ids",
        "nonconformity_id.qms_show_all_codes",
    )
    def _compute_qms_code_domains(self):
        """Leaf codes, narrowed to the product's profiles when that helps.

        Three states, and the first is the one step 1 got wrong:

        - no profile resolves, or no product: every leaf code, no filter
        - profiles resolve: the leaf codes of their groups
        - profiles resolve and the header's switch is on: every leaf code

        A code matches a profile through its group, so ``parent_id.`` is one
        hop, which is why qms_catalog holds the catalogs to two levels.
        """
        for item in self:
            nonconformity = item.nonconformity_id
            profiles = nonconformity.qms_effective_profile_ids
            if nonconformity.qms_show_all_codes or not profiles:
                item.qms_defect_code_domain = LEAF_ONLY_DOMAIN
                item.qms_object_part_domain = LEAF_ONLY_DOMAIN
                continue
            profile_term = [("parent_id.profile_ids", "in", profiles.ids)]
            item.qms_defect_code_domain = LEAF_ONLY_DOMAIN + profile_term
            item.qms_object_part_domain = LEAF_ONLY_DOMAIN + profile_term

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
