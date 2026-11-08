# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    paid_day_hours = fields.Float(
        string="Hours per Paid Day",
        help="Hours that make one paid day. Empty: the day's scheduled hours. Set it on a "
        "calendar that combines shifts, so that each shift worked counts as a day.",
    )
    night_start = fields.Float(string="Night From", default=22.0)
    night_end = fields.Float(string="Night To", default=6.0)

    @api.constrains("paid_day_hours", "night_start", "night_end")
    def _check_attendance_day_hours(self):
        for calendar in self:
            if calendar.paid_day_hours < 0:
                raise ValidationError(
                    self.env._(
                        "Hours per Paid Day cannot be negative on calendar %(calendar)s.",
                        calendar=calendar.display_name,
                    )
                )
            for value in (calendar.night_start, calendar.night_end):
                if not 0 <= value <= 24:
                    raise ValidationError(
                        self.env._(
                            "The night window of calendar %(calendar)s must lie between "
                            "00:00 and 24:00.",
                            calendar=calendar.display_name,
                        )
                    )
