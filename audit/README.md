# audit

Checks the play scenario against real plays: every real input is run through `run_play` with the baseline predictors, validated, and compared with what actually happened.

API (`from audit import ...`):

- `run_audit(season=2026, weeks=None, sims=1, seed=0) -> Audit`: input problems (`validate_context`), simulated plays that broke an invariant or raised, and real/simulated outcome pairs.
- `metrics(audit) -> list[dict]`: real vs simulated reasonableness metrics (play calling, 4th downs, tries, yardage, turnovers, red zone, penalties, kicking, scoring, clock), each flagged when outside tolerance.
- `write_report(audit, path=None)`: markdown report at `audit_output/report_<season>.md` (gitignored), with example plays narrated next to the real play.
- CLI: `python -m audit --season 2026 [--weeks 1-3] [--sims 1]`.

A metric compares one simulated play per real input against the real outcome, aggregated over all inputs. It measures whether the predictors are reasonable, not whether they're calibrated. Calibration belongs to the evaluator (phase 1).
