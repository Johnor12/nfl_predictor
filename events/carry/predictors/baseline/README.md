# baseline carry predictor

Yards from a histogram for the kind of carry (runs by the carrier's position group, catches by pass depth and the receiver's), how it ended, and who made the tackle: by position group and each defender's own tackles.

API (`from events.carry.predictors.baseline import predict`, or `play.load_predictors("baseline")`):

- `predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd`

From data: yardage histograms by kind (`run` by the carrier's position group; `catch`, the yards after it, by pass depth (behind the line, short, medium, deep) and the receiver's position group; `scramble`, `interception`, `punt_return`, `kick_return`; `run_goal` and `catch_goal` inside the 10), how carries end (`carry_end`), how often a run or a catch ends in a lateral (`lateral`), and the tackle as the box score credits it, by the kind of carry: whether anybody is credited, by how the carry ended (`credited`: nearly always, out of bounds too), whether it is one tackle or two assists (`shared`), and the tacklers' position groups for each (`tackler`: a catch's lone tackler is a defensive back 70% of the time, a run's shared one a lineman a third of the time).

From each defender's own past: on a run, a scramble, or a catch, a position group's tackles go to its players on the field by their own tackles and assists per snap on defense, this season and earlier ones (`shared.priors.TACKLES`; `shared/priors/README.md` has how).

From the charting (2018 on, counted per game, so these are league rates): whether the carrier broke a tackle (`broken`, for runs and catches), whether a defender missed one (`missed`) and his position group (`misser`), picked by his own missed tackles, and the share of a run's yards that came after contact (`after_contact`).

Hand-set: kneels, fumble recovery returns, how returns without data end and who is credited on them, slides on scrambles, forced fumble credit, who takes a lateral (a back, receiver, or tight end on the field), how a run's yards after contact vary around the league's share, and the carry's duration (set so that a run and a completion take about the 6 seconds real ones do, a scramble 8).

The priors come from the `priors_<season>.json` files next to the code: a game is predicted from the counts of what was played before it (the earlier seasons and its own season's earlier weeks), older seasons counting less (see `shared/priors/README.md`). `kick_return` only pools the seasons played under the game's kickoff rules (`shared.rulebook.KICKOFF`). Rebuild every event's with `python -m events.baseline_priors` (`2026` for one season).
