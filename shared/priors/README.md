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
- `priors_of(file, rules=None, decay=None) -> load(season, week) -> dict`: a cached loader for the `priors_<season>.json` files next to `file`. A season's file holds the counts of that season's plays, week by week. `load(season, week)` pools what was played before that week: the earlier seasons, and the season's own earlier weeks (for week 6, weeks 1 to 5). Every top-level key is the sum of their counts, with a season counting `decay` times the one after it (`DECAY`, 0.5, unless given). So a game is always predicted from what was known before its week, and recent seasons count most. Games of the same week don't inform each other.
  - A key that no earlier season has comes from the whole of the first season that does: the on-field personnel starts in 2016, the charting in 2022, and each is used for the games before it too, and for every game of its own first season.
  - `rules={key: fields}` ties a key to rulebook fields (`shared.rulebook.KICKOFF`, `TRY`): it only pools the seasons played under the same rules as the game's. Kickoffs under the 2025 touchback line are predicted from 2025 on, and 2025 itself from its own games, there being nothing earlier.
- `NFL_PRIORS_DECAY=<decay>` (environment variable): another decay for every predictor, to measure it (0 is the last season alone, 1 every season equally).
- `save_priors(by_week, file, season) -> Path`: writes a season's `{week: priors}`.

Building priors (used by each baseline's `priors.py` and by `events/baseline_priors.py`):
- `Sample(context, actual, row, charting, participation)`: one real play: its `PlayContext`, `RealPlay.actual`, nflverse pbp row, FTN charting row (or None), and participation row (who was on the field; None where the season has no such data). A row is anything with the file's columns as attributes.
- `Tally`: `tally.c[name][key] += 1` counts, `tally.hist[name].append(x)` collects values, and `tally.priors()` returns the JSON-ready dict. A name like `"unit|3|4-6|7"` nests everything after the first `|` as a sub-key.
- `present(value)`: not None and not NaN.
- `flag(sample)`: the flag on the play as `(foul name, "offense" | "defense")` in the play scenario's foul names, or None. `PRESNAP`: the fouls that belong to the pre-snap event. `flagrant(sample)`: the flagged player was disqualified.
- `personnel(sample)` (`"11"`, `"12+"`), `package(sample)` (`goal_line`, `base`, `nickel`, `dime`), `played(sample)` (`(offense ids, defense ids)`): the participation row read in the lineups event's terms, or None.
- `kickoff_result(sample)`: `(zone, result)` for a kickoff that came down in the landing zone or end zone, else None.
- `timeout_case(play) -> (context, caller)`: the play's context as it stood before any timeout was called, and who called one (`offense`, `defense`, or `none`). `play` is a `Sample` or a `RealPlay`: only its context and `actual` are read.
- `nullified(sample)`: what a play wiped out by a penalty was (`run`, `pass`, `punt`, `field_goal`, `kickoff`), from its description.
