# MAINTAINER

- __init__.py: exports `simulate_plays`, `simulate_play`, `PlaySimulation`, and re-exports `scenarios.play.summarize`.
- simulator.py: all of it.
- test_simulator.py: a synthetic simulation is valid and repeatable by seed; rule-breaking predictors are collected as failures.

Notes:
- `summarize` moved to the play scenario (`scenarios/play/summary.py`) so the game scenario can use it for its history. Its notes are in `scenarios/play/MAINTAINER.md`.
