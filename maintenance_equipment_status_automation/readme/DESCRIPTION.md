Keeps a machine's status in step with its corrective requests. A maintenance stage can name the
equipment status that a corrective request's machine takes when the request reaches it — *Down*
when work starts, *Operational* when it is restored, *Retired* when it is scrapped, or whatever
statuses the site defines.

It builds on `maintenance_equipment_status`, whose statuses are configuration; nothing is
mapped, and nothing happens, until a stage names a status.
