# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class QmsDeterminationRule(models.Model):
    """Maps analysis to a suggested response.

    Conditions decide whether the rule applies to an item; an empty condition
    means any, and a group matches every code beneath it. Outputs say what it
    suggests. Every matching rule applies -- nothing ranks rules (D26).
    """

    _name = "qms.determination.rule"
    _description = "Determination Rule"
    _order = "sequence, id"

    # A SQL constraint, not @api.constrains: a Python constraint runs only when
    # one of its fields is in the create/write values (odoo/api.py:184-190), so
    # a rule created with just a name would never be checked.
    _sql_constraints = [
        (
            "has_condition",
            "CHECK (defect_code_id IS NOT NULL OR object_part_id IS NOT NULL "
            "OR cause_id IS NOT NULL OR origin_id IS NOT NULL)",
            "A rule needs at least one condition: a defect code, an object part, "
            "a cause or an origin.",
        ),
    ]

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(
        default=10, help="Display order only; plays no part in matching."
    )
    active = fields.Boolean(default=True)
    domain_kind = fields.Selection(
        selection=[("qm", "Quality"), ("pm", "Maintenance"), ("both", "Both")],
        string="Domain",
        required=True,
        default="both",
    )

    # Conditions. ondelete="restrict": nothing a rule depends on is deleted
    # under it. Causes have no active field, so a cause in use stays until the
    # rule stops using it; set null would break has_condition or silently
    # broaden the rule.
    defect_code_id = fields.Many2one(
        comodel_name="qms.defect.code",
        string="Defect Code",
        ondelete="restrict",
        help="Empty means any. A group matches every code beneath it.",
    )
    object_part_id = fields.Many2one(
        comodel_name="qms.object.part",
        string="Object Part",
        ondelete="restrict",
        help="Empty means any. A group matches every part beneath it.",
    )
    cause_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.cause",
        string="Cause",
        ondelete="restrict",
        help="Empty means any. A cause matches every cause beneath it.",
    )
    origin_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.origin",
        string="Origin",
        ondelete="restrict",
        help="Empty means any. An origin matches every origin beneath it.",
    )

    # Outputs.
    severity_id = fields.Many2one(
        comodel_name="mgmtsystem.nonconformity.severity",
        string="Suggested Severity",
        ondelete="restrict",
    )
    action_template_ids = fields.Many2many(
        comodel_name="mgmtsystem.action.template",
        relation="qms_determination_rule_action_template_rel",
        column1="rule_id",
        column2="template_id",
        string="Action Templates",
    )
    document_ids = fields.Many2many(
        comodel_name="document.page",
        relation="qms_determination_rule_document_page_rel",
        column1="rule_id",
        column2="page_id",
        string="Documents",
        domain=[("mgmtsystem_page_type", "in", ("procedure", "work_instruction"))],
    )

    @api.constrains("domain_kind", "defect_code_id", "object_part_id")
    def _check_domain_kind(self):
        """Reject a direct clash between the rule's domain and a condition's.

        The same clash-only rule qms.catalog.profile applies to its groups.
        Cause and origin are exempt: neither has a domain_kind.
        """
        kinds = dict(self._fields["domain_kind"]._description_selection(self.env))
        for rule in self:
            if rule.domain_kind == "both":
                continue
            for condition in (rule.defect_code_id, rule.object_part_id):
                if not condition or condition.domain_kind in ("both", rule.domain_kind):
                    continue
                raise ValidationError(
                    self.env._(
                        "'%(condition)s' (%(condition_kind)s) does not fit rule "
                        "'%(rule)s' (%(rule_kind)s).",
                        condition=condition.display_name,
                        condition_kind=kinds[condition.domain_kind],
                        rule=rule.name,
                        rule_kind=kinds[rule.domain_kind],
                    )
                )

    @api.model
    def _self_and_ancestor_ids(self, record):
        """The record's own id and its ancestors', from parent_path.

        Not a parent_of search: a search is filtered by active, so an archived
        group would drop out and its rules would stop firing for the group's
        still-active codes. All three condition models are _parent_store.
        """
        if not record:
            return []
        return [int(part) for part in record.parent_path.split("/") if part]

    @api.model
    def _match_item(self, item):
        """Every active rule whose non-empty conditions fit the item.

        An empty condition matches anything; a condition on a group or code
        matches the item's value at or beneath it. False in an ``in`` list
        becomes IS NULL (odoo/models.py:3190-3214), so an empty item value
        matches only rules that leave that condition empty.
        """
        return self.search(
            [
                (
                    "defect_code_id",
                    "in",
                    [False] + self._self_and_ancestor_ids(item.defect_code_id),
                ),
                (
                    "object_part_id",
                    "in",
                    [False] + self._self_and_ancestor_ids(item.object_part_id),
                ),
                (
                    "cause_id",
                    "in",
                    [False] + self._self_and_ancestor_ids(item.cause_id),
                ),
                (
                    "origin_id",
                    "in",
                    [False] + self._self_and_ancestor_ids(item.origin_id),
                ),
            ]
        )
