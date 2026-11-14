# START
# Tests for the coin toss scenario (no data needed).
# - test_choices_decide_the_kickoffs: receive, kick, and defer under the rules; no deferring in overtime.
# - test_illegal_choices_raise: a team that isn't playing, or a choice that isn't allowed.
# - test_baseline_toss: the baseline is a fair coin that mostly defers.
# END
import random

import pytest

from scenarios.coin_toss import TossContext, TossPredictors, allowed_choices, load_toss_predictors, run_coin_toss
from scenarios.play import Game, IllegalChoice

GAME = Game("test", 2026, 1, "HOME", "AWAY")


def toss(winner, choice, overtime=False):
    predictors = TossPredictors(lambda ctx, rng: winner, lambda ctx, winner, allowed, rng: choice)
    return run_coin_toss(TossContext(GAME, (), overtime), predictors, random.Random(0))


def test_choices_decide_the_kickoffs():
    assert (toss("HOME", "defer").kicking, toss("HOME", "defer").second_half_kicking) == ("HOME", "AWAY")
    assert (toss("HOME", "receive").kicking, toss("HOME", "receive").second_half_kicking) == ("AWAY", "HOME")
    assert (toss("AWAY", "kick").kicking, toss("AWAY", "kick").second_half_kicking) == ("AWAY", "AWAY")
    overtime = toss("AWAY", "receive", overtime=True)
    assert (overtime.receiving, overtime.kicking, overtime.second_half_kicking) == ("AWAY", "HOME", None)
    assert "defer" not in allowed_choices(TossContext(GAME, (), True))


def test_illegal_choices_raise():
    with pytest.raises(IllegalChoice):
        toss("OTHER", "defer")
    with pytest.raises(IllegalChoice):
        toss("HOME", "defer", overtime=True)


def test_baseline_toss():
    predictors, rng = load_toss_predictors("baseline"), random.Random(0)
    tosses = [run_coin_toss(TossContext(GAME, ()), predictors, rng) for _ in range(2000)]
    assert 0.45 < sum(t.winner == "HOME" for t in tosses) / 2000 < 0.55
    assert sum(t.choice == "defer" for t in tosses) / 2000 > 0.8
    with pytest.raises(ValueError):
        load_toss_predictors("baseline", snap="baseline")
