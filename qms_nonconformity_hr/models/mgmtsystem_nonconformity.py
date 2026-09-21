# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MgmtsystemNonconformity(models.Model):
    _inherit = "mgmtsystem.nonconformity"

    department_id = fields.Many2one(
        default=lambda self: self._default_department_id()
    )
    manager_user_id = fields.Many2one(
        default=lambda self: self._default_manager_user_id()
    )

    def _default_department_id(self):
        """The reporter's department, or nothing.

        sudo twice over: hr.employee is readable by HR officers only, and
        res.users.department_id is declared related_sudo=False
        (hr/models/res_users.py:97), so even reading it through the user
        record applies the caller's own rights.
        """
        return self.env.user.sudo().department_id

    def _default_manager_user_id(self):
        """The reporter's manager, or nothing.

        Here rather than in qms_nonconformity: res.users.employee_id comes from
        hr (hr/models/res_users.py:89), which that module does not depend on.
        Every hop may be missing -- no employee, no manager, a manager with no
        user account -- and an empty result leaves the required field for the
        user to fill.
        """
        return self.env.user.sudo().employee_id.parent_id.user_id
