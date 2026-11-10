# MAINTAINER

- __init__.py: exports `simulate_plays`, `simulate_play`, `summarize`, `PlaySimulation`.
- simulator.py: all of it.
- test_simulator.py: a synthetic simulation is valid and repeatable by seed; rule-breaking predictors are collected as failures.

Notes:
- `summarize` and `shared.nflverse.contexts._actual` must produce the same keys. Change them together.
- The values must mean the same thing too. nflverse counts an offensive touchdown as a first down, so `summarize` does as well (`evaluators/play`'s reliability table is where a mismatch like that shows up).
