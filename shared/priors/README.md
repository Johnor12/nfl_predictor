# priors

The toolkit behind the baseline predictors, which sample simple priors (raw counts and histograms) built from real plays. Each baseline predictor keeps its own priors files next to its code; this package is what they share.

API (`from shared.priors import ...`):

Sampling, for predictors:
- `choice(weights, rng)`: a key of a `{key: weight}` dict.
- `hist(histogram, rng, low=None, high=None) -> float`: a value from a `{"value": count}` histogram; with bounds, one of its values in `[low, high)` (how a trained predictor fills in the yard once its model has said between which two cuts a number falls).
- `rate(counts, key) -> float`: the key's share of the counts.
- `blend(counts, fallback, k=10)`: counts backed off to a coarser distribution worth `k` samples.
- `wait(gaps, rng) -> float`: how long a team let the clock go before a snap or a timeout, from a histogram of the game seconds between two snaps (what the data records), less what the first play itself took (`PLAY_SECONDS`).

Buckets, the keys priors are counted and sampled by:
- `role(player)` (`"RB1"`, `"WR3"`), `group(player)` (position group), `dist_bucket(distance)`, `field_bucket(x)`, `air_bucket(air_yards)`, `goal_bucket(yards_to_goal)`, `fg_bin(distance)`, `script(situation)` (hurry, bleed, normal).

Players on the field:
- `on_field(ctx, lineups, team)`, `returner(ctx, players, slot, rng)`.
- `pick(ctx, players, group_weights, rng, exclude=(), own=None)`: one of the players, by position group (`{group: weight}`, usually counts from the priors). `pick_many(ctx, players, group_weights, n, rng, own=None)`: `n` different ones. `some(ctx, players, rng, happened, second, group_weights, own=None)`: nobody, one, or two, where `happened` and `second` are `{"yes": n, "no": n}` counts.
- `own`: an `Own(stats, per)` makes a pick read each player's own past. A group's weight is then split among its players on the field by how often each has done it: his `stats` (summed) per his snaps (`per`, summed), this season's plus half the earlier seasons', shrunk toward the rate of the group's players on the field. Ready-made: `TACKLES`, `PASS_RUSH` (sacks and hits), `COVERAGE` (passes defended), `FLAGS` (penalties), and from the charting `HURRIES`, `BLITZES`, `MISSES`, `TARGETED`.
- `fouler(ctx, lineups, name, team, rng, groups=None)`: who committed a foul: `groups` are the position groups it is called on (from the priors), and within a group each player's own flags.
- `usage(player, stat, got, on_play, per_snap) -> float`: how often a player gets the ball on a play he is on the field for. His depth chart role's rate (`on_play[role]`, counts of `got` or `other`), scaled by how his own past (`stat` per offensive snap: this season's, plus half the earlier seasons') compares with his role's rate per snap (`per_snap[role]`). His own rate is shrunk toward his role's, and counts as much as it once he has played `USAGE_SNAPS` snaps; with no snaps at all he is his role.

Priors files:
- `priors_of(file, rules=None, decay=None) -> load(season, week) -> dict`: a cached loader for the `priors_<season>.json` files next to `file`. A season's file holds the counts of that season's plays, week by week. `load(season, week)` pools what was played before that week: the earlier seasons, and the season's own earlier weeks (for week 6, weeks 1 to 5). Every top-level key is the sum of their counts, with a season counting `decay` times the one after it (`DECAY`, 0.5, unless given). So a game is always predicted from what was known before its week, and recent seasons count most. Games of the same week don't inform each other.
  - A key that no earlier season has comes from the whole of the first season that does: the on-field personnel starts in 2016, the charting in 2022, and each is used for the games before it too, and for every game of its own first season.
  - `rules={key: fields}` ties a key to rulebook fields (`shared.rulebook.KICKOFF`, `TRY`): it only pools the seasons played under the same rules as the game's. Kickoffs under the 2025 touchback line are predicted from 2025 on, and 2025 itself from its own games, there being nothing earlier.
- `NFL_PRIORS_DECAY=<decay>` (environment variable): another decay for every predictor, to measure it (0 is the last season alone, 1 every season equally).
- `save_priors(by_week, file, season) -> Path`: writes a season's `{week: priors}`.

Building priors (used by each baseline's `priors.py` and by `events/baseline_priors.py`):
- `Sample(context, actual, row, charting, participation)`: one real play: its `PlayContext`, `RealPlay.actual`, nflverse pbp row, FTN charting row (or None), and participation row (who was on the field; None where the season has no such data). A row is anything with the file's columns as attributes.
- `Totals`: a week's stat lines added up by position group, for what the data only counts per player and game (the charting): `totals.total(stat)`, `totals.groups(stat) -> {group: total}`. A `priors.py` reads them in `observe_totals(tally, totals)`.
- `Tally`: `tally.c[name][key] += 1` counts, `tally.hist[name].append(x)` collects values, and `tally.priors()` returns the JSON-ready dict. A name like `"unit|3|4-6|7"` nests everything after the first `|` as a sub-key.
- `present(value)`: not None and not NaN.
- `flag(sample)`: the flag on the play as `(foul name, "offense" | "defense")` in the play scenario's foul names, or None. `PRESNAP`: the fouls that belong to the pre-snap event. `flagged(sample)`: the position group of the player it was on. `flagrant(sample)`: he was disqualified.
- `personnel(sample)` (`"11"`, `"12+"`), `package(sample)` (`goal_line`, `base`, `nickel`, `dime`), `played(sample)` (`(offense ids, defense ids)`): the participation row read in the lineups event's terms, or None.
- `kickoff_result(sample)`: `(zone, result)` for a kickoff that came down in the landing zone or end zone, else None.
- `sent_out(sample)`: the unit behind a real scrimmage down (`offense`, `punt`, `field_goal`, `victory` for a kneel, None if a penalty wiped it out). A run or a pass out of a kicking formation (the description says which) was the kicking unit's: a fake.
- `timeout_case(play) -> (context, caller)`: the play's context as it stood before any timeout was called (both teams', if each called one), and who called the first (`offense`, `defense`, or `none`). `play` is a `Sample` or a `RealPlay`: only its context and `actual` are read.
- `nullified(sample)`: what a play wiped out by a penalty was (`run`, `pass`, `punt`, `field_goal`, `kickoff`), from its description.
