## Checklists

A qualitative question carries a defect code on each of its answers: the code records
what that answer means when it is given. A quantitative question carries one code on the
question itself, since there is a single way to fail a tolerance. Both offer leaf codes
of the quality domain — a code group is a heading, not a finding.

The inspection's lines show a **Defect Code** column beside *Valid values* and
*Success?*, filled only on a line that failed, and a **Quantity Failed** column for how
many units that defect affected — the inspection's own quantity is the lot that was
inspected, not the damage found in it. Both columns are also on the *Inspection Lines*
list, which has a Failed filter, so it doubles as a defect view across inspections.

Quantities are counted in the same unit as the inspection's quantity, and they are not
checked against it: one garment with two defects is two lines of one unit each.

## Populate Defect

The button appears on a nonconformity when all of the following hold: it is in Analysis,
it holds no analysis items yet, and its source inspection has been confirmed — that is,
the inspection is awaiting supervisor approval, or has passed, or has failed. It adds one
analysis item per recorded defect, in the inspection's question order, with the question
in the item's note and the failed quantity carried over. Severity comes from the defect
code; object part and cause are left for the analyst to fill.

The button never deletes anything, which is why it disappears once the analysis holds an
item. To populate again, delete the items by hand first.

It requires the *Quality control / User* group, because it reads the inspection. A
management-system user without that group sees no button.

## Raising a nonconformity from an inspection

The inspection's **Nonconformities** button opens the ones already raised from it, or a new
form when there are none. Either way the new record starts with the inspection, its product,
its number as a title and its company. The product matters beyond convenience: it is what
scopes the defect and object-part dropdowns to the catalog profiles that apply.

An inspection recorded against a picking carries no product of its own — a picking holds
many — so the prefill is empty there and the dropdowns offer nothing until the filter is
cleared in the search panel.

## Actions

An action can point at the inspection it came from, through the **Inspection** field on the
action, which opens that inspection when clicked. The inspection's **Actions** button
counts every action it led to: raised on the inspection directly, listed in the action plan of
a nonconformity raised from it, or set as that nonconformity's immediate action. An action
reachable two ways is counted once.
