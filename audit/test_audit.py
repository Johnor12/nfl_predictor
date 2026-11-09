# START
# Tests for the audit. Skipped unless the 2026 files are already in .cache/nflverse.
# - test_week_one_audit: every real week 1 input is valid, every simulated play passes the validator,
#   and the report is written.
# END
import pytest

from nflverse.download import CACHE

pytestmark = pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")


def test_week_one_audit(tmp_path):
    from audit import metrics, run_audit, write_report
    audit = run_audit(2026, weeks=[1])
    assert audit.input_errors == [] and audit.failures == []
    assert len(audit.simulated) == len(audit.plays)
    assert len(metrics(audit)) > 30
    assert write_report(audit, tmp_path / "report.md").exists()
