# baseline snap predictor

Run or pass by game script, down, and distance; the ball carrier by depth chart role.

API (`from events.snap.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, defense, allowed_actions, rng) -> Snap`

From data: pass rate by game script, down, and distance (`pass_rate`), the two-point play mix (`two_point_play`), and designed-run carriers by role (`run_carrier`).

Hand-set: the bad snap rate, kneels from the victory formation, and spikes late in a half with no timeouts. Punt and field goal units always kick (no fakes).

The priors come from the `priors_<season>.json` for the game's season (the latest earlier one if it has none). Rebuild every event's with `python -m events.baseline_priors 2026`.
