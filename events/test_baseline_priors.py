# START
# Tests for the baseline priors build. Skipped unless the 2026 files are already in .cache/nflverse.
# - test_week_one_build: every event with a priors.py gets priors, with the same keys as its committed file.
# - test_on_field_priors: a season that records who was on the field (2025) adds the personnel keys, and a
#   2026 game gets them from it. Skipped unless the 2025 files are cached too.
# END
import pytest

from shared.nflverse.download import CACHE

pytestmark = pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")


def test_week_one_build():
    from events.baseline_priors import _builders, build
    from shared.priors import priors_of
    built = build(2026, weeks=[1])
    assert len(built) == 18
    for event, priors in built.items():
        assert priors and set(priors) <= set(priors_of(_builders()[event].__file__)(2026)), event


@pytest.mark.skipif(not (CACHE / "pbp_participation_2025.parquet").exists(), reason="2025 nflverse cache missing")
def test_on_field_priors():
    from events.baseline_priors import _builders, build
    from shared.priors import priors_of
    built, builders = build(2025, weeks=[1]), _builders()
    assert {"personnel", "package"} <= set(built["lineups"]) and "personnel_shotgun" in built["offensive_formation"]
    assert max(built["lineups"]["personnel"]["normal|1|7-10"], key=built["lineups"]["personnel"]["normal|1|7-10"].get) == "11"
    for event, priors in built.items():
        assert set(priors) <= set(priors_of(builders[event].__file__)(2025)), event
    assert "personnel" in priors_of(builders["lineups"].__file__)(2026)  # 2026 has none of its own
