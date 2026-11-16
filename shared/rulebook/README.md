# rulebook

All NFL rules that change between seasons, in one place.

API (`from shared.rulebook import ...`):
- `rules_for(season) -> Rules`: the season's rule constants (kickoff spots, touchback lines, try spots, onside rules, play clock, overtime format and length, how a third coach's challenge is earned...).
- `same_rules(season, other, fields) -> bool`: the two seasons agree on those `Rules` fields. `KICKOFF` and `TRY` are the fields that change how kickoffs and tries are played; the baseline priors use them to keep kickoff and try counts from being pooled across a rule change.

Seasons: 2011 on (`rules_for` raises before that).

Yard lines in `Rules` are measured from the named team's own goal line (e.g. `kickoff_line=35` is the kicking team's 35).
Rule logic that never changes between seasons (downs, scoring values, penalty enforcement) lives with the scenario that uses it.
