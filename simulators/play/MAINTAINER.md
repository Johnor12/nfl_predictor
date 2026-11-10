# MAINTAINER

- __init__.py: exports `simulate_plays`, `summarize`, `PlaySimulation`.
- simulator.py: all of it.
- test_simulator.py: a synthetic simulation is valid and repeatable by seed; rule-breaking predictors are collected as failures.

Notes:
- `summarize` and `shared.nflverse.contexts._actual` must produce the same keys. Change them together.
