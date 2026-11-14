# play evaluator

Scores the play scenario, and each of its event predictors on its own, against real plays. Every real play of a season is simulated many times; the simulated distribution is scored against what really happened with `evaluators.scoring`.

API (`from evaluators.play import ...`):

- `evaluate(season=2026, weeks=None, sims=100, seed=0, predictors=None, workers=None) -> Evaluation`: `predictors` is a `play.Predictors` (the baseline set if omitted). Each week runs in its own process (`workers=1` to stay in this one). A season at 100 sims takes about 5 minutes on 16 cores.
- `Evaluation`: `season`, `weeks`, `sims`, `plays`, `failures` (simulated plays that raised or broke an invariant), and `card`, a `scoring.Scorecard` (`card.rows()`, `card.pit(name)`, `card.reliability(name)`).
- `write_report(evaluation, path=None)`: markdown at `evaluation_output/play_<season>.md` (gitignored): score tables, PIT histograms, reliability.
- CLI: `python -m evaluators.play --season 2026 [--weeks 1-3] [--sims 100] [--swap carry=tuned]`. `--swap` evaluates `events/carry/predictors/tuned/` in place of the baseline: run it with and without, and compare the rows.

## what is scored

**The play scenario** (`play: ...`): the real inputs, simulated end to end.

- scrimmage downs: action, yards, first down, touchdown, turnover, penalty, points for minus against.
- tries: action, points for minus against.
- free kicks: touchback, return yards.

**Each event predictor** (`<event>: ...`): the predictor is called directly with the event's real inputs and sampled `sims` times; the samples are scored against the event's real output. Its score only moves when that predictor changes.

| event | outputs |
|---|---|
| lineups | unit (4th down, downs 1-3, try); in seasons with on-field data: personnel (the offense's group, the defense's package) and players missed, by unit |
| offensive_formation | shotgun |
| defensive_formation | box |
| pre_snap | foul (type and side, or none) |
| snap | action (run, pass, spike), carrier (depth chart role) |
| pass_rush | result, sack yards, rushers |
| target | receiver (depth chart role), air yards, direction |
| pass_result | result |
| carry | yards and end, by kind (run, scramble, catch); yards for returns (interception, punt, kick) |
| loose_ball | lost (fumbles) |
| punt_kick | blocked, distance |
| punt_result | result |
| kick_attempt | result (field goal, extra point) |
| free_kick | out of bounds, distance |
| kick_result | result |
| fouls | foul (type and side, or none) |
| injuries | injury |

## reading the results

- The score columns are explained in `evaluators/scoring/README.md`.
- **Stand-ins**: nflverse doesn't record the formation, the defensive look, or the play record the fouls and injuries predictors read, and it only records who was on the field in some seasons (2025, not 2026 yet). An event case takes those from simulated runs where the offense sent out the same unit as in the real play (and ran the same kind of play, for fouls), a different run for each sample, so the forecast is spread over what the unrecorded inputs might have been. Every other input is real, including the lineups where the season has them. A case with no such run is counted in the `unscored` column.
- **Players missed**: how many of the 11 players really on the field a simulated lineup left out (the real value is 0, so the fair CRPS rewards getting close and penalizes nothing else). Scored on the runs that sent out the same unit as the real play.
- **In-sample**: each season has its own priors, built from its own plays, so a season's scores are in-sample. `NFL_PRIORS_THROUGH=2025 python -m evaluators.play --season 2026` is the out-of-sample check: 2026's plays with priors built from 2025 only.
- An output that only exists on some samples (sack yards, the carrier of a run) is scored on those samples, so its `sims` is lower.
- The clock isn't scored here: nflverse times a play from its snap to the next snap, the scenario from the end of the previous play. `evaluators/game` scores it as plays per game.
