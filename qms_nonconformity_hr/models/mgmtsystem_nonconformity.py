# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    department_id = fields.Many2one(
        default=lambda self: self._default_department_id()
    )

    def _default_department_id(self):
        """The reporter's department, or nothing.

        sudo twice over: hr.employee is readable by HR officers only, and
        res.users.department_id is declared related_sudo=False
        (hr/models/res_users.py:97), so even reading it through the user
        record applies the caller's own rights.
        """
        return self.env.user.sudo().department_id
