# START
# Tests for the priors toolkit.
# - test_blend_is_ordered: sampling a blend can't depend on set order (plays must be reproducible).
# - test_tally: counts, nested sub-keys, and histograms.
# - test_priors_pool_the_seasons_before: a game's priors are the earlier seasons' counts, older ones
#   discounted; a key no earlier season has comes from the first that does; NFL_PRIORS_THROUGH and
#   NFL_PRIORS_DECAY override.
# - test_priors_stay_within_a_rule: a key tied to rulebook fields only pools the seasons with the same rules.
# END
import random

from shared.priors import Tally, blend, choice, priors_of, save_priors
from shared.rulebook import KICKOFF


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


def test_priors_pool_the_seasons_before(tmp_path, monkeypatch):
    monkeypatch.delenv("NFL_PRIORS_THROUGH", raising=False)
    monkeypatch.delenv("NFL_PRIORS_DECAY", raising=False)
    file = tmp_path / "predictor.py"
    save_priors({"run": {"3": 10, "4": 2}}, file, 2022)
    save_priors({"run": {"3": 20}, "personnel": {"11": 7}}, file, 2023)  # only 2023's data can say the personnel
    save_priors({"run": {"3": 40}}, file, 2024)
    load = priors_of(file, decay=0.5)
    assert load(2024) == {"run": {"3": 25.0, "4": 1.0}, "personnel": {"11": 7.0}}  # 2023, and half of 2022
    assert load(2025)["run"] == {"3": 52.5, "4": 0.5} and load(2030) == load(2025)
    assert load(2023) == {"run": {"3": 10.0, "4": 2.0}, "personnel": {"11": 7.0}}  # personnel: the first season with it
    assert load(2022)["run"] == {"3": 10.0, "4": 2.0}  # nothing earlier: the first season
    assert priors_of(file, decay=1)(2025)["run"] == {"3": 70, "4": 2}
    monkeypatch.setenv("NFL_PRIORS_THROUGH", "2024")
    assert priors_of(file, decay=0.5)(2024)["run"]["3"] == 52.5  # this season's games too
    monkeypatch.setenv("NFL_PRIORS_DECAY", "0")
    assert priors_of(file, decay=0.5)(2024)["run"] == {"3": 40.0, "4": 0.0}


def test_priors_stay_within_a_rule(tmp_path, monkeypatch):
    monkeypatch.delenv("NFL_PRIORS_THROUGH", raising=False)
    file = tmp_path / "predictor.py"
    for season in (2022, 2023, 2024, 2025):
        save_priors({"kickoff": {str(season): 1}, "punt": {str(season): 1}}, file, season)
    load = priors_of(file, rules={"kickoff": KICKOFF}, decay=1)
    assert load(2026) == {"kickoff": {"2025": 1}, "punt": {"2022": 1, "2023": 1, "2024": 1, "2025": 1}}
    assert load(2023)["kickoff"] == {"2022": 1}
    assert load(2024)["kickoff"] == {"2024": 1} and load(2025)["kickoff"] == {"2025": 1}  # each the first season of a rule
