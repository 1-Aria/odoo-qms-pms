## Analysis items

Analysis happens in the **Causes and Analysis** tab of a nonconformity, once it has left
draft. Each item records a defect code, the object part it was found on and its cause.
The defect and object-part dropdowns offer only the codes allowed by the catalog
profiles of the nonconformity's product; clear the filter in the dropdown's search to
see the whole catalog. Cause is recorded per item, so the header's own cause list is
hidden.

## Severity

Each item takes its defect code's **Default Severity**, which can be changed on the
item. The nonconformity's severity is taken from its most severe item and can also be
changed by hand; the change is recorded in the chatter.

**Severity ranks start at 0 and must be set.** Open each severity under
*Management System → Configuration → Nonconformities → Severities* and give it a
**Severity Rank** — higher is more severe. Until ranks are set, a nonconformity takes
the severity of its first item. Changing a rank later does not rewrite existing
nonconformities; it applies the next time their items change.

## Disposition

The verdict on the affected material or equipment is chosen from a list you can extend
under *Configuration → Nonconformities → Dispositions*. Each disposition has a **Code**
that cannot be changed once saved: automation matches on the code, never on the label.
