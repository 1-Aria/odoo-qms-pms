## Catalogs

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

## Catalog profiles

A **catalog profile** bundles code groups — never individual codes — from both
catalogs, and is assigned to products so that only the relevant part of the
vocabulary is offered. A profile also carries a Domain, and a group whose domain
clashes with it is refused: a Maintenance group cannot go into a Quality profile.
A group marked Both fits either.

Assign profiles on a product variant, on a product, or on a product category —
the **Catalog Profiles** tab on the product form, or the group of the same name
on the category form. Assignment is **additive**: a variant ends up with its own
profiles, its product's, its category's and those of every parent category. It
never overrides. The read-only **Effective** field on each form shows the result,
so a variant displays what it inherits as well as what was set on it.

Nothing is required. A product with no profile anywhere simply offers no codes
in the filtered dropdowns, and the user clears the filter to see the whole
catalog.
