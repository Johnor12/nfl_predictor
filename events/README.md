# events

One package per event: a discrete thing that happens, with inputs and an output, predicted by a predictor. 17 are the play scenario's events, 2 the coin toss scenario's, and 1 the game scenario's.

Each event package `events/<event>/` has:

- `README.md`: what the event is, its predictor's signature, its inputs and output, and what the scenario enforces.
- `__init__.py`: the output type (`from events.carry import CarryEnd`), if the output is more than a plain value.
- `predictors/<name>/`: one package per implementation, each exporting `predict` with the event's signature. Every event has a `baseline`; `offensive_formation` and `snap` also have `gbm`, a trained (machine learning) one. `predictors/__init__.py` names the one the system uses (`DEFAULT`): `gbm` for those two, the baseline everywhere else.

Events, in the order the play scenario chains them: `lineups`, `offensive_formation`, `defensive_formation`, `pre_snap`, `snap`, `pass_rush`, `target`, `pass_result`, `punt_kick`, `punt_result`, `kick_attempt`, `free_kick`, `kick_result`, `carry`, `loose_ball`, `fouls`, `injuries` (the chain itself is in `play/README.md`).

The coin toss scenario's events: `coin_toss`, `toss_choice`. The game scenario's: `timeout` (who calls one, and how far into the play clock), asked before every play. Their inputs are in their own READMEs; `game.load_game_predictors(timeout="other")` chooses implementations for all 20.

Inputs common to every play event's predictor:

- `ctx`: the `PlayContext` (game, situation, active players, history).
- `lineups`: the `Lineups` on the field (every event after `lineups` itself).
- `rng`: a seeded `random.Random`, always the last argument. A predictor returns one sample drawn from it, and nothing else random.
- Spots (`x`) are play coordinates: yards from the play's offense's own goal line (the kicking team's on free kicks).

Choosing implementations: `play.load_predictors()` loads every event's default, `play.load_predictors(carry="other")` swaps in `events/carry/predictors/other/`, and `play.load_predictors("baseline")` loads every event's `baseline`. All of them go through `events.predictor(event, name=None)`, which returns an implementation's `predict` (the event's default without a name).

Scoring implementations: `python -m evaluators.play --swap carry=other` scores each play event's predictor against what really happened in a sample of games across seasons (see `evaluators/play/README.md`), and `python -m evaluators.game --swap carry=other` scores whole games, and the timeout predictor, with it (see `evaluators/game/README.md`).

Trained predictors: a model per season, fitted to the real plays of the seasons before it, next to the predictor's code (`model_<season>.txt`). `python -m events.snap.predictors.gbm.train` retrains the snap event's and `python -m events.offensive_formation.predictors.gbm.train` the offensive formation's (see their READMEs). `from events import situation` is the inputs they share: `situation.features(ctx)`, what is known before a scrimmage snap as a row of numbers, and `situation.personnel(group)`. `from events.training import table` builds the table a model is trained on: `table(name, seasons, example, columns) -> DataFrame`, one row per real play that `example(sample)` returns a row for, cached per season under `.cache/training/`.

Baseline priors: `python -m events.baseline_priors` rebuilds every baseline predictor's `priors_<season>.json` for every season from 2011 on, each from that season's real plays (downloading nflverse data on first use); `python -m events.baseline_priors 2026` rebuilds one season, `2020-2026` a range. `from events.baseline_priors import build, save` does the same from code. A season's file holds what that season's data can say, week by week. A game is predicted from what was played before it (the earlier seasons and its own season's earlier weeks), pooled with older seasons counting less, and a predictor can keep a key to the seasons played under the game's rules (`shared/priors/README.md`).
