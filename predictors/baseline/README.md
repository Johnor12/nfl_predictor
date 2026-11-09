# baseline predictors

Every play scenario event, predicted by sampling simple priors from real plays (2026 so far), plus a few hand-set rules where there's no data yet.

API (`from predictors.baseline import ...`):

- `baseline_predictors(season=2026, priors=None) -> Predictors`: ready for `run_play`.
- `build_priors(season) -> dict`, `save_priors(priors, season)`, `load_priors(season)`: the priors file `priors_<season>.json` (committed, so tests don't need the network).
- Rebuild it with `python -m predictors.baseline.priors 2026` (downloads nflverse data on first use).

From data: unit choice by down, distance, and field position (4th-down decisions); run/pass rate by game script, down, and distance; ball carrier and target by depth chart role; yardage histograms by play type, with separate goal-to-go histograms; sack, scramble, throwaway, completion and interception rates; field goal and extra point make rates; punt and kickoff distances and results; return yards; foul rates per play type; defensive box counts; shotgun rate; injury rate.

Hand-set (no 2026 participation data): personnel groupings, depth-chart lineups for every unit, formation templates, kneel/spike/end-of-half field goal rules, the late-game two-point chart, onside kicks, play clock usage, play durations, recovery odds for muffs/blocked kicks/bad snaps, injury lengths, and which positions commit each foul.
