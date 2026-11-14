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
- `priors_of(file) -> load(season) -> dict`: a cached loader for the `priors_<season>.json` files next to `file`. Each top-level key comes from the latest season's file that has it and isn't after the season asked for (the earliest file if all are later). A season's file only holds what that season's data can say, so a predictor gets everything any season so far has recorded: 2026 has no on-field personnel yet, and a 2026 game gets 2025's.
- `NFL_PRIORS_THROUGH=<season>` (environment variable): ignore the files of later seasons. `NFL_PRIORS_THROUGH=2025` scores 2026's plays with priors that have never seen them.
- `save_priors(priors, file, season) -> Path`.

Building priors (used by each baseline's `priors.py` and by `events/baseline_priors.py`):
- `Sample(context, actual, row, charting, participation)`: one real play: its `PlayContext`, `RealPlay.actual`, nflverse pbp row, FTN charting row (or None), and participation row (who was on the field; None where the season has no such data).
- `Tally`: `tally.c[name][key] += 1` counts, `tally.hist[name].append(x)` collects values, and `tally.priors()` returns the JSON-ready dict. A name like `"unit|3|4-6|7"` nests everything after the first `|` as a sub-key.
- `present(value)`: not None and not NaN.
- `flag(sample)`: the flag on the play as `(foul name, "offense" | "defense")` in the play scenario's foul names, or None. `PRESNAP`: the fouls that belong to the pre-snap event. `flagrant(sample)`: the flagged player was disqualified.
- `personnel(sample)` (`"11"`, `"12+"`), `package(sample)` (`goal_line`, `base`, `nickel`, `dime`), `played(sample)` (`(offense ids, defense ids)`): the participation row read in the lineups event's terms, or None.
- `kickoff_result(sample)`: `(zone, result)` for a kickoff that came down in the landing zone or end zone, else None.
- `timeout_case(sample) -> (context, caller)`: the play's context as it stood before any timeout was called, and who called one (`offense`, `defense`, or `none`).
- `nullified(sample)`: what a play wiped out by a penalty was (`run`, `pass`, `punt`, `field_goal`, `kickoff`), from its description.
