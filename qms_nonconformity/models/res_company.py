# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Real Boolean columns rather than ir.config_parameter, which the spec first
    # named and which cannot carry a default-on switch: res.config.settings
    # writes a False Boolean by calling set_param(key, False), and set_param
    # deletes the parameter when the value is falsy
    # (base/models/ir_config_parameter.py:91-98). get_param then returns the
    # caller's default, so a gate read with a default of True would come back on
    # the moment someone switched it off. A column stores False as False, and
    # being on the company it also lets each company keep its own policy.
    qms_require_action_plan_comments = fields.Boolean(
        string="Require action plan comments",
        default=True,
        help="Action plan comments must be filled before a nonconformity can "
        "move to In Progress.",
    )
    qms_require_evaluation_comments = fields.Boolean(
        string="Require evaluation comments",
        default=True,
        help="Evaluation comments must be filled before a nonconformity can be "
        "closed.",
    )
    qms_require_actions_done = fields.Boolean(
        string="Require all actions done",
        default=True,
        help="Every action of a nonconformity must be in an ending stage before "
        "it can be closed.",
    )
