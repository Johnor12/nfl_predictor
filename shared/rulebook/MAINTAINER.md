# MAINTAINER

- __init__.py: exports `Rules`, `rules_for`.
- rules.py: the `Rules` dataclass (defaults are the current season's rules) and `rules_for`, which applies older-season overrides.
- test_rules.py: spot checks of rule changes.

Notes:
- Overtime's format and length are here because they changed by season (2012, 2017, 2022, 2025). How a format plays out is the game scenario's (`scenarios/game/overtime.py`).
