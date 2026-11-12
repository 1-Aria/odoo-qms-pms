# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Attendance Daily Figures",
    "summary": "Per-day normal hours, overtime with its night part, late arrivals and absences, "
    "derived from Odoo's attendance",
    "version": "18.0.1.0.0",
    "author": "1-Aria",
    "website": "https://github.com/1-Aria/odoo-qms-pms",
    "license": "AGPL-3",
    "category": "Human Resources/Attendances",
    "depends": ["hr_attendance", "hr_contract"],
    "data": [
        "views/resource_calendar_views.xml",
        "views/hr_attendance_views.xml",
    ],
    "installable": True,
}
