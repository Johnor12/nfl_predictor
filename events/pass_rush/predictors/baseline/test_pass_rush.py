# START
# Spot check of the baseline pass rush predictor (no network needed).
# - test_a_quarterbacks_season_moves_his_dropbacks: his sack and scramble rates go from the league's toward
#   his own as he drops back more.
# END
from types import SimpleNamespace

import pytest

from events.pass_rush.predictors.baseline import DROPBACKS, _dropback

LEAGUE = {"sack": 7, "scramble": 5, "throw": 88}


def test_a_quarterbacks_season_moves_his_dropbacks():
    quarterback = lambda **stats: SimpleNamespace(stats=stats)
    assert _dropback(quarterback(), LEAGUE) == LEAGUE  # he hasn't played: the league's
    runner = _dropback(quarterback(dropbacks=DROPBACKS, scrambles=0.15 * DROPBACKS), LEAGUE)
    assert runner["scramble"] == pytest.approx(0.10) and runner["sack"] == pytest.approx(0.035)  # halfway to his own
    assert sum(runner.values()) == pytest.approx(1)
