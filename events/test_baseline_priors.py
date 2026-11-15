# START
# Tests for the baseline priors build. Skipped unless the 2026 files are already in .cache/nflverse.
# - test_week_one_build: every event with a priors.py gets priors, with the same keys as its committed file.
# - test_on_field_priors: a season that records who was on the field (2025) adds the personnel keys, and a
#   2026 game gets them from it. Skipped unless the 2025 files are cached too.
# - test_old_season_build: a season in the older data formats (2016) builds the same keys, the personnel
#   ones included. Skipped unless the 2016 files are cached.
# END
import pytest

from shared.nflverse.download import CACHE

pytestmark = pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")


def test_week_one_build():
    from events.baseline_priors import _builders, build
    from shared.priors import priors_of
    built = {event: by_week[1] for event, by_week in build(2026, weeks=[1]).items()}
    assert len(built) == 18
    for event, priors in built.items():
        assert priors and set(priors) <= set(priors_of(_builders()[event].__file__)(2026, 1)), event


@pytest.mark.skipif(not (CACHE / "pbp_participation_2025.parquet").exists(), reason="2025 nflverse cache missing")
def test_on_field_priors():
    from events.baseline_priors import _builders, build
    from shared.priors import priors_of
    built, builders = {event: by_week[1] for event, by_week in build(2025, weeks=[1]).items()}, _builders()
    assert {"personnel", "package"} <= set(built["lineups"]) and "personnel_shotgun" in built["offensive_formation"]
    assert max(built["lineups"]["personnel"]["normal|1|7-10"], key=built["lineups"]["personnel"]["normal|1|7-10"].get) == "11"
    for event, priors in built.items():
        assert set(priors) <= set(priors_of(builders[event].__file__)(2025, 1)), event
    assert "personnel" in priors_of(builders["lineups"].__file__)(2026, 9)  # 2026 has none of its own


@pytest.mark.skipif(not (CACHE / "pbp_participation_2016.parquet").exists(), reason="2016 nflverse cache missing")
def test_old_season_build():
    from events.baseline_priors import build
    built = {event: by_week.get(1, {}) for event, by_week in build(2016, weeks=[1]).items()}
    assert len(built) == 18 and not built["defensive_formation"]  # no charting before 2022
    assert {"personnel", "package", "unit", "two_point"} <= set(built["lineups"])
    assert {"carry_rate", "pass_rate"} <= set(built["snap"]) and "target_rate" in built["target"]
    assert max(built["lineups"]["package"]["11"], key=built["lineups"]["package"]["11"].get) == "nickel"
