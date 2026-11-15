# game simulator

Plays the game scenario many times from one set of inputs, checks every game, and presents the distributions of what happened.

API (`from simulators.game import ...`):

- `simulate_game(ctx, predictors, sims=1000, seed=0, workers=1) -> GameSimulation`: runs the `GameContext` `sims` times with the given `GamePredictors`. A game that raises or breaks an invariant is recorded as a failure instead of stopping the run. `workers` splits the runs across processes.
- `GameSimulation`:
  - `outcomes`: one summary per game that ran.
  - `failures`: `(run number, message, traceback or box score)`.
  - `example`: the first game's full `GameResult`.
  - `values(key)`, `team(team, stat)`, `player(player_id, stat)`: one value per outcome (0 for a player or team without the stat).
- `summarize(result) -> dict`: one game's outcome: `points` by team, `margin` (home minus away), `total`, `winner` (None for a tie), `overtime`, `plays`, `teams` (`{team: {stat: value}}`), `players` (`{player id: {stat: value}}`). Same keys and meaning as `shared.nflverse`'s `RealGame.actual`. Stat names are the play scenario's.
- `replay(ctx, predictors, seed, run) -> GameResult`: one run again, in full (to narrate it with `game.describe_game`).
- `distribution(values) -> dict`: mean and the 10th, 25th, 50th, 75th, and 90th percentiles.
- `forecast(sim) -> str`: win probabilities, the distributions of the score, margin, total, and plays, and the main players' stat lines.
- CLI: `python -m simulators.game 2026_10_NE_DET [--sims 1000] [--workers N] [--swap carry=other]` forecasts a real game from `shared.nflverse`'s inputs, played or not, of any season from 2011 on. The baseline predictors know the seasons before the game's; `NFL_PRIORS_THROUGH=2026` in the environment adds this season's games so far for an upcoming 2026 game (`shared/priors/README.md`).

Every run has its own seed (from `seed`, the game id, and the run number), so any game can be replayed.

About 0.25 seconds a game with the baseline predictors, validation included.
