A starting SLA configuration for garment manufacturing, so that commitments are measured from the
day `maintenance_sla` is installed:

- a stage flow with waiting stages, which pause the restore clock, and a confirmation stage before
  *Done*;
- response and restore targets for each priority, and a fallback for requests without one;
- a priority grid of equipment criticality × reported urgency, for `maintenance_priority_matrix`;
- waive reasons.

It adds no models, fields or views: it is configuration, for a site to tune.
