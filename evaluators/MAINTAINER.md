# MAINTAINER

- __init__.py: `parse_weeks`, shared by the CLIs, and `executor` (a process pool, or `Inline` for `workers=1`), shared by the play and game evaluators.
- compare.py: `save`, `load`, `compare`, `table`, and the CLI: two evaluations of the same games, case by case.
- test_compare.py: a run compares as itself with no change, and with another run case by case.
- sample.py: which games an evaluation covers: `EVALUATED`, `sample_games`, `label`. Used by the play, game, and lines evaluators.
- test_sample.py: a game without a result or stat lines isn't sampled (a fake schedule; no cache needed).
- scoring/: the scoring toolkit (see its MAINTAINER.md). Imports nothing from the rest of the project.
- play/: the play and event evaluator (see its MAINTAINER.md).
- lines/: the betting lines evaluator (see its MAINTAINER.md).
- game/: the game evaluator (see its MAINTAINER.md).
- audit/: the play audit (see its MAINTAINER.md).

Notes:
- A new evaluator scores with `scoring.Scorecard` (`add(name, samples, actual)` per case) and reports with `scoring.score_table` and friends, so every level of the system is measured the same way.
- The game evaluator is the only one that can score the clock (plays per game) and anything that builds up over a game (stat lines, the score).
- The audit and the play evaluator answer different questions. The audit compares overall rates (is the simulator reasonable on average?) and checks every play is valid. The play evaluator scores each play's forecast distribution (is it right about this play?).
- The sample is a shuffle of the seasons' played games with a fixed seed, cut to `n`: it changes when the seasons or weeks do, or when new games are played (a season in progress), so compare two runs made on the same day's data. A played game is one with a result and stat lines: nflverse publishes the box scores and the charting a few days after a game, and until then its real stat lines would be empty or its charted stats 0. Reading the stat lines to check costs the parent about a second for six seasons.
- `compare` matches cases by their order in the scorecard, which is the games' order and, within a game, the outputs' (`game_outputs`' for the game evaluator): two runs of the same games line up, and an output that got a case more or fewer is skipped rather than misaligned. A saved evaluation is a pickle of this project's own objects, so it is only as durable as their fields: keep one for a comparison, not as a record.
- The audit still takes one season (`--season`); it is a diagnostic, not a score.

## run time

The evaluators are the development loop, so their run time is worth guarding.

- Where it goes (profile with `workers=1`: `python -m cProfile -s cumulative -m evaluators.game --games 4 --sims 20 --workers 1 --no-lines`): the play scenario's `run_play` is about 75% of a game evaluation and 50% of a play evaluation, spread thinly over the predictors once the lineups stopped dominating; validating every simulated play is about 15%; the play evaluator's event cases and their samples about 25% of it.
- Work that doesn't depend on the run belongs outside the per-sim loop. The two big wins so far were of that kind: the lineups predictor ranked the roster from scratch on every play (now once per set of active players), and the play evaluator rebuilt each play's real lineups and read pandas rows once per simulated run.
- Nothing is done in the parent process that a worker can do: reading a season's games and scoring its timeouts and challenges are jobs in the same pool as the games.
- A speedup must not change a score. Check it against a copy of the code from before (`git archive HEAD | tar -x -C <dir>`, with `.cache` linked in): the same small evaluation on both (`--games 8 --sims 6`) must give the same per-case scores (`evaluation.card.outputs[name].scores`, and `pits`, `forecasts`, `halves`), and a few dozen seeded games the same narration (`describe_game`) and stats.
- Not done, because they change the numbers or cost more than they save: fewer validations, a cache of the built rosters on disk, sampling tables for the priors (`shared.priors.choice` rebuilds its weights on every draw, about 7% of a run).
