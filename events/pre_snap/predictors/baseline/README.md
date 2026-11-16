# baseline pre snap predictor

Play clock used by game script, from the real time between snaps, and pre-snap fouls at the real rate.

API (`from events.pre_snap.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, allowed_fouls, rng) -> PreSnap`

From data: pre-snap foul rates per snap (`fouls` over `snaps`), the position groups each foul is called on (`fouler`; within a group, by each player's own penalties per snap), and the play clock used on a full play clock with the game clock running: a real gap between two snaps for the game script (`snap_gap`: hurry, bleed, or normal), less what the first play itself took (`shared.priors.wait`).

Hand-set: play clock usage after an administrative stoppage (the 25-second clock).

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
