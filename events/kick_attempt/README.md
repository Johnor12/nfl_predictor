# kick attempt event

A field goal, extra point, or fair-catch kick: good, no good, or blocked (a loose ball).

Predictor: `predict(ctx, lineups, kicker, distance, rng) -> KickAttempt`

Inputs (besides the [common ones](../README.md)):

- `kicker`: the kicker's id.
- `distance`: the kick's length in yards (line of scrimmage to the goal line, plus 17; a fair-catch kick is from the spot, so plus 10).

Output (`from events.kick_attempt import ...`):

- `KickAttempt(result, blocked_by, seconds)`: `result` is one of `RESULTS` (`good`, `no_good`, `blocked`).

The play scenario raises `IllegalChoice` unless the result is one of `RESULTS`, and a blocker is on the field for the defense. A fair-catch kick (`lineups.offense.unit == "fair_catch_kick"`) can't be blocked: the play scenario takes `blocked` there as a miss.

Implementations are in [predictors/](predictors/README.md).
