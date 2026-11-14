# MAINTAINER

- __init__.py: the public API (re-exports).
- sampling.py: `choice`, `hist`, `rate`, `blend`.
- buckets.py: `role`, `group`, and the situation buckets.
- players.py: `on_field`, `pick`, `pick_many`, `returner`, `fouler`, and `FOULERS` (hand-set: which positions commit each foul).
- files.py: `priors_of` (the per-key merge across seasons, and `NFL_PRIORS_THROUGH`), `save_priors`.
- building.py: `Sample`, `Tally`, `present`, and the nflverse row readers more than one event needs (`flag` with the `FOULS` name map and `PRESNAP`, `flagrant`, `kickoff_result`, `nullified`, `timeout_case`, and the participation readers `personnel`, `package`, `played`).
- test_priors.py: `blend` ordering, `Tally`, and season selection in `priors_of` (per key, and capped by `NFL_PRIORS_THROUGH`).

Notes:
- Counts are stored raw (not normalized) so small samples stay visible; predictors normalize when sampling.
- The merge across seasons is by top-level key only: a key in a later season's file replaces the earlier season's whole, however thin it is. Pooling seasons would be a change to `priors_of`.
- `priors_of` caches per season and reads `NFL_PRIORS_THROUGH` on the first load, so set it before anything is loaded (the environment reaches the evaluators' worker processes too).
- `FOULS` maps an nflverse foul the play scenario doesn't have to the one enforced the same way (a pair picks by side). A foul it doesn't list is dropped from every priors count.
- `blend` sorts its keys. Sampling from a dict built in set order made plays differ between processes with the same seed.
- This package imports nothing from the rest of the project. `building.py` reads nflverse column names but doesn't import `shared.nflverse` or pandas.
- A reader belongs in `building.py` only when more than one user (two events' `priors.py`, or one and an evaluator) needs the same interpretation of a row; otherwise it stays in the event's `priors.py`.
