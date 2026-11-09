# START
# Tests for real play contexts. Skipped unless the 2026 files are already in .cache/nflverse (no downloads in tests).
# - test_week_one_contexts_are_valid: every real input passes validate_context.
# - test_conventions: kickoffs are from the kicking team's side; tries use the two-point spot; clock inference.
# END
import pytest

from nflverse.download import CACHE
from scenarios.play import validate_context

pytestmark = pytest.mark.skipif(not (CACHE / "play_by_play_2026.parquet").exists(), reason="nflverse cache missing")


@pytest.fixture(scope="module")
def plays():
    from nflverse import real_plays
    return real_plays(2026, weeks=[1])


def test_week_one_contexts_are_valid(plays):
    assert len(plays) > 2000
    assert [(p.context.game.game_id, e) for p in plays for e in validate_context(p.context)] == []


def test_conventions(plays):
    opening = plays[0].context.situation
    assert opening.kind == "kickoff" and opening.x == 35 and opening.quarter == 1 and opening.clock == 900
    assert not opening.clock_running
    tries = [p.context.situation for p in plays if p.context.situation.kind == "try"]
    assert all(80 <= s.x <= 99 and s.down is None for s in tries)  # behind the 2 after a penalty on the try
    assert sum(s.x == 98 for s in tries) > 0.9 * len(tries)
    after_kickoff = plays[1].context.situation
    assert after_kickoff.kind == "scrimmage" and not after_kickoff.clock_running
    assert all(len(p.context.history) == i for i, p in enumerate(plays[:50]))
