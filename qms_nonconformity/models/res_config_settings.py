# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Related to the company, the pattern mgmtsystem_hazard_risk already uses
    # for its own setting. readonly=False makes them editable in Settings.
    qms_require_action_plan_comments = fields.Boolean(
        related="company_id.qms_require_action_plan_comments", readonly=False
    )
    qms_require_evaluation_comments = fields.Boolean(
        related="company_id.qms_require_evaluation_comments", readonly=False
    )
    qms_require_actions_done = fields.Boolean(
        related="company_id.qms_require_actions_done", readonly=False
    )
