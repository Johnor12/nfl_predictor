# MAINTAINER

- __init__.py: exports `SEASONS`, `load`, `real_plays`, `real_samples`, `RealPlay`, `real_games`, `RealGame`, `STAT_COLUMNS`.
- download.py: `SEASONS`, `load`, and the file URLs (`FILES`); caches under `.cache/nflverse/`. A file in `OPTIONAL` that isn't published (404) leaves a `.missing` marker, so it's only asked for once. `load` renames the teams that have moved (`TEAMS`) in every file's team columns.
- depth.py: `depth_charts(season)`: the depth charts in the 2025+ shape for every season (the weekly charts before 2025 are dated the day before the week's first game, and their slots renamed by `SLOTS`).
- contexts.py: `real_samples`, and `real_plays` and its pipeline (`_Rosters`, `_weekly_snaps`, `_game`, `_kind`, `_clock_state`, `_situation`, `_actual`, `_summary`, `_seconds_to_next`).
- games.py: `real_games`, `RealGame`, `STAT_COLUMNS`, and `_actual` (a game's real outcome from the schedule and the player stats file). Uses contexts.py's `_Rosters`, `_players`, and `_game`, so a game and its plays get the same inputs.
- test_contexts.py: week 1 contexts are valid; conventions (kickoff orientation, try spots, clock inference); timeouts before plays; week 1 games (inputs, outcomes, stat lines); a season in the older formats (2014). Skipped if the cache is missing.

Notes:
- nflverse lists the receiving team as `posteam` on kickoffs, so the kicking team is our offense there and `x = yardline_100`.
- A try's `x` is the two-point spot. A kicked try is snapped 13 yards behind it, so penalty-moved kicks map back (clamped at the 1 for the rare kick snapped inside the 13).
- The pre-play score is the previous row's `total_home_score`/`total_away_score` (those columns are post-play).
- Weekly rosters can lag the current week's game-day inactives (week 9 had none marked when built), so a few contexts carry extra players.
- 2026 participation data (who was on the field, personnel, formation) isn't published yet; 2016 to 2025 are. When it appears, delete `.cache/nflverse/pbp_participation_2026.missing` (or `load("participation", 2026, refresh=True)`) and rebuild the 2026 priors: the snaps switch to the per-unit counts and the lineups priors gain 2026's personnel on their own.
- In a participation row `offense_players` is the team nflverse lists in possession, which on a kickoff is the receiving team. `_weekly_snaps` names each side's unit from the play type (`UNITS`); `shared.priors.played` splits `players_on_play` by team instead.
- Snap counts come from Pro Football Reference, with its own player ids. The weekly rosters carry a PFR id for about 80% of the rows (few linemen), the rest are matched by team and name; about 1% stay unmatched and have no snaps.
- `SNAP_WEEKS` (4) is how far back a player's snaps reach. Two to four weeks predicted 2025's lineups best (see `events/lineups/predictors/baseline/MAINTAINER.md`).
- `_actual` and `simulators.play.summarize` must produce the same keys with the same meaning (the audit and `evaluators/play` compare them). Change them together.
- `games._actual` and `simulators.game.summarize` must produce the same keys with the same meaning (`evaluators/game` compares them). Change them together.
- Timeouts are their own pbp rows (`timeout == 1`, `timeout_team`). A play's own row has `timeout == 1` when its challenge was lost; that timeout is attributed to the next play. Only the first timeout between two plays is kept.
- The player stats file has a leftover row per team without a player id (penalties that weren't assigned). `games._actual` skips it, so team penalties are the players' only.
- `real_plays` and `real_games` take about 5 seconds for a season before the first play or game comes out, nearly all of it building the rosters; that is the fixed cost of every evaluator process.
- A cached file doesn't refresh itself: `load(name, season, refresh=True)` after new games are played.
- Older seasons, and what was done about each difference (a new one belongs in the same places: `load` for names, `depth.py` for depth charts, `_Rosters.players` for a player's fields):
  - Team codes: only the play-by-play uses the current ones for every season. `load` renames the rest (`TEAMS`).
  - Roster positions before 2016 are detailed (`T`, `DE`, `CB`); `GROUPS` maps them. `years_exp` is missing for a few 2016 rows.
  - The weekly depth charts (before 2025) have wrong rows: a quarterback at left guard, the kicker and punter swapped. They are kept as published; the baseline lineups predictor doesn't trust a slot over a position for linemen and specialists.
  - A roster sometimes lists the kicker as a punter (the 2022 and early 2023 Chargers). A team with two punters and no kicker gets the depth chart's kicker as its `K`.
  - Participation rows before 2023 list `players_on_play` in another id system, and personnel without the quarterback and linemen (`1 RB, 1 TE, 3 WR`); `shared.priors.played` and `personnel` read both forms. About a quarter of those seasons' rows have no personnel.
  - 2016's week 1 rosters hold up to 90 players a team (not yet cut down), so those contexts carry extras.
  - A team can really have no kicker (the 2015 Jets, week 9: the punter kicked). The context is kept as it is and fails `validate_context`; its field goal plays can't be simulated.
  - A few roster files miss linemen (the 2011 Rams, week 1, have four), and their plays fail in simulation.
