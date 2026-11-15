# MAINTAINER

- __init__.py: package marker.
- rulebook/: season-versioned rule constants (see its MAINTAINER.md).
- priors/: the baseline predictors' toolkit (see its MAINTAINER.md).
- models/: the trained predictors' toolkit (see its MAINTAINER.md).
- nflverse/: the nflverse data source (see its MAINTAINER.md).
- lines/: betting lines (see its MAINTAINER.md).

Dependencies:
- rulebook/, priors/, and models/ import nothing from events/, scenarios/, simulators/, or evaluators/.
- nflverse/ is the one exception: it builds `PlayContext`s and `GameContext`s, so it imports `scenarios.play` and `scenarios.game` (and `shared.rulebook`, `shared.priors`). The scenarios must never import it back.
- lines/ imports `shared.nflverse` (the schedule, and rosters to map ESPN's player ids).
