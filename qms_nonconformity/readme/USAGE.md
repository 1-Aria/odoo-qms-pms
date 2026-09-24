## Analysis items

Analysis happens in the **Causes and Analysis** tab of a nonconformity, once it has left
draft. Each item records a defect code, the object part it was found on, its cause and its origin.
Cause and origin are recorded per item, so the header's own lists of both are hidden: one
nonconformity can carry defects found different ways, and determination rules read the item.

## Catalog codes on analysis items

The Defect Code and Object Part dropdowns are narrowed to the catalog profiles that apply to
the nonconformity's product, to keep the lists short. The filter is a convenience, not a rule:

- a product with no profile assigned anywhere offers **every** code, not an empty list;
- ticking **Show all catalog codes**, under the Analysis Items, offers every code even when
  profiles do apply.

Code groups are never offered in either case: an item records a code, and a group is only a
heading for one.

## Severity

Each item takes its defect code's **Default Severity**, which can be changed on the
item. The nonconformity's severity is taken from its most severe item and can also be
changed by hand; the change is recorded in the chatter. It sits in the header, beside the
disposition, and stays editable until the record is closed or cancelled.

**Severity ranks start at 0 and must be set.** Open each severity under
*Management System → Configuration → Nonconformities → Severities* and give it a
**Severity Rank** — higher is more severe. Until ranks are set, a nonconformity takes
the severity of its first item. Changing a rank later does not rewrite existing
nonconformities; it applies the next time their items change.

## Disposition

The verdict on the affected material or equipment is chosen from a list you can extend
under *Configuration → Nonconformities → Dispositions*. Each disposition has a **Code**
that cannot be changed once saved: automation matches on the code, never on the label.
