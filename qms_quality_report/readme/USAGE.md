Both analyses are under **Quality Control → Reporting**, for quality-control managers, and read
finished inspections only — *waiting*, *success* and *failed*.

- **DHU** is defects ÷ pieces inspected × 100.
- **Defective %** is defective pieces ÷ pieces inspected.
- **FTR** is (pieces inspected − defective pieces) ÷ pieces inspected.

The pivot sums each column on its own, so put the two sums side by side. A failed check with no
quantity counts one defect. Re-inspections are filtered out by default. Fabric roll inspections
are left out of Inspection Analysis and read in the fabric section.

A *No defect code* group in Defect Analysis is a checklist answer or question missing its code.

## Fabric

The fabric section reads confirmed roll inspections only.

- **Roll Analysis** averages roll acceptance and score over the scored rolls, by partner, fabric
  and dye lot.
- **Shade Analysis** counts rolls by dye lot and band, banded-only rolls included, with the ΔE
  averages as measures. An unread ΔE counts as 0, so apply *ΔE measured* (or *Head–tail
  measured*, *Side–centre–side measured*) when reading a ΔE average; the band distribution reads
  all rolls.
- **Fabric Defect Analysis** sums points and counts entries by defect code.
