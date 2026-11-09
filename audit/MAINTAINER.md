# MAINTAINER

- __init__.py: exports `run_audit`, `Audit`, `metrics`, `write_report`.
- audit.py: `run_audit` and `sim_outcome` (a simulated play summarized with the same keys as `RealPlay.actual`).
- report.py: `METRICS` (definitions), `metrics`, `write_report`.
- __main__.py: the CLI.
- test_audit.py: a week 1 audit has no failures. Skipped if the nflverse cache is missing.

Notes:
- To add a metric, append a `Metric` to `METRICS`. Its filter and value see `(context, outcome)`, where the outcome has the keys produced by both `nflverse.contexts._actual` and `sim_outcome`. Keep those two in sync.
