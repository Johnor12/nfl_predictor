# MAINTAINER

- __init__.py: `parse_weeks`, shared by the CLIs.
- sample.py: which games an evaluation covers: `EVALUATED`, `sample_games`, `label`. Used by the play, game, and lines evaluators.
- scoring/: the scoring toolkit (see its MAINTAINER.md). Imports nothing from the rest of the project.
- play/: the play and event evaluator (see its MAINTAINER.md).
- lines/: the betting lines evaluator (see its MAINTAINER.md).
- game/: the game evaluator (see its MAINTAINER.md).
- audit/: the play audit (see its MAINTAINER.md).

Notes:
- A new evaluator scores with `scoring.Scorecard` (`add(name, samples, actual)` per case) and reports with `scoring.score_table` and friends, so every level of the system is measured the same way.
- The game evaluator is the only one that can score the clock (plays per game) and anything that builds up over a game (stat lines, the score).
- The audit and the play evaluator answer different questions. The audit compares overall rates (is the simulator reasonable on average?) and checks every play is valid. The play evaluator scores each play's forecast distribution (is it right about this play?).
- The sample is a shuffle of the seasons' played games with a fixed seed, cut to `n`: it changes when the seasons or weeks do, or when new games are played (a season in progress), so compare two runs made on the same day's data.
- The audit still takes one season (`--season`); it is a diagnostic, not a score.
