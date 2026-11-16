# baseline pass rush predictor

The dropback's result, rushers, sack yardage, and quarterback hits from the priors.

API (`from events.pass_rush.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, formation, defense, rng) -> PassRush`

From data: the result mix (`dropback`: throw, sack, or scramble; the quarterback's own sack and scramble rates this season, from `Player.stats`, count as much as the league's once he has dropped back 150 times), how often a throw is thrown away (`throwaway`) and the rushers (`rushers`), both from the charting, which starts in 2022, sack yardage (`sack_yards`), the strip-sack rate (`strip_sack`), sackers by position group (`sacker`), how often two of them split a sack (`shared_sack`), and the quarterback hit rate (`qb_hit`).

From each defender's own past: a position group's sacks and hits go to its players on the field by their own sacks and hits per snap on defense (`shared.priors.PASS_RUSH`).

From Pro Football Reference's charting (2018 on, counted per game, so these are league rates): how often a dropback is blitzed (`blitzed`) and a throw without a hit is hurried (`hurried`), whether a second defender had a part (`second_blitzer`, `second_hurrier`), and their position groups (`blitzer`, `hurrier`), each picked by his own blitzes or hurries.

Hand-set: time to throw, scramble, or throw away, how long a sack takes, and how fast a quarterback's own season takes over (`DROPBACKS`).

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
