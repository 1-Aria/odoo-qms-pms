`maintenance_security` narrows nine core maintenance menus to the Equipment Manager group.
This module restores the grouping core ships, `group_equipment_manager,base.group_user`, so
an internal user who has full rights on maintenance requests can reach them.

Configuration and Teams remain manager-only, as in core.

Install this where technicians and inspectors work in maintenance without being equipment
managers. It carries no Python and no access rules: nine menu records, and a dependency on
`maintenance_security` so its data is applied afterwards.
