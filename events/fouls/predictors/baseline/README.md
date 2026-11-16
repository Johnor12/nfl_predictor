# baseline fouls predictor

At most one foul per play, at the real rate for the kind of play.

API (`from events.fouls.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, record, allowed_fouls, rng) -> tuple[Foul, ...]`

From data: flags per play by kind of play (`fouls` over `snaps`, for run, pass, punt, field_goal, kickoff), the position groups each foul is called on (`fouler`), and how often a personal foul gets the player disqualified (`flagrant`, for the fouls in `personal`).

From each player's own past: a position group's flags go to its players on the field by their own penalties per snap (`shared.priors.fouler`).

Hand-set: the foul's timing when several are possible, and its spot.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
