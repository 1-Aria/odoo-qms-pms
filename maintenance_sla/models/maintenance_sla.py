# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


def _request_selection(model, field_name):
    """A selection of maintenance.request, resolved rather than restated.

    A rule keyed on a value the request cannot hold would never match.
    _description_selection (odoo/fields.py:3020) handles a list, a callable or a
    method name, and picks up any selection_add. This module's own helper:
    maintenance_priority_matrix has an equivalent, and importing it would make
    this module depend on that one.
    """
    field = model.env["maintenance.request"]._fields[field_name]
    return field._description_selection(model.env)


class MaintenanceSla(models.Model):
    """One row is one commitment: P3 · Response · reach In progress · 0:15."""

    _name = "maintenance.sla"
    _description = "Maintenance SLA Rule"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(
        default=10,
        help="When several matching rules share a target stage, the lowest "
        "sequence wins.",
    )
    active = fields.Boolean(default=True)
    # No default: a rule with no company applies to every company, as the
    # priority grid does. No check_company on the teams and categories either:
    # with no company on the rule, _check_company allows only company-less
    # co-records (odoo/models.py:4334-4335), which would lock the common case out
    # of every team and category. A rule naming another company's team simply
    # never matches.
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    maintenance_type = fields.Selection(
        selection=lambda self: _request_selection(self, "maintenance_type"),
        string="Maintenance Type",
        required=True,
    )
    priority = fields.Selection(
        selection=lambda self: _request_selection(self, "priority"),
        string="Priority",
        help="Empty matches any priority, including a request with none.",
    )
    team_ids = fields.Many2many(
        comodel_name="maintenance.team",
        string="Teams",
        help="Empty matches any team.",
    )
    equipment_category_ids = fields.Many2many(
        comodel_name="maintenance.equipment.category",
        string="Equipment Categories",
        help="Empty matches any category. The request's own category must be "
        "listed: parent categories do not cover their children.",
    )
    domain = fields.Char(
        string="Extra Filter",
        help="Optional condition on the request for cases the fields above do "
        "not cover. Literal values only.",
    )
    target_stage_id = fields.Many2one(
        comodel_name="maintenance.stage",
        string="Target Stage",
        required=True,
        ondelete="restrict",
        help="Reaching this stage, or any later one, meets the commitment.",
    )
    # restrict lands on the relation table's stage column (column2, the only one
    # ondelete governs): a stage a rule pauses on cannot be deleted under it.
    pause_stage_ids = fields.Many2many(
        comodel_name="maintenance.stage",
        string="Pause Stages",
        ondelete="restrict",
        help="Time spent in these stages is not counted.",
    )
    # Labelled apart from maintenance.request.duration, core's manual estimate
    # for calendar and gantt display: the two will sit near each other in
    # reports.
    duration = fields.Float(
        string="Target (hours)",
        required=True,
        help="Time allowed from the start of the clock to the target stage.",
    )
    at_risk_pct = fields.Integer(
        string="At Risk (%)",
        default=75,
        help="Share of the target after which a running commitment shows as at "
        "risk.",
    )

    @api.constrains("target_stage_id")
    def _check_target_not_cancel(self):
        """A stage cannot both meet and cancel a commitment.

        This side only sees a rule's target being written; flagging a stage that
        is already a target is caught by maintenance.stage._check_not_a_target.
        """
        for rule in self:
            if rule.target_stage_id.sla_cancel:
                raise ValidationError(
                    self.env._(
                        "'%(stage)s' cancels SLA records, so it cannot also be "
                        "a target stage.",
                        stage=rule.target_stage_id.display_name,
                    )
                )

    @api.constrains("domain")
    def _check_domain(self):
        """Refuse at save a domain that would raise while a request is created.

        Two halves, as core's own checks have. literal_eval refuses what does not
        parse and the dynamic forms (uid, context_today()), which this version
        does not support. expression.expression then refuses a field the request
        does not have, which parses perfectly; it is ir.rule's check
        (base/models/ir_rule.py:63-72) and builds the query without running it.
        """
        requests = self.env["maintenance.request"].sudo()
        for rule in self.filtered("domain"):
            try:
                expression.expression(ast.literal_eval(rule.domain), requests)
            except Exception as error:
                raise ValidationError(
                    self.env._("This domain cannot be read: %(error)s", error=error)
                ) from error

    def _parsed_domain(self):
        """The domain as a list, or [] when unset. The single reader."""
        self.ensure_one()
        return ast.literal_eval(self.domain) if self.domain else []
