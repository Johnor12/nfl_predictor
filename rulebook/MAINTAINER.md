# MAINTAINER

- __init__.py: exports `Rules`, `rules_for`.
- rules.py: the `Rules` dataclass (defaults are the current season's rules) and `rules_for`, which applies older-season overrides.
- test_rules.py: spot checks of rule changes.
