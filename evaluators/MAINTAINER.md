# MAINTAINER

- __init__.py: `parse_weeks`, shared by the CLIs.
- scoring/: the scoring toolkit (see its MAINTAINER.md). Imports nothing from the rest of the project.
- play/: the play and event evaluator (see its MAINTAINER.md).
- lines/: the betting lines evaluator (see its MAINTAINER.md).
- audit/: the play audit (see its MAINTAINER.md).

Notes:
- A new evaluator scores with `scoring.Scorecard` (`add(name, samples, actual)` per case) and reports with `scoring.score_table` and friends, so every level of the system is measured the same way.
- The audit and the play evaluator answer different questions. The audit compares overall rates (is the simulator reasonable on average?) and checks every play is valid. The play evaluator scores each play's forecast distribution (is it right about this play?).
