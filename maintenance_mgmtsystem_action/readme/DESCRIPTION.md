Links a management-system action to the maintenance request it belongs to: a **Maintenance
Request** field on the action, and an **Actions** count with a smart button on the request.

Useful on its own, wherever corrective and preventive actions are tracked in
`mgmtsystem_action` while the work is carried out as maintenance requests. It is also the
shared dependency of plan-seeded action generation and of a quality-management bridge, which
is why it is a module of its own rather than part of either.

It adds no model and no access rule, and depends only on core `maintenance` and
`mgmtsystem_action`.
