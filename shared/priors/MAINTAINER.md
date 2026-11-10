# MAINTAINER

- __init__.py: the public API (re-exports).
- sampling.py: `choice`, `hist`, `rate`, `blend`.
- buckets.py: `role`, `group`, and the situation buckets.
- players.py: `on_field`, `pick`, `pick_many`, `returner`, `fouler`, and `FOULERS` (hand-set: which positions commit each foul).
- files.py: `priors_of`, `save_priors`.
- building.py: `Sample`, `Tally`, `present`, and the nflverse row readers more than one event needs (`flag` with the `FOULS` name map and `PRESNAP`, `kickoff_result`).
- test_priors.py: `blend` ordering, `Tally`, and season selection in `priors_of`.

Notes:
- Counts are stored raw (not normalized) so small samples stay visible; predictors normalize when sampling.
- `blend` sorts its keys. Sampling from a dict built in set order made plays differ between processes with the same seed.
- This package imports nothing from the rest of the project. `building.py` reads nflverse column names but doesn't import `shared.nflverse` or pandas.
- A reader belongs in `building.py` only when two events' `priors.py` need the same interpretation of a row; otherwise it stays in the event's `priors.py`.
