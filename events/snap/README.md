# snap event

The snap itself (clean, or bad, which becomes a loose ball) and what the offense does with it: a handoff (to whom), a dropback pass, a kneel, a spike, a punt, a field goal or extra point kick, or a fake out of a special teams formation.

Predictor: `predict(ctx, lineups, formation, defense, allowed_actions, rng) -> Snap`

Inputs (besides the [common ones](../README.md)):

- `formation` / `defense`: the offense's `Formation` and the `DefensiveFormation`.
- `allowed_actions`: what the unit on the field can run (offense: run, pass, kneel, spike; victory: kneel; punt: punt, run, pass; field_goal: field_goal, run, pass; no field_goal without a kicker on the field).

Output (`from events.snap import ...`):

- `Snap(action, ball_to, bad_snap)`: the action, the ball carrier on a run, and whether the snap was bad.

The play scenario raises `IllegalChoice` unless the action is one of `allowed_actions`, and a handoff goes to a player in the backfield.

Implementations are in [predictors/](predictors/README.md).
