## Test

Tick **Roll Inspection** on the test and set the limit in points per 100 m² and the cap per
metre — 4 under the 4-point system. If the buyer's standard gives the limit per 100 yd²,
multiply it by 1.196. A limit of 0 leaves the score unjudged. Set the three ΔE maxima — against
the standard, head–tail and side–centre–side — as the spectrophotometer reports them; 0 leaves
one unjudged. An inspection keeps the
settings its test had when the test was set; editing the test changes later inspections only.

## Trigger

Set the fabric receipt trigger to the *after* timing, without *inspection per lot*, so each
receipt line gets one inspection holding all of its rolls.

## Rolls

On the inspection's **Rolls** page, add a row per roll and pick its lot. Enter its length in
metres and width in centimetres to score it, then open its point entries with the row's list
button and enter each defect with the metre it lies in (1 for the first) and its points, 1 to 4. A running defect is entered once per metre
it covers; no metre counts more than the cap. A roll with neither length nor width is not
scored — the rest of a sample. **Load rolls**, above the list, adds a row for every lot on the receipt
line that has none yet, in receipt order, so every roll can be banded while only the sample is
scored. Rows already there are kept; a deleted row comes back at the next press. The defect list follows the product's catalog profiles;
**Show all catalog codes** widens it.

## Shade

In each roll's row, enter the spectrophotometer's ΔE against the standard, head–tail and
side–centre–side, and the shade band from shade sorting: one letter, A closest to the standard
and meaningful within the dye lot, or a 555 code of three digits 1–9. Lowercase is stored as
uppercase; any other format is refused. A roll passes only when its points and every judged ΔE
are within the test's limits.

## Lots

A lot's dye lot is read from its name up to the last "-", by the [Dye lot]-[Roll] convention,
and can be corrected on the lot. Its shade band appears once an inspection banding it is
confirmed, and follows the latest one. Group the lot list by dye lot to see the bands for
cutting: never mix two bands of one dye lot in a lay.

## Verdict

The inspection succeeds only when every question passes and every roll passes. One failing
roll sends it to supervisor approval, which records it as failed; which rolls are returned is
decided on the nonconformity.

## Nonconformity

Populate Defect on a nonconformity raised from a confirmed roll inspection adds, after the
checklist's items, one item per defect code found on the rolls, with the number of entries as
the quantity and the rolls named in the note.

## Counting fields

The sample size, pieces inspected, defective pieces and re-inspection fields of the quality-control
module describe garment checks, and are hidden on roll inspections, whose figures are on the rolls.
