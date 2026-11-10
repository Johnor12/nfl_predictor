# rulebook

All NFL rules that change between seasons, in one place.

API (`from shared.rulebook import ...`):
- `rules_for(season) -> Rules`: the season's rule constants (kickoff spots, touchback lines, try spots, onside rules, play clock...).

Yard lines in `Rules` are measured from the named team's own goal line (e.g. `kickoff_line=35` is the kicking team's 35).
Rule logic that never changes between seasons (downs, scoring values, penalty enforcement) lives with the scenario that uses it.
