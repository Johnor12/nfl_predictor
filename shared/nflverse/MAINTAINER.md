# MAINTAINER

- __init__.py: exports `load`, `real_plays`, `RealPlay`.
- download.py: `load` and the file URLs (`FILES`); caches under `.cache/nflverse/`.
- contexts.py: `real_plays` and its pipeline (`_Rosters`, `_game`, `_kind`, `_clock_state`, `_situation`, `_actual`, `_summary`, `_seconds_to_next`).
- test_contexts.py: week 1 contexts are valid; conventions (kickoff orientation, try spots, clock inference). Skipped if the cache is missing.

Notes:
- nflverse lists the receiving team as `posteam` on kickoffs, so the kicking team is our offense there and `x = yardline_100`.
- A try's `x` is the two-point spot. A kicked try is snapped 13 yards behind it, so penalty-moved kicks map back (clamped at the 1 for the rare kick snapped inside the 13).
- The pre-play score is the previous row's `total_home_score`/`total_away_score` (those columns are post-play).
- Weekly rosters can lag the current week's game-day inactives (week 9 had none marked when built), so a few contexts carry extra players.
- 2026 participation data (who was on the field, personnel, formation) isn't published yet; 2025's is.
- `_actual` and `simulators.play.summarize` must produce the same keys (the audit compares them). Change them together.
