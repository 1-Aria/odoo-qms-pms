# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    item_ids = fields.One2many(
        comodel_name="qms.nonconformity.item",
        inverse_name="nonconformity_id",
        string="Analysis Items",
    )
    # Read by the item lines' domain. It lives on the header because a domain
    # can only reach parent.<field>, which the client evaluates to an id list.
    qms_effective_profile_ids = fields.Many2many(
        comodel_name="qms.catalog.profile",
        related="product_id.qms_effective_profile_ids",
        string="Effective Catalog Profiles",
        readonly=True,
    )
    # A nonconformity raised from an inspection or a maintenance request often
    # has no partner at all. Every other attribute is inherited.
    partner_id = fields.Many2one(required=False)
    # Origin moved to the analysis item, so the header's list is relaxed and
    # hidden rather than removed: it stays available to other views, to the API
    # and to any OCA code that reads it. The same treatment cause_ids has.
    origin_ids = fields.Many2many(required=False)
    responsible_user_id = fields.Many2one(
        default=lambda self: self._default_responsible_user_id()
    )
    severity_id = fields.Many2one(
        compute="_compute_severity_id",
        store=True,
        readonly=False,
        tracking=True,
    )
    # The escape hatch for the catalog filtering: the profiles reduce noise on
    # the item dropdowns, and this widens them to the whole catalog when the
    # analyst judges a code outside the assigned profiles to be the right one.
    # On the header rather than the line, because it governs every line and a
    # per-line switch would be a column of checkboxes.
    qms_show_all_codes = fields.Boolean(
        string="Show all catalog codes",
        default=False,
        help="Offer every defect code and object part, instead of only those in "
        "the catalog profiles assigned to this product.",
    )
    disposition_id = fields.Many2one(
        comodel_name="qms.disposition",
        string="Disposition",
        ondelete="restrict",
        tracking=True,
        help="What was decided about the affected material or equipment.",
    )

    def _default_responsible_user_id(self):
        return self.env.user

    def _qms_gates(self):
        """The company whose gate switches apply to this nonconformity."""
        self.ensure_one()
        return self.company_id or self.env.company

    # Both constraints below keep @api.constrains. The decorator is what makes a
    # method a constraint at all: _constraint_methods collects it from the
    # resolved class attribute (odoo/models.py:902-916), so an override without
    # it would not relax the rule -- it would delete it.
    #
    # The messages are ours rather than OCA's: they name the switch, so someone
    # who meets the gate knows it can be turned off.
    @api.constrains("stage_id")
    def _check_open_with_action_comments(self):
        """OCA's gate at In Progress, behind a company switch.

        Source: mgmtsystem_nonconformity/models/mgmtsystem_nonconformity.py,
        _check_open_with_action_comments -- diff against it on an OCA upgrade.
        """
        for nonconformity in self:
            if nonconformity.state != "open":
                continue
            if not nonconformity._qms_gates().qms_require_action_plan_comments:
                continue
            if not nonconformity.action_comments:
                raise ValidationError(
                    self.env._(
                        "Action plan comments are required before a "
                        "nonconformity can move to In Progress. This "
                        "requirement can be turned off in the settings."
                    )
                )

    @api.constrains("stage_id")
    def _check_close_with_evaluation(self):
        """OCA's two gates at Closed, each behind its own company switch.

        Restated rather than delegated: OCA enforces two unrelated things in one
        method, so calling super() could only keep or skip both. Source:
        mgmtsystem_nonconformity/models/mgmtsystem_nonconformity.py,
        _check_close_with_evaluation -- diff against it on an OCA upgrade.
        """
        for nonconformity in self:
            if nonconformity.state != "done":
                continue
            gates = nonconformity._qms_gates()
            if (
                gates.qms_require_evaluation_comments
                and not nonconformity.evaluation_comments
            ):
                raise ValidationError(
                    self.env._(
                        "Evaluation comments are required before a "
                        "nonconformity can be closed. This requirement can be "
                        "turned off in the settings."
                    )
                )
            if gates.qms_require_actions_done:
                actions = nonconformity._get_all_actions()
                if not all(actions.mapped("stage_id.is_ending")):
                    raise ValidationError(
                        self.env._(
                            "Every action must be in an ending stage before a "
                            "nonconformity can be closed. This requirement can "
                            "be turned off in the settings."
                        )
                    )

    # qms_severity_rank is deliberately NOT a dependency: re-ranking severities
    # would otherwise recompute every nonconformity not overridden by hand,
    # closed ones included, and post tracking chatter on each. The roll-up uses
    # the ranks current when the items last changed.
    @api.depends("item_ids.severity_id", "item_ids.sequence")
    def _compute_severity_id(self):
        """The severity of the most severe item.

        - no items with a severity: the value is left alone, not blanked, as
          hr.employee._compute_parent_id leaves unassigned records alone
        - items without a severity are skipped rather than ranked 0
        - ties, including every rank still at 0, go to the first item by
          sequence then id, so an unconfigured roll-up is predictable
        """
        for nonconformity in self:
            items = nonconformity.item_ids.filtered("severity_id").sorted(
                lambda item: (item.sequence, item.id)
            )
            if not items:
                continue
            most_severe = items[0]
            for item in items[1:]:
                if (
                    item.severity_id.qms_severity_rank
                    > most_severe.severity_id.qms_severity_rank
                ):
                    most_severe = item
            nonconformity.severity_id = most_severe.severity_id
