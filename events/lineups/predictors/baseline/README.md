# baseline lineups predictor

The unit from hand-set rules and 4th-down priors, the personnel group and the defense's package from the priors, then 11 players who have been playing in the unit.

API (`from events.lineups.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, rng) -> Lineups`

From data:

- unit choice by down, distance, and field position (`unit`; this is the 4th-down decision), and the two-point attempt rate (`two_point`).
- the offense's personnel group by game script, down, and distance (`personnel`), and the defense's package against it (`package`). Both come from who was on the field, which nflverse publishes after a season: 2025 has it, 2026 doesn't yet, so 2026 games use 2025's.
- the players: each `Player.snaps`, his snaps in his team's last four weeks by unit. Backs, receivers, tight ends, defenders, and kicking-unit regulars are drawn by them (sharpened a little toward the regulars), so a player is on the field about as often as he has been. Linemen and specialists are the ones with the most. Where a season records who was on the field (2025), the snaps are per kicking unit; otherwise (2026) they are the per-game snap counts, which only say offense, defense, or special teams.

From the depth chart: the quarterback and the returners, and everyone when a team has no snaps yet (week 1).

Hand-set: the kneel rule, the field goal at the end of a half, the late-game two-point chart, onside kicks, and the positions each kicking unit is topped up from.

The priors come from the `priors_<season>.json` files next to the code: each key from the latest season that has it and isn't after the game's (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors 2026`.
