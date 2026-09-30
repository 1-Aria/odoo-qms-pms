# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools

# Declared once and imported by the other files, so the two vocabularies cannot
# drift apart. Lowercase keys with the explanation in the label: the stored value
# is what rules and reports match on, so it must not be a letter whose meaning
# lives only in a label.
CRITICALITY = [
    ("a", "A — critical"),
    ("b", "B — important"),
    ("c", "C — minor"),
]
URGENCY = [
    ("safety", "Safety risk"),
    ("line_stopped", "Line stopped"),
    ("defects", "Producing defects"),
    ("degraded", "Degraded operation"),
    ("no_impact", "No production impact"),
]


def _request_priority_selection(model):
    """Core's own priority values, resolved rather than restated.

    A rule offering values the request cannot hold would be a bug waiting to
    happen. _description_selection (odoo/fields.py:3020) handles a list, a
    callable or a method name, and picks up any selection_add a future module
    contributes.
    """
    field = model.env["maintenance.request"]._fields["priority"]
    return field._description_selection(model.env)


class MaintenancePriorityRule(models.Model):
    """One row: this criticality with this urgency means this priority."""

    _name = "maintenance.priority.rule"
    _description = "Maintenance Priority Rule"
    _order = "criticality, urgency"

    criticality = fields.Selection(selection=CRITICALITY, required=True)
    urgency = fields.Selection(selection=URGENCY, required=True)
    priority = fields.Selection(
        selection=lambda self: _request_priority_selection(self),
        required=True,
    )
    # No default: a row with no company is the grid every company uses, and
    # defaulting to the active company would make the global row the one nobody
    # creates by accident. Uniqueness includes the company, so two companies may
    # disagree.
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    active = fields.Boolean(default=True)

    # Uniqueness is a unique INDEX over COALESCE(company_id, -1), not a table
    # constraint: a plain "unique (criticality, urgency, company_id)" treats
    # NULLs as distinct, so the company-less rows -- the grid every company uses,
    # and the common case here -- could be duplicated freely. ir_filters solves
    # the same problem the same way (base/models/ir_filters.py:185-191).
    #
    # One index covers both kinds of row, so there is no table constraint beside
    # it, and there is no Python constraint either: a duplicate reports itself as
    # a raw duplicate-key error rather than a sentence, because Odoo builds the
    # readable message by looking e.diag.constraint_name up in pg_constraint and
    # matching _sql_constraints (models.py:7574-7590), and an index is not a
    # constraint.
    #
    # An @api.constrains cannot recover that message. On create, create() runs
    # its INSERT (:5224) before it validates (:5297). On write, the constraint's
    # own search() triggers the pre-search flush (:5795), which writes the
    # pending row and makes the database raise inside the constraint. It was
    # tried, and failed on the write path exactly there.
    #
    # The one mechanism that would give a readable message for every case is a
    # table constraint with PostgreSQL 15's UNIQUE NULLS NOT DISTINCT. Not used:
    # Odoo 18 runs on older servers too, and a module that fails to install on
    # PostgreSQL 14 is worse than an ugly message on a configuration grid.
    def _auto_init(self):
        result = super()._auto_init()
        tools.create_unique_index(
            self._cr,
            "maintenance_priority_rule_pair_uniq",
            self._table,
            ["criticality", "urgency", "COALESCE(company_id, -1)"],
        )
        return result

    @api.model
    def _priority_for(self, criticality, urgency, company=None):
        """The priority this pair means, or False.

        A row for the company wins over a company-less row. Either input empty,
        or nothing configured, gives False -- the unconfigured state, which
        leaves a request's priority alone.
        """
        if not criticality or not urgency:
            return False
        company = company or self.env.company
        rules = self.search(
            [
                ("criticality", "=", criticality),
                ("urgency", "=", urgency),
                ("company_id", "in", [company.id, False]),
            ]
        )
        rule = rules.filtered("company_id")[:1] or rules[:1]
        return rule.priority or False
