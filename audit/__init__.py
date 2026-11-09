# START
# audit: runs real play contexts through the play scenario and checks the results.
# - run_audit(season, weeks=None, sims=1, seed=0) -> Audit: input problems, invariant failures, and the
#   actual vs simulated outcome pairs.
# - write_report(audit, path) -> Path: a markdown report (summary, failures, reasonableness table, examples).
# - CLI: `python -m audit --season 2026 [--weeks 1-3] [--sims 1]` writes audit_output/report_<season>.md.
# END
from audit.audit import Audit, run_audit
from audit.report import metrics, write_report

__all__ = ["Audit", "run_audit", "write_report", "metrics"]
