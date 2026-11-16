# MAINTAINER

- __init__.py: exports `evaluate`, `evaluate_games`, `game_outputs`, `Evaluation`, `write_report`.
- evaluate.py: `evaluate` (one pool of processes; its jobs are a season's games to read, a season's timeouts and challenges to score, and a game to simulate), `evaluate_games` (a job per game, scorecards merged), and the timeout and challenge predictors' cases (`_score_events`).
- outputs.py: `game_outputs`, and what it scores: the stats by family (`FAMILIES`, `STATS`, `CHARTED`), each position's (`POSITION_STATS`), a player's role (`role_of`, `ROLES`), `fantasy`, and `parse` (a row's name taken apart).
- report.py: `write_report`, and `pooled` (a player stat's roles as one row).
- __main__.py: the CLI (the only place the betting lines are fetched).
- test_game.py: synthetic games scored against the scenario itself, with lines; which outputs a game has; a real week. The last is skipped if the nflverse cache is missing.

Notes:
- To score a new stat, add it to a family in `outputs.py` (or a new family, listed for the positions that have a part in it): every team and every player of those positions is then scored on it. It needs a real column (`shared.nflverse.STAT_COLUMNS` or `CHARTED`) and a line in `scenarios/play/stats.py`, under the same name. Anything else goes into `game_outputs`, which reads a real outcome (`RealGame.actual`) and a simulated one (`simulators.game.summarize`) the same way, so the key has to mean the same thing in both.
- A new stat's first check is `mean` against `sim mean` in the team row: a gap is usually a definition (the box score counts a sack as a tackle, its sack yards are negative, its defensive touchdowns are interceptions only), and the play-by-play says which.
- A game has about 1,500 cases (it had 100 before every player was scored); scoring them takes about half a second a game, next to the 17 of simulating it at 100 sims.
- The pooled rows are weighted means of the role rows (their standard errors combined as independent), not a scoring of their own, so a role with more players counts for more.
- A charted stat is only scored from `shared.nflverse.CHARTED_SINCE` on: before it the real value would be a zero that means "not charted".
- Outputs are typed by their values: `bool`, `str`, or a number (see `evaluators/scoring`).
- A case is named by its output and its subject (a team or player id), so one game adds two cases to every `team:` output and several to a `player:` one.
- Only the samples behind the given lines are kept (`samples`); the rest of each game's simulation is dropped once it's scored.
- Line keys are `evaluators.lines`'s: `("margin", game_id)`, `("total", game_id)`, `(stat, game_id, player_id)`.
- Each game's runs are seeded from `seed`, its game id, and the run number, so a game scores the same alone or with others. The timeout samples are seeded per season, so they depend on which of the season's games are in the sample.
- The timeout and challenge cases are read with `real_plays`, not `real_samples`: they need the context and the outcome, not the nflverse rows.
- A challenge case is a real play that started before the two-minute warning of its half, in regulation. Both teams are taken to have a challenge left, and a timeout if they had one before the play: the data doesn't say otherwise.
- A skill player's role comes from `shared.priors.role` (the depth chart rank at the player's own position). A team whose starter is out has no QB1 that week. A lineman's or defender's comes from his depth chart slots (`role_of`): the charts name about 11 starters a side, so a nickel back who plays most snaps is a backup.
