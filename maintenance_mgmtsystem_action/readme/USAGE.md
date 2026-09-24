## On the action

The **Maintenance Request** field sits beside Reference. Setting it links the action to that
request, and clicking it opens the request.

## On the request

The **Actions** button counts the actions belonging to the request and opens them. At a count
of zero it opens an empty list whose New button already carries the request, so an action
raised there is linked without further typing. Nothing else is prefilled: an action's subject
and its response type are for the person creating it.

The button needs the *Management system / Viewer* group or higher, because the count reads
action records. Someone without it sees the request as before, with no button.

## Extending the count

The count follows `maintenance.request._action_domain()`, which by itself matches the actions
that point at the request. A module that knows about other routes — actions attached to a
nonconformity raised from the request, for instance — overrides that method to add them, and
both the count and the list follow. When it does, it should add its own field paths to the
`_compute_action_count` dependencies so the count still refreshes when those records change.
