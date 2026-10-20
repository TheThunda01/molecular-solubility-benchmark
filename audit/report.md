# Split audit

This export reconstructs the benchmark's outer partitions and inner validation folds without fitting models or exporting target values.

Input records: **1128**. Assignment rows: **2256** (one record per split strategy).

Recorded reference checked: **True**.

| Split | Train | Test | Inner folds | Outer identity overlap | Outer scaffold overlap |
| --- | ---: | ---: | ---: | ---: | ---: |
| random | 902 | 226 | 5 | 0 | 44 |
| scaffold | 902 | 226 | 5 | 0 | 0 |

Inner fit/validation grouping overlaps are zero. Scaffold overlap can occur in the identity-grouped random partition; it is reported, not treated as a failed check.

`assignments.csv` gives row membership and the one inner fold in which each outer-training row is used for validation. All other inner folds use that row for fitting. Outer-test rows have no inner fold.

Group fingerprints support joins and equality checks. They are not anonymization and do not establish chemical dissimilarity. The manifest records runtime versions, code fingerprints, and reference status. See `docs/practical-use.md` for how to apply this export.
