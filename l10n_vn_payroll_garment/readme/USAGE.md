**Loading:** in the company to configure, *Settings → Payroll → Load Garment Pay Scheme*
(payroll managers). The notification lists what was created and what was kept. A record whose
code already exists in the company — a parameter, scale, component, category, the structure or
one of its rules — is kept exactly as it is; loading again creates only what is missing.

**Grade amounts** are placeholders. Set each person's grade and step on the contract's pay lines,
or a new version of the `GRADE` scale; a G6 amount goes on the pay line itself.

**Switching an option on:** unarchive the component in *Payroll → Configuration → Pay Components*,
then add its pay lines to the contracts. The attendance bonus also needs the parameters
`vn.policy.attendance_bonus` (the amount) and `vn.policy.attendance_late_max` (late arrivals
allowed); without them its payslips stop with a calculation error naming the parameter.

**Go-live:** contracts move to the structure *VN_GARMENT*, with their participant type and pay
lines.
