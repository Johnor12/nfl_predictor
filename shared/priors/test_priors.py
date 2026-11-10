# START
# Tests for the priors toolkit.
# - test_blend_is_ordered: sampling a blend can't depend on set order (plays must be reproducible).
# - test_tally: counts, nested sub-keys, and histograms.
# - test_priors_of_picks_the_season: the latest file not after the season, else the earliest.
# END
import random

from shared.priors import Tally, blend, choice, priors_of, save_priors


def test_blend_is_ordered():
    blended = blend({"punt": 3, "offense": 1}, {"field_goal": 5, "offense": 5})
    assert list(blended) == ["field_goal", "offense", "punt"]
    assert blended == {"field_goal": 5.0, "offense": 6.0, "punt": 3.0}
    assert choice(blended, random.Random(0)) in blended


def test_tally():
    tally = Tally()
    tally.c["unit|4|1|5"]["punt"] += 2
    tally.c["snaps"]["n"] += 1
    tally.hist["yards"] += [3.4, 2.6, float("nan"), 500]
    tally.hist["yards_goal|1-2"].append(1)
    assert tally.priors() == {"unit": {"4|1|5": {"punt": 2}}, "snaps": {"n": 1}, "yards": {"3": 2, "110": 1},
                              "yards_goal": {"1-2": {"1": 1}}}


def test_priors_of_picks_the_season(tmp_path):
    file = tmp_path / "predictor.py"
    for season in (2024, 2026):
        save_priors({"season": season}, file, season)
    load = priors_of(file)
    assert [load(s)["season"] for s in (2023, 2024, 2025, 2026, 2030)] == [2024, 2024, 2024, 2026, 2026]
