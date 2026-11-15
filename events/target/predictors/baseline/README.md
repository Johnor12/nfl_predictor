# baseline target predictor

The receiver by how often each eligible player is thrown to when he is on the field (his depth chart role's rate, moved toward his own this season); air yards by his position group; direction from the priors.

API (`from events.target.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, eligible, rng) -> Target`

From data: how often a back, receiver, or tight end on the field is the target, by depth chart role (`target_rate`, from seasons whose data records who was on the field), air yards by the receiver's position group (`air_yards`: a back's passes are thrown about 10 yards shorter than a receiver's; `air_yards_goal` inside the 10), and direction (`direction`). A player's own season scales his role's rate (`shared.priors.usage`): his targets per offensive snap (`Player.stats`) against his role's (`targets_per_snap`). Before he has played, he is his role.

Hand-set: nothing.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
