# MAINTAINER

- __init__.py: the public API (re-exports).
- sampling.py: `choice`, `hist`, `rate`, `blend`.
- buckets.py: `role`, `group`, and the situation buckets.
- players.py: `on_field`, `pick`, `pick_many`, `returner`, `fouler`, and `FOULERS` (hand-set: which positions commit each foul).
- files.py: `priors_of` (pooling the seasons before a game's, per key: `DECAY`, the rules a key is tied to, `NFL_PRIORS_THROUGH`, `NFL_PRIORS_DECAY`), `save_priors`.
- building.py: `Sample`, `Tally`, `present`, and the nflverse row readers more than one event needs (`flag` with the `FOULS` name map and `PRESNAP`, `flagrant`, `kickoff_result`, `nullified`, `timeout_case`, and the participation readers `personnel`, `package`, `played`).
- test_priors.py: `blend` ordering, `Tally`, and `priors_of`: pooling with decay, the first season of a key, the environment variables, and keys tied to rules.

Notes:
- Counts are stored raw (not normalized) so small samples stay visible; predictors normalize when sampling.
- Pooled counts are fractions (a count times a decay), and the most recent pooled season always counts 1. Predictors only ever use counts as weights, so nothing else changes; a threshold on a count (`blend`'s `k`, the lineups' 20) now means that many recent-season plays.
- The pooled dict's keys are sorted at every level, as the files' are, so sampling order doesn't depend on which seasons were pooled.
- A season in the middle of being played is pooled like any other once a later season asks for it; a game never sees its own season unless `NFL_PRIORS_THROUGH` says so.
- `priors_of` caches per season and reads the environment variables on the first load, so set it before anything is loaded (the environment reaches the evaluators' worker processes too).
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
