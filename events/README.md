# events

One package per event: a discrete thing that happens, with inputs and an output, predicted by a predictor. 17 are the play scenario's events, 2 the coin toss scenario's, and 1 the game scenario's.

Each event package `events/<event>/` has:

- `README.md`: what the event is, its predictor's signature, its inputs and output, and what the scenario enforces.
- `__init__.py`: the output type (`from events.carry import CarryEnd`), if the output is more than a plain value.
- `predictors/<name>/`: one package per implementation, each exporting `predict` with the event's signature. Every event has a `baseline`.

Events, in the order the play scenario chains them: `lineups`, `offensive_formation`, `defensive_formation`, `pre_snap`, `snap`, `pass_rush`, `target`, `pass_result`, `punt_kick`, `punt_result`, `kick_attempt`, `free_kick`, `kick_result`, `carry`, `loose_ball`, `fouls`, `injuries` (the chain itself is in `play/README.md`).

The coin toss scenario's events: `coin_toss`, `toss_choice`. The game scenario's: `timeout`, asked before every play. Their inputs are in their own READMEs; `game.load_game_predictors("baseline", timeout="other")` chooses implementations for all 20.

Inputs common to every play event's predictor:

- `ctx`: the `PlayContext` (game, situation, active players, history).
- `lineups`: the `Lineups` on the field (every event after `lineups` itself).
- `rng`: a seeded `random.Random`, always the last argument. A predictor returns one sample drawn from it, and nothing else random.
- Spots (`x`) are play coordinates: yards from the play's offense's own goal line (the kicking team's on free kicks).

Choosing implementations: `play.load_predictors("baseline")` loads every event's `baseline`, and `play.load_predictors("baseline", carry="other")` swaps in `events/carry/predictors/other/`.

Scoring implementations: `python -m evaluators.play --swap carry=other` scores each play event's predictor against what really happened (see `evaluators/play/README.md`), and `python -m evaluators.game --swap carry=other` scores whole games, and the timeout predictor, with it (see `evaluators/game/README.md`).

Baseline priors: `python -m events.baseline_priors 2026` rebuilds every baseline predictor's `priors_2026.json` from that season's real plays (downloading nflverse data on first use). `from events.baseline_priors import build, save` does the same from code.
