A catalog is two levels deep. A record with no group is a **code group**; the
records under it are **codes**. A third level is rejected, and so is giving a
group of its own codes a parent.

Every record carries a **Domain** — Quality, Maintenance or Both. A code's
domain must fit its group's: Quality under Quality, Maintenance under
Maintenance, anything under Both. A new code starts with its group's domain.

**Code** is required and unique within the catalog, archived records included.
Archiving `FAB-01` therefore does not release the string: to use it again, delete
the record — and a group that still has codes cannot be deleted. This is
deliberate. Reissuing a retired code merges two different defects in every
historical report.
