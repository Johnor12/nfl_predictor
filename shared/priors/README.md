# priors

The toolkit behind the baseline predictors, which sample simple priors (raw counts and histograms) built from real plays. Each baseline predictor keeps its own priors files next to its code; this package is what they share.

API (`from shared.priors import ...`):

Sampling, for predictors:
- `choice(weights, rng)`: a key of a `{key: weight}` dict.
- `hist(histogram, rng) -> float`: a value from a `{"value": count}` histogram.
- `rate(counts, key) -> float`: the key's share of the counts.
- `blend(counts, fallback, k=10)`: counts backed off to a coarser distribution worth `k` samples.

Buckets, the keys priors are counted and sampled by:
- `role(player)` (`"RB1"`, `"WR3"`), `group(player)` (position group), `dist_bucket(distance)`, `field_bucket(x)`, `air_bucket(air_yards)`, `goal_bucket(yards_to_goal)`, `fg_bin(distance)`, `script(situation)` (hurry, bleed, normal).

Players on the field:
- `on_field(ctx, lineups, team)`, `pick(ctx, players, group_weights, rng, exclude=())`, `pick_many(ctx, players, group_weights, n, rng)`, `returner(ctx, players, slot, rng)`, `fouler(ctx, lineups, name, team, rng)`.

Priors files:
- `priors_of(file) -> load(season) -> dict`: a cached loader for the `priors_<season>.json` files next to `file`. It returns the latest season's file that isn't after the season asked for (the earliest if there is none).
- `save_priors(priors, file, season) -> Path`.

Building priors (used by each baseline's `priors.py` and by `events/baseline_priors.py`):
- `Sample(context, actual, row, charting)`: one real play: its `PlayContext`, `RealPlay.actual`, nflverse pbp row, and FTN charting row (or None).
- `Tally`: `tally.c[name][key] += 1` counts, `tally.hist[name].append(x)` collects values, and `tally.priors()` returns the JSON-ready dict. A name like `"unit|3|4-6|7"` nests everything after the first `|` as a sub-key.
- `present(value)`: not None and not NaN.
- `flag(sample)`: the flag on the play as `(foul name, "offense" | "defense")` in the play scenario's foul names, or None. `PRESNAP`: the fouls that belong to the pre-snap event.
- `kickoff_result(sample)`: `(zone, result)` for a kickoff that came down in the landing zone or end zone, else None.
- `nullified(sample)`: what a play wiped out by a penalty was (`run`, `pass`, `punt`, `field_goal`, `kickoff`), from its description.
