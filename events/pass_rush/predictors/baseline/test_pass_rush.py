# START
# Spot check of the baseline pass rush predictor (no network needed).
# - test_a_quarterbacks_season_moves_his_dropbacks: his sack and scramble rates go from the league's toward
#   his own as he drops back more.
# END
from types import SimpleNamespace

import pytest

from events.pass_rush.predictors.baseline import DROPBACKS, dropback

LEAGUE = {"sack": 7, "scramble": 5, "throw": 88}


def test_a_quarterbacks_season_moves_his_dropbacks():
    formation = SimpleNamespace(qb="qb")
    rates = lambda **stats: dropback(SimpleNamespace(by_id={"qb": SimpleNamespace(stats=stats)}), formation, LEAGUE)
    assert rates() == LEAGUE  # he hasn't played: the league's
    runner = rates(dropbacks=DROPBACKS, scrambles=0.15 * DROPBACKS)
    assert runner["scramble"] == pytest.approx(0.10) and runner["sack"] == pytest.approx(0.035)  # halfway to his own
    assert sum(runner.values()) == pytest.approx(1)
