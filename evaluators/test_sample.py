# START
# sample_games against a fake schedule and stat lines (no cache needed): a game is sampled once it has a
# result and stat lines.
# END
import pandas as pd

from evaluators import sample


def test_a_game_without_a_result_or_stat_lines_is_not_sampled(monkeypatch):
    schedule = pd.DataFrame({"game_id": ["recorded", "uncharted", "upcoming"], "week": [1, 1, 2],
                             "result": [3.0, -7.0, None]})
    monkeypatch.setattr(sample, "load", lambda name, season: schedule)
    monkeypatch.setattr(sample, "stat_lines", lambda season: pd.DataFrame({"game_id": ["recorded"]}))
    assert sample.sample_games([2026]) == {2026: ["recorded"]}
    assert sample.sample_games([2026], weeks=[2]) == {}
