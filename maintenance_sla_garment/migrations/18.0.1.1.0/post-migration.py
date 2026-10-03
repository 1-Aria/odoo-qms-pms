# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Map the equipment statuses on a site that already had the preset.

post_init_hook runs at install only, and the stages are noupdate, so a site on
18.0.1.0.0 gets the new statuses from the data file but not the mapping. Post,
so the data file has loaded and the statuses exist.
"""

from odoo import SUPERUSER_ID, api

from odoo.addons.maintenance_sla_garment.hooks import _map_equipment_statuses


def migrate(cr, version):
    _map_equipment_statuses(api.Environment(cr, SUPERUSER_ID, {}))
