# START
# Tests for the betting lines evaluator.
# - test_no_vig: the bookmaker's margin is removed.
# - test_score_lines: the market's scores, pushes and unplayed lines left out, and a simulator's scores on the
#   same lines (no data needed).
# - test_season_lines: the cached 2026 lines score against the results. Skipped unless the files are in .cache.
# END
import random

import pytest

from evaluators.lines import Line, no_vig, score_lines
from shared.lines.lines import CACHE
from shared.nflverse.download import CACHE as NFLVERSE


def test_no_vig():
    assert no_vig(-110, -110) == pytest.approx(0.5)
    assert no_vig(-200, 170) == pytest.approx((200 / 300) / (200 / 300 + 100 / 270))
    assert no_vig(-200, 170) + no_vig(170, -200) == pytest.approx(1)
    assert no_vig(float("nan"), -110) == 0.5


def test_score_lines():
    rng = random.Random(0)
    lines, samples = [], {}
    for i in range(400):
        truth = rng.gauss(0, 10)
        actual = round(truth + rng.gauss(0, 13))
        lines.append(Line("spread", ("margin", i), round(truth + 8) + 0.5, 0.5, actual))  # a market 8 points off
        lines.append(Line("moneyline", ("margin", i), 0.0, 0.5, actual))
        samples[("margin", i)] = [truth + rng.gauss(0, 13) for _ in range(200)]
    lines += [Line("total", ("total", 0), 44.0, 0.5, 44.0), Line("total", ("total", 1), 44.5, 0.5, None)]
    market = {row["market"]: row for row in score_lines(lines)}
    assert set(market) == {"moneyline", "spread"}  # the push and the unplayed game aren't scored
    assert market["spread"]["n"] == 400 and market["spread"]["brier"] == pytest.approx(0.25)
    assert market["spread"]["over"] < 0.4 and market["moneyline"]["mae"] is None
    both = {row["market"]: row for row in score_lines(lines, samples)}
    assert both["spread"]["sim_brier"] < both["spread"]["brier"] and both["spread"]["sim_mae"] < both["spread"]["mae"]
    assert both["moneyline"]["sim_log_loss"] < both["moneyline"]["log_loss"]
    assert both["spread"]["sim_crps"] < both["spread"]["sim_mae"]
    del samples[("margin", 0)]
    assert score_lines(lines, samples)[0]["n"] == market["moneyline"]["n"] - (lines[1].actual != 0)


@pytest.mark.skipif(not any(CACHE.glob("props_*.json")) or not (NFLVERSE / "stats_player_week_2026.parquet").exists(),
                    reason="lines cache missing")
def test_season_lines(tmp_path):
    from evaluators.lines import lines, write_report
    from shared.nflverse import load
    played = load("games", 2026).dropna(subset=["result"])
    week = int(played.week.min())
    if not all((CACHE / f"props_{int(event)}.json").exists() for event in played[played.week == week].espn):
        pytest.skip("lines cache incomplete")
    every = lines(2026, weeks=[week])
    games = sum(played.week == week)
    assert sum(l.market == "moneyline" for l in every) == games
    assert all(0 < l.p_over < 1 for l in every) and sum(l.actual is not None for l in every) > 0.8 * len(every)
    rows = {row["market"]: row for row in score_lines(every)}
    assert {"moneyline", "spread", "total", "pass_yds", "rec_yds"} <= set(rows) and 30 < rows["pass_yds"]["mae"] < 100
    assert "Moneyline reliability" in write_report(2026, [week], path=tmp_path / "lines.md").read_text()
