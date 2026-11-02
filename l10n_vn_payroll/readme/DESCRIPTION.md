Vietnamese payroll on OCA `payroll`.

This first step holds the configuration layer:

- **Pay components:** each earning, deduction, employer contribution and total, with its legal nature,
  whether it counts in the SI base and the OT base, its PIT treatment, where its amount comes from and
  how it is prorated.
- **Pay scales:** grade and step tables and productivity levels, with dated versions of their amounts.
- **Contract pay lines:** dated lines on each contract. A change is a new line from its date; the
  contract's wage follows the lines whose component sets it.
- **Payroll roles:** Officer, Reviewer, Approver, Reader and Manager. Officers see every payslip of their
  companies, and new users receive no payroll role.
- **Statutory parameters:** minimum wages, the SI reference level, contribution rates and caps, PIT
  brackets and deductions, OT factors and limits, created for every Vietnamese company and kept up to
  date at each upgrade, without overwriting values edited by hand.
- **Pay profiles** (step 2): participant types (labour contract, probation contract, manager without a
  labour contract, contract under 1 month) deciding the SI funds, the SI base and the PIT method; on the
  contract, the participant type, a declared SI base and the probation form; on the employee, the pay
  group, attendance mode, minimum-wage region, tax residency, union membership and commitment form year;
  PIT dependents registered on the employee's relatives.
