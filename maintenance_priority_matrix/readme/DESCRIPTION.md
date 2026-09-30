Derives a maintenance request's priority from the criticality of the machine and the urgency
reported with the request, through a rule table, so that priority means the same thing whoever
raises the request.

Criticality is set on equipment categories and inherited by new machines; urgency is reported on
the request from a fixed list. A grid of criticality × urgency rows says what each combination is
worth. An override is allowed and asks for a reason.

Useful on its own wherever "everything is urgent" makes priority meaningless. It is also the
first module of the maintenance SLA cluster, which needs consistent priority before any target
can mean anything — but it depends on nothing beyond core `maintenance`.
