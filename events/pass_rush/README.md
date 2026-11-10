# pass rush event

What happens to the quarterback on a dropback: how many rushers came, whether he was hit (and by whom), how long until something happened, and the result: throw, sack, scramble, throwaway, or strip sack.

Predictor: `predict(ctx, lineups, formation, defense, rng) -> PassRush`

Inputs (besides the [common ones](../README.md)):

- `formation` / `defense`: the offense's `Formation` and the `DefensiveFormation`.

Output (`from events.pass_rush import ...`):

- `PassRush(rushers, result, seconds, hitters, sackers, sack_yards)`: `result` is one of `RESULTS` (`throw`, `sack`, `scramble`, `throwaway`, `strip_sack`); `sack_yards` is yards lost (>= 0).

The play scenario raises `IllegalChoice` unless the result is one of `RESULTS`; `seconds` isn't negative; hitters and sackers are defenders on the field; a sack has a sacker and non-negative yardage.

Implementations are in [predictors/](predictors/README.md).
