# START
# Tests for the baseline priors build. Skipped unless the 2026 files are already in .cache/nflverse.
# - test_week_one_build: every event with a priors.py gets priors, with the same keys as its committed file.
# END
import pytest

from shared.nflverse.download import CACHE

pytestmark = pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")


def test_week_one_build():
    from events.baseline_priors import _builders, build
    from shared.priors import priors_of
    built = build(2026, weeks=[1])
    assert len(built) == 17
    for event, priors in built.items():
        assert priors and set(priors) <= set(priors_of(_builders()[event].__file__)(2026)), event
