# MAINTAINER

- README.md: the API, the event chain, and what the game keeps between plays.
- RULES.md: the hardcoded NFL rules, the invariants, and what isn't built yet.
- __init__.py: the public API (re-exports).
- context.py: `GameContext` and `validate_game_context`.
- predictors.py: the `GamePredictors` bundle and `load_game_predictors`.
- record.py: `Stoppage` and `GameResult`.
- game.py: `run_game`, the chain: one step per play (timeout, play, clock, period).
- clock.py: the clock's rules as small functions (two-minute warning, the snap that never came, the try after time expires, the runoff choice, overtime's setup) and constants.
- overtime.py: `Overtime`, which tracks each team's possession and says when the score ends the game.
- roster.py: `Availability`, who can play the next play.
- validate.py: `validate_game`, the invariants.
- describe.py: narration.
- testing.py: a synthetic game, chaos predictors, and `with_events`.
- test_game.py: fuzzed invariants, baseline games, and hand-built tests for endings, timeouts, the clock, overtime, and injuries.

Notes:
- A situation's `clock` is the clock when the last play ended. The play scenario takes the pre-snap time off a running clock itself, so the game only finds out afterward that the period (or the two-minute warning) came first; it then discards that play and never records it. The play's draws from the `rng` are still used up, so games stay reproducible.
- `step` returns the next play's `Situation`, or None when the game is over. Every way a period can end goes through `end_period`.
- The play scenario's `next` situation has the clock running only for `clock_after == "running"`. The game also runs it for `"ready"`, as `shared.nflverse` infers for real plays.
- Rules that change between seasons (overtime) come from `shared.rulebook`. Rules that don't (quarter length, timeouts per half) are constants in clock.py.
- `Overtime.over` must be called after every overtime play, in order: it keeps the possession state.
- When adding a rule, add a test in test_game.py. The fuzz test only proves internal consistency.
- A scripted game is hard to build play by play. Test game rules with `with_events` on top of the baseline (see `QUIET` in test_game.py, a game of kneel-downs), or on the pieces directly (`Overtime`, `Availability`).
- Speed: about 0.2 seconds a game with the baseline predictors, most of it in the lineups predictor's depth chart lookups.
