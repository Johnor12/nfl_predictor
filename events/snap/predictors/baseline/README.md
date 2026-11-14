# baseline snap predictor

Run or pass by game script, down, and distance; the ball carrier by how often each back on the field carries when he is out there.

API (`from events.snap.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, defense, allowed_actions, rng) -> Snap`

From data: pass rate by game script, down, and distance (`pass_rate`), the two-point play mix (`two_point_play`), and how often a player on the field for a designed run carries it, by depth chart role (`carry_rate`, from seasons whose data records who was on the field).

Hand-set: the bad snap rate, kneels from the victory formation, and spikes late in a half with no timeouts. Punt and field goal units always kick (no fakes).

The priors come from the `priors_<season>.json` files next to the code: each key from the latest season that has it and isn't after the game's (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors 2026`.
