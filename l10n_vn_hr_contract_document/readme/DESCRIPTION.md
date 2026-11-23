Prints the Vietnamese labour contract (with or without a probation clause), the separate
probation contract and the training contract from the Odoo contract, in Vietnamese, following
the Labor Code 2019 (Art. 21, 24–27, 61) and Circular 10/2020/TT-BLĐTBXH.

- The contract type says which form a contract prints.
- The salary article comes from the contract's pay lines (`l10n_vn_payroll`): the base salary and
  fixed allowances as amounts, variable pay by name with a reference to the company's pay
  regulation, bonuses and welfare in their own article. Each pay component says how it prints.
- The company's own clauses (duties, payday, hours, protective equipment, rights and duties,
  training) are a wording record per company; without one, generic texts print.
- The company's legal representative, and the employee's ID issue date and place and permanent
  address, are added; the contract form lists what its document still lacks.
