# MAINTAINER

- __init__.py: exports `Rules`, `rules_for`, `same_rules`, `KICKOFF`, `TRY`.
- rules.py: the `Rules` dataclass (defaults are the current season's rules), `rules_for`, which applies older-season overrides, and `same_rules` with the field groups `KICKOFF` and `TRY`.
- test_rules.py: spot checks of rule changes, and `same_rules`.

Notes:
- Overtime's format and length are here because they changed by season (2012, 2017, 2022, 2025). How a format plays out is the game scenario's (`scenarios/game/overtime.py`).
- A rule change that alters how an event plays out needs its fields in a group like `KICKOFF`, and the priors keys it affects tied to the group where the predictor calls `priors_of`. Otherwise counts from before the change are pooled with the ones after it.
- `kickoff_fair_catch_line` (2023's fair catch rule) isn't in `KICKOFF`: 2023 would have no earlier season to learn kickoffs from. Its fair catches (about 3% of kickoffs) are predicted at the earlier seasons' rate, next to none.
