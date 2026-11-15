# baseline snap predictor

No longer the snap event's default: `gbm/` decides run or pass with a trained model and uses this one for everything else. `--swap snap=baseline` (or `load_predictors(snap="baseline")`) brings it back whole.

Run or pass by game script, down, and distance; the ball carrier by how often each back on the field carries when he is out there: his depth chart role's rate, moved toward his own this season.

API (`from events.snap.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, defense, allowed_actions, rng, pass_rate=pass_rate) -> Snap`
- `pass_rate(ctx, lineups, formation, defense) -> float`: how often the offense drops back here. Another implementation hands `predict` its own and keeps everything else (`gbm/` does).

From data: pass rate by game script, down, and distance (`pass_rate`), the two-point play mix (`two_point_play`), and how often a player on the field for a designed run carries it, by depth chart role (`carry_rate`, from seasons whose data records who was on the field). A player's own season scales his role's rate (`shared.priors.usage`): his designed carries per offensive snap (`Player.stats`) against his role's (`carries_per_snap`), so a second back who has been getting the carries gets them, and a quarterback who runs keeps running. Before he has played, he is his role.

Hand-set: the bad snap rate, kneels from the victory formation, and spikes late in a half with no timeouts. Punt and field goal units always kick (no fakes).

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
