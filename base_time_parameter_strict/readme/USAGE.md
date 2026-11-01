From server code:

```python
rate = self.env["base.time.parameter"]._strict_get("vn.rate.ee.si", payslip.date_to)
cap = self.env["base.time.parameter"]._strict_get("vn.si.reference_level", date, company=company)
```

Values are stored as text and read by the parameter's type:

| Type | Text | Returns |
|---|---|---|
| Boolean | `True`, `False`, `1`, `0` | `True` or `False` |
| Date | `YYYY-MM-DD` | a date |
| Float | a number | a float |
| Integer | a whole number, `26` or `26.0` | an int |
| JSON | JSON text | the parsed value |
| Text | any text | the text |
| Record | the version's reference | the record |

Parameters are managed by users in the *Manage Time Parameters* group.
