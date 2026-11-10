# audit

Checks the play simulator against real plays: every real input is validated, simulated, and compared with what actually happened.

API (`from evaluators.audit import ...`):

- `run_audit(season=2026, weeks=None, sims=1, seed=0, predictors=None) -> Audit`: input problems (`validate_context`), simulated plays that broke an invariant or raised, and real/simulated outcome pairs. `predictors` is a `play.Predictors` (the baseline set if omitted), so a swapped-in predictor can be audited: `run_audit(predictors=load_predictors("baseline", carry="other"))`.
- `metrics(audit) -> list[dict]`: real vs simulated reasonableness metrics (play calling, 4th downs, tries, yardage, turnovers, red zone, penalties, kicking, scoring, clock), each flagged when outside tolerance.
- `write_report(audit, path=None)`: markdown report at `audit_output/report_<season>.md` (gitignored), with example plays narrated next to the real play.
- CLI: `python -m evaluators.audit --season 2026 [--weeks 1-3] [--sims 1]`.

A metric compares one simulated play per real input against the real outcome, aggregated over all inputs. It measures whether the predictors are reasonable on average. Scoring each play's forecast (and calibration) is `evaluators/play`'s job.
