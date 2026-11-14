# MAINTAINER

- __init__.py: exports `simulate_game`, `summarize`, `GameSimulation`, `replay`, `distribution`, `forecast`.
- simulator.py: `simulate_game`, `summarize`, `GameSimulation`, `replay`.
- forecast.py: `distribution` and `forecast`.
- __main__.py: the CLI. The only place a simulator reads real data (`shared.nflverse.real_games`).
- test_simulator.py: a synthetic simulation is valid and repeatable by seed, in one process or two; rule-breaking predictors are collected as failures; the forecast.

Notes:
- The simulation happens at the game level: each run is one whole timeline of concrete plays. Nothing is averaged along the way.
- `summarize` and `shared.nflverse.games._actual` must produce the same keys with the same meaning (`evaluators/game` compares them). Change them together.
- Outcomes keep every player's and team's stat line, but not the plays. A 1,000-game simulation is a few megabytes; keeping the timelines would be gigabytes.
- With `workers`, run k goes to process k mod workers, so `outcomes` isn't in run order. Each run's seed doesn't depend on that.
- An unplayed game's inputs are only as good as the latest weekly roster. The CLI refuses a game whose inputs don't validate (usually a kicker who hasn't been activated yet).
