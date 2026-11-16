# MAINTAINER

- README.md: the API, the event chain, and what the game keeps between plays.
- RULES.md: the hardcoded NFL rules, the invariants, and what isn't built yet.
- __init__.py: the public API (re-exports).
- context.py: `GameContext` and `validate_game_context`.
- predictors.py: the `GamePredictors` bundle and `load_game_predictors`.
- record.py: `Stoppage` and `GameResult`.
- game.py: `run_game`, the chain: one step per play (timeouts, play, challenge, clock, period).
- clock.py: the rules between plays as small functions (two-minute warning, the snap that never came, the clock at a timeout, the try after time expires, the runoff choice, who may challenge, who is charged for an injury, overtime's setup) and constants.
- overtime.py: `Overtime`, which tracks each team's possession and says when the score ends the game.
- roster.py: `Availability`, who can play the next play (injuries, disqualifications, and emergency replacements).
- validate.py: `validate_game`, the invariants.
- describe.py: narration.
- testing.py: a synthetic game, chaos predictors, and `with_events`.
- test_game.py: fuzzed invariants, baseline games, and hand-built tests for endings, timeouts, the clock, overtime, injuries and stand-ins, challenges, the fair-catch kick, disqualifications, and the 10-second runoff.

Notes:
- A situation's `clock` is the clock when the last play ended. The play scenario takes the pre-snap time off a running clock itself, so the game only finds out afterward that the period (or the two-minute warning) came first; it then discards that play and never records it. The play's draws from the `rng` are still used up, so games stay reproducible.
- `step` returns the next play's `Situation`, or None when the game is over. Every way a period can end goes through `end_period`.
- The play scenario's `next` situation has the clock running only for `clock_after == "running"`. The game also runs it for `"ready"`, as `shared.nflverse` infers for real plays.
- Rules that change between seasons (overtime) come from `shared.rulebook`. Rules that don't (quarter length, timeouts per half) are constants in clock.py.
- `Overtime.over` must be called after every overtime play, in order: it keeps the possession state. `after` calls it first, so nothing is recorded after the play that ends the game.
- `end_period` reads the period's number: odd ones go on from the same situation, the second quarter and every overtime period 4n+2 end a half (a kickoff by `second_half_kicking` of the latest toss), and the fourth quarter and every overtime period 4n start with a toss. Regular season overtime never gets past its first period.
- A challenge is asked for with the play's `summarize` outcome, the same keys a real play's `actual` has, so the predictor can be scored on real plays (`evaluators/game`). It never changes the play.
- A fair-catch kick with no time left: `after` hands out the down and sets `kick_only`; `step` runs the play and, if the lineups predictor didn't send the kick out, discards it and ends the period (like the snap that never came).
- A stand-in is a copy of the `Player` with another `position`, only in the plays' inputs (`Availability.active`); `GameResult.context.players` and the stats keep him as he is. `kneel` in test_game.py picks whoever is available, so tests with injuries can use `QUIET`.
- When adding a rule, add a test in test_game.py. The fuzz test only proves internal consistency.
- A scripted game is hard to build play by play. Test game rules with `with_events` on top of the baseline (see `QUIET` in test_game.py, a game of kneel-downs), or on the pieces directly (`Overtime`, `Availability`).
- The game keeps `warned` (who has one unsportsmanlike conduct foul) only by copying each play's `PlayResult.warned` into the next `PlayContext`; the rule itself lives in the play scenario.
- Measured (2026-11-16, the evaluators' default 160 games of 2021 to 2026 at 100 sims, before and after challenges, the second timeout, injury stoppages, stand-ins, the third overtime kickoff, the fair-catch kick, and fake kicks went in together): no game, team, or player score moved by more than 1.2 standard errors, and the simulation takes as long as before. `timeout: caller (rest of the game)` 0.0421 -> 0.0384 (-9%, 2 standard errors): a lost challenge is no longer a timeout called for no reason the situation shows. The baseline challenge predictor scores level with forecasting the overall rates on every play (skill -0.1%): its buckets say how often, not which play. A simulated game has about 0.5 challenges (as real ones do), 0.25 timeouts charged for injuries, and 0.1 fakes; fair-catch kicks and third overtime periods are rarer than the sample can show.
- Speed: about 0.2 seconds a game with the baseline predictors, most of it in the lineups predictor's player ranking.
