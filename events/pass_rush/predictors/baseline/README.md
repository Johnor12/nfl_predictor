# baseline pass rush predictor

The dropback's result, rushers, sack yardage, and quarterback hits from the priors.

API (`from events.pass_rush.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, defense, rng) -> PassRush`

From data: the result mix (`dropback`: throw, sack, or scramble), how often a throw is thrown away (`throwaway`) and the rushers (`rushers`), both from the charting, which starts in 2022, sack yardage (`sack_yards`), the strip-sack rate (`strip_sack`), sackers by position group (`sacker`), and the quarterback hit rate (`qb_hit`).

Hand-set: time to throw, sack, scramble, or throw away, and the split-sack rate.

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of the seasons before its own, older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
