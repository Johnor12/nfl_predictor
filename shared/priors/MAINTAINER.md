# MAINTAINER

- __init__.py: the public API (re-exports).
- sampling.py: `choice`, `hist`, `rate`, `blend`.
- buckets.py: `role`, `group`, and the situation buckets.
- players.py: `on_field`, `pick`, `pick_many`, `returner`, `fouler`, and `FOULERS` (hand-set: which positions commit each foul).
- files.py: `priors_of` (pooling what was played before a game, per key: the earlier seasons and its own season's earlier weeks, `DECAY`, the rules a key is tied to, `NFL_PRIORS_DECAY`), `save_priors`.
- building.py: `Sample`, `Tally`, `present`, and the nflverse row readers more than one event needs (`flag` with the `FOULS` name map and `PRESNAP`, `flagrant`, `kickoff_result`, `nullified`, `timeout_case`, and the participation readers `personnel`, `package`, `played`).
- test_priors.py: `blend` ordering, `Tally`, and `priors_of`: pooling with decay, the season's earlier weeks, the first season of a key, the environment variable, and keys tied to rules.

Notes:
- Counts are stored raw (not normalized) so small samples stay visible; predictors normalize when sampling.
- Pooled counts are fractions (a count times a decay), and the most recent pooled season always counts 1. Predictors only ever use counts as weights, so nothing else changes; a threshold on a count (`blend`'s `k`, the lineups' 20) now means that many recent-season plays.
- The pooled dict's keys are sorted at every level, as the files' are, so sampling order doesn't depend on which seasons were pooled.
- A game's own season is pooled like any other season, cut off before the game's week: it counts 1 and the seasons before it `decay` each, as soon as it has a week with the key. A week's games never see each other (a Thursday game doesn't inform Sunday's), and a week is whatever nflverse numbers it, the playoffs running on from the regular season.
- The first season of a rule or of a data source is the one place a game sees plays that came after it (and its own): a few weeks of a new kickoff don't fill every key a predictor reads, so the whole season stands in. The season after it is walked forward like any other.
- A week is one line of a season's file, so a weekly rebuild during the season adds a line.
- The season's earlier weeks were measured, on the play evaluator's rows for 96 games of 2021-2026 at 30 sims, compared case by case with the earlier seasons alone: 5 of 39 outputs better by more than 2 standard errors, none worse. The gains are where the league moves from one season to the next: kickoffs (the play's touchback -2.5% and return yards -1.5%, the kick result -1.5%), the fourth-down unit -1.5%, shotgun -0.5%. The rest are within noise, a season of plays having already pinned those rates down.
- `priors_of` caches per season and week and reads the environment variable on the first load, so set it before anything is loaded (the environment reaches the evaluators' worker processes too).
- `FOULS` maps an nflverse foul the play scenario doesn't have to the one enforced the same way (a pair picks by side). A foul it doesn't list is dropped from every priors count.
- `blend` sorts its keys. Sampling from a dict built in set order made plays differ between processes with the same seed.
- This package imports only `shared.rulebook` (for the rules a key is tied to) from the rest of the project. `building.py` reads nflverse column names but doesn't import `shared.nflverse` or pandas.
- A reader belongs in `building.py` only when more than one user (two events' `priors.py`, or one and an evaluator) needs the same interpretation of a row; otherwise it stays in the event's `priors.py`.
- Personnel strings in the participation files aren't clean before 2023 (`1 RB, 2 TE, 1 WR,1 DL`, or empty), so `_positions` picks out the count and position pairs instead of splitting on the separator. A group that doesn't add up to 11 is unusable and read as None.
- `DECAY` was measured, on the play evaluator's event rows for 64 games of 2021-2026 at 30 sims, each game predicted from the seasons before it, compared case by case with the last season alone (0):
  - 0.5 and 0.8 are within noise of it on nearly every output. One season of plays already pins a league-wide rate down, so older seasons have little to add.
  - 1 (every season equally) is worse where the league has drifted: the fourth-down unit +7.6% (3 standard errors), punt distance +2.7%, the kickoff result +1.3%. 0.8 shows the same on the fourth-down unit (+2.8%).
  - The thin counts lean the other way without reaching 2 standard errors: interception returns -4% to -6%, field goals by distance -1.5% to -3%.
  - 0.5 keeps most of the weight on the last two seasons and still gives a thin key a few seasons to draw on. A predictor that wants another weight passes `decay=` to `priors_of`; none does yet.
