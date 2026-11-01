A strict reader for the time-dependent parameters of `base_time_parameter`.

`base.time.parameter._strict_get(code, date, company=None)` returns the value of a parameter in force
on a date. Unlike the base module's reader, a stored 0 or False is a value, and anything missing raises
an error: an unknown code, a date before the first version, an empty value, or a value that does not
convert to the parameter's type.

A parameter of the given company is used before a parameter with no company. The method reads as
superuser, so calculations can use parameters whatever the user's groups.
