# MAINTAINER

- __init__.py: exports `load`, `real_plays`, `real_samples`, `RealPlay`, `real_games`, `RealGame`, `STAT_COLUMNS`.
- download.py: `load` and the file URLs (`FILES`); caches under `.cache/nflverse/`.
- contexts.py: `real_samples`, and `real_plays` and its pipeline (`_Rosters`, `_game`, `_kind`, `_clock_state`, `_situation`, `_actual`, `_summary`, `_seconds_to_next`).
- games.py: `real_games`, `RealGame`, `STAT_COLUMNS`, and `_actual` (a game's real outcome from the schedule and the player stats file). Uses contexts.py's `_Rosters`, `_players`, and `_game`, so a game and its plays get the same inputs.
- test_contexts.py: week 1 contexts are valid; conventions (kickoff orientation, try spots, clock inference); timeouts before plays; week 1 games (inputs, outcomes, stat lines). Skipped if the cache is missing.

Notes:
- nflverse lists the receiving team as `posteam` on kickoffs, so the kicking team is our offense there and `x = yardline_100`.
- A try's `x` is the two-point spot. A kicked try is snapped 13 yards behind it, so penalty-moved kicks map back (clamped at the 1 for the rare kick snapped inside the 13).
- The pre-play score is the previous row's `total_home_score`/`total_away_score` (those columns are post-play).
- Weekly rosters can lag the current week's game-day inactives (week 9 had none marked when built), so a few contexts carry extra players.
- 2026 participation data (who was on the field, personnel, formation) isn't published yet; 2025's is.
- `_actual` and `simulators.play.summarize` must produce the same keys with the same meaning (the audit and `evaluators/play` compare them). Change them together.
- `games._actual` and `simulators.game.summarize` must produce the same keys with the same meaning (`evaluators/game` compares them). Change them together.
- Timeouts are their own pbp rows (`timeout == 1`, `timeout_team`). A play's own row has `timeout == 1` when its challenge was lost; that timeout is attributed to the next play. Only the first timeout between two plays is kept.
- The player stats file has a leftover row per team without a player id (penalties that weren't assigned). `games._actual` skips it, so team penalties are the players' only.
- `real_games` takes about 20 seconds for a season, nearly all of it building the rosters.
- A cached file doesn't refresh itself: `load(name, season, refresh=True)` after new games are played.
