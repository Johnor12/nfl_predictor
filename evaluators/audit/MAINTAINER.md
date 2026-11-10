# MAINTAINER

- __init__.py: exports `run_audit`, `Audit`, `metrics`, `write_report`.
- audit.py: `run_audit`, which feeds `shared.nflverse.real_plays` to `simulators.play.simulate_plays` and pairs the outcomes.
- report.py: `METRICS` (definitions), `metrics`, `write_report`.
- __main__.py: the CLI (`--weeks` is read by `evaluators.parse_weeks`).
- test_audit.py: a week 1 audit has no failures. Skipped if the nflverse cache is missing.

Notes:
- To add a metric, append a `Metric` to `METRICS`. Its filter and value see `(context, outcome)`, where the outcome has the keys produced by both `shared.nflverse.contexts._actual` and `simulators.play.summarize`.
