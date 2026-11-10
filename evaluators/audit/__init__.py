# START
# audit: scores the play simulator against real plays.
# - run_audit(season=2026, weeks=None, sims=1, seed=0, predictors=None) -> Audit: input problems, invariant
#   failures, and the actual vs simulated outcome pairs.
# - metrics(audit) -> list[dict]: real vs simulated reasonableness metrics.
# - write_report(audit, path=None) -> Path: a markdown report (summary, failures, metrics table, examples).
# - CLI: `python -m evaluators.audit --season 2026 [--weeks 1-3] [--sims 1]` writes audit_output/report_<season>.md.
# END
from evaluators.audit.audit import Audit, run_audit
from evaluators.audit.report import metrics, write_report

__all__ = ["Audit", "run_audit", "write_report", "metrics"]
