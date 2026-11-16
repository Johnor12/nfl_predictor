# play evaluator

Scores the play scenario, and each of its event predictors on its own, against real plays. Every real play of a sample of games is simulated many times; the simulated distribution is scored against what really happened with `evaluators.scoring`.

API (`from evaluators.play import ...`):

- `evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None) -> Evaluation`: the played games of `seasons` (and `weeks`), or a fixed sample of `games` of them (see `evaluators/README.md`). `predictors` is a `play.Predictors` (each event's default implementation if omitted). Games run eight to a process (`workers=1` to stay in this one). It costs about 0.17 core-seconds per game and sim, plus 3 seconds per process to load a season: the CLI's default (160 games, 100 sims) is about 3 minutes on 16 cores and 12 on 4.
- `Evaluation`: `seasons`, `games`, `sims`, `plays`, `failures` (simulated plays that raised or broke an invariant), and `card`, a `scoring.Scorecard` (`card.rows()`, `card.pit(name)`, `card.reliability(name)`).
- `write_report(evaluation, path=None)`: markdown at `evaluation_output/play_<seasons>.md` (gitignored; `play_2021-2026.md`): score tables, PIT histograms, reliability.
- CLI: `python -m evaluators.play [--seasons 2021-2026] [--games 160] [--weeks 1-3] [--sims 100] [--swap carry=tuned]`. `--swap` evaluates `events/carry/predictors/tuned/` in place of the carry event's default: run it with and without, and compare the rows (`--swap snap=baseline` is the snap event's baseline against its default, the trained model).

## what is scored

**The play scenario** (`play: ...`): the real inputs, simulated end to end.

- scrimmage downs: action, yards, first down, touchdown, turnover, penalty, points for minus against.
- tries: action, points for minus against.
- free kicks: touchback, return yards.

**Each event predictor** (`<event>: ...`): the predictor is called directly with the event's real inputs and sampled `sims` times; the samples are scored against the event's real output. Its score only moves when that predictor changes.

| event | outputs |
|---|---|
| lineups | unit (4th down, downs 1-3, try; a real fake punt or field goal is the kicking unit's); in seasons with on-field data: personnel (the offense's group, the defense's package) and players missed, by unit |
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
- **Stand-ins**: nflverse doesn't record the formation, the defensive look, or the play record the fouls and injuries predictors read, and it only records who was on the field in some seasons (2016 to 2025, not 2026 yet). An event case takes those from simulated runs where the offense sent out the same unit as in the real play (and ran the same kind of play, for fouls), a different run for each sample, so the forecast is spread over what the unrecorded inputs might have been. Every other input is real, including the lineups where the season has them, and so is what the data does record of a stand-in: the snap and the defensive formation get the real play's shotgun and personnel group, and the snap its charted box, whatever the run lined up in. So `snap: action` is the snap predictor told how the offense really lined up; `play: action (scrimmage)` is the same call end to end, from formations the scenario predicted itself. A case with no such run is counted in the `unscored` column.
- **Players missed**: how many of the 11 players really on the field a simulated lineup left out (the real value is 0, so the fair CRPS rewards getting close and penalizes nothing else). Scored on the runs that sent out the same unit as the real play.
- **Out of sample**: a game is predicted from what was played before it (earlier seasons, and earlier weeks of its own), so no score has seen its own plays (the exceptions are listed in `evaluators/README.md`). The charted outputs (box, rushers, throwaways) are only scored from 2022 on, where there is charting to score against.
- An output that only exists on some samples (sack yards, the carrier of a run) is scored on those samples, so its `sims` is lower.
- The clock isn't scored here: nflverse times a play from its snap to the next snap, the scenario from the end of the previous play. `evaluators/game` scores it as plays per game.
