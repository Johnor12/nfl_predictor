# START
# Tests for the priors toolkit.
# - test_blend_is_ordered: sampling a blend can't depend on set order (plays must be reproducible).
# - test_hist_within_bounds: a draw between two bounds is one of the histogram's values there, and the lower
#   bound where it has none; without bounds it draws as before.
# - test_tally: counts, nested sub-keys, and histograms.
# - test_priors_pool_what_was_played_before: a game's priors are the earlier seasons' counts, older ones
#   discounted, plus its own season's earlier weeks; a key no earlier season has comes from the first that
#   does; NFL_PRIORS_DECAY overrides.
# - test_priors_stay_within_a_rule: a key tied to rulebook fields only pools the seasons with the same rules.
# - test_usage_moves_a_role_toward_the_player: a player's own season scales his role's rate, by how much he has played.
# END
import random
from types import SimpleNamespace

import pytest

from shared.priors import Tally, blend, choice, hist, priors_of, save_priors, usage
from shared.priors.players import USAGE_SNAPS
from shared.rulebook import KICKOFF


def test_blend_is_ordered():
    blended = blend({"punt": 3, "offense": 1}, {"field_goal": 5, "offense": 5})
    assert list(blended) == ["field_goal", "offense", "punt"]
    assert blended == {"field_goal": 5.0, "offense": 6.0, "punt": 3.0}
    assert choice(blended, random.Random(0)) in blended


def test_hist_within_bounds():
    yards = {"-2": 1, "0": 5, "3": 10, "4": 10, "12": 2, "40": 1}
    assert {hist(yards, random.Random(seed), 3, 5) for seed in range(50)} == {3.0, 4.0}
    assert {hist(yards, random.Random(seed), 10, None) for seed in range(50)} == {12.0, 40.0}
    assert hist(yards, random.Random(0), None, -1) == -2.0
    assert hist(yards, random.Random(0), 5, 6) == 5.0 and hist(yards, random.Random(0), None, -5) == -6.0
    assert hist(yards, random.Random(7)) == float(choice(yards, random.Random(7)))


def test_tally():
    tally = Tally()
    tally.c["unit|4|1|5"]["punt"] += 2
    tally.c["snaps"]["n"] += 1
    tally.hist["yards"] += [3.4, 2.6, float("nan"), 500]
    tally.hist["yards_goal|1-2"].append(1)
    assert tally.priors() == {"unit": {"4|1|5": {"punt": 2}}, "snaps": {"n": 1}, "yards": {"3": 2, "110": 1},
                              "yards_goal": {"1-2": {"1": 1}}}


def test_priors_pool_what_was_played_before(tmp_path, monkeypatch):
    monkeypatch.delenv("NFL_PRIORS_DECAY", raising=False)
    file = tmp_path / "predictor.py"
    save_priors({1: {"run": {"3": 6, "4": 2}}, 2: {"run": {"3": 4}}}, file, 2022)
    save_priors({1: {"run": {"3": 20}, "personnel": {"11": 7}}}, file, 2023)  # only 2023's data can say the personnel
    save_priors({1: {"run": {"3": 30}}, 2: {"run": {"3": 10}}}, file, 2024)
    load = priors_of(file, decay=0.5)
    assert load(2024, 1) == {"run": {"3": 25.0, "4": 1.0}, "personnel": {"11": 7.0}}  # 2023, and half of 2022
    assert load(2024, 2)["run"] == {"3": 42.5, "4": 0.5}  # week 1 too, and the seasons before count half as much
    assert load(2024, 2)["personnel"] == {"11": 7.0}  # nothing this season: the last season still counts 1
    assert load(2025, 1)["run"] == {"3": 52.5, "4": 0.5} and load(2030, 9) == load(2025, 1)
    assert load(2023, 1) == {"run": {"3": 10.0, "4": 2.0}, "personnel": {"11": 7.0}}  # personnel: the first season with it
    assert load(2023, 2)["personnel"] == {"11": 7.0}  # and all of it, all season
    assert load(2022, 2)["run"] == {"3": 10.0, "4": 2.0}  # nothing earlier: the first season, whole
    assert priors_of(file, decay=1)(2025, 1)["run"] == {"3": 70, "4": 2}
    monkeypatch.setenv("NFL_PRIORS_DECAY", "0")
    assert priors_of(file, decay=0.5)(2025, 1)["run"] == {"3": 40.0, "4": 0.0}


def test_priors_stay_within_a_rule(tmp_path):
    file = tmp_path / "predictor.py"
    for season in (2022, 2023, 2024, 2025):
        save_priors({1: {"kickoff": {str(season): 1}, "punt": {str(season): 1}}}, file, season)
    load = priors_of(file, rules={"kickoff": KICKOFF}, decay=1)
    assert load(2026, 1) == {"kickoff": {"2025": 1}, "punt": {"2022": 1, "2023": 1, "2024": 1, "2025": 1}}
    assert load(2023, 1)["kickoff"] == {"2022": 1} and load(2023, 2)["kickoff"] == {"2022": 1, "2023": 1}
    assert load(2024, 2)["kickoff"] == {"2024": 1} and load(2025, 1)["kickoff"] == {"2025": 1}  # each the first season of a rule


def test_usage_moves_a_role_toward_the_player():
    on_play = {"RB2": {"carried": 80, "other": 20}}   # an RB2 carries 80% of the runs he is out there for,
    per_snap = {"RB2": {"carried": 40, "other": 60}}  # which is 40% of his snaps
    back = lambda **stats: SimpleNamespace(position="RB", rank=lambda slot: 2, stats=stats)
    rate = lambda player: usage(player, "carries", "carried", on_play, per_snap)
    assert rate(back()) == 0.8  # he hasn't played: his role
    assert rate(back(offense_snaps=USAGE_SNAPS, carries=0.4 * USAGE_SNAPS)) == pytest.approx(0.8)  # he is his role
    assert rate(back(offense_snaps=USAGE_SNAPS)) == pytest.approx(0.4)  # no carries yet: halfway to none
    assert rate(back(offense_snaps=9 * USAGE_SNAPS, carries=0.2 * 9 * USAGE_SNAPS)) == pytest.approx(0.44)
    assert usage(back(offense_snaps=50, carries=9), "carries", "carried", {}, {}) == 0.0  # a role nobody counted
