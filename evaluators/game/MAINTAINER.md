# MAINTAINER

- __init__.py: exports `evaluate`, `evaluate_games`, `game_outputs`, `Evaluation`, `write_report`.
- evaluate.py: `evaluate` (one pool of processes; its jobs are a season's games to read, a season's timeouts and challenges to score, and a game to simulate), `evaluate_games` (a job per game, scorecards merged), `game_outputs`, the stats scored (`TEAM_STATS`, `PLAYER_STATS`), and the timeout and challenge predictors' cases (`_score_events`).
- report.py: `write_report`.
- __main__.py: the CLI (the only place the betting lines are fetched).
- test_game.py: synthetic games scored against the scenario itself, with lines; a real week. The last is skipped if the nflverse cache is missing.

Notes:
- To score a new output, add it to `game_outputs`. It reads a real outcome (`RealGame.actual`) and a simulated one (`simulators.game.summarize`) the same way, so the key has to mean the same thing in both. A stat needs a column in `shared.nflverse.STAT_COLUMNS`.
- Outputs are typed by their values: `bool`, `str`, or a number (see `evaluators/scoring`).
- A case is named by its output and its subject (a team or player id), so one game adds two cases to every `team:` output and several to a `player:` one.
- Only the samples behind the given lines are kept (`samples`); the rest of each game's simulation is dropped once it's scored.
- Line keys are `evaluators.lines`'s: `("margin", game_id)`, `("total", game_id)`, `(stat, game_id, player_id)`.
- Each game's runs are seeded from `seed`, its game id, and the run number, so a game scores the same alone or with others. The timeout samples are seeded per season, so they depend on which of the season's games are in the sample.
- The timeout and challenge cases are read with `real_plays`, not `real_samples`: they need the context and the outcome, not the nflverse rows.
- A challenge case is a real play that started before the two-minute warning of its half, in regulation. Both teams are taken to have a challenge left, and a timeout if they had one before the play: the data doesn't say otherwise.
- Roles come from `shared.priors.role` (the depth chart rank at the player's own position). A team whose starter is out has no QB1 that week.
