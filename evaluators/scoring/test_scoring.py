# START
# Tests for the scoring toolkit (no data needed).
# - test_fair_crps_is_unbiased: small ensembles score the same on average as large ones.
# - test_binary_fair_crps_is_fair_brier: fair CRPS on True/False samples equals the fair Brier formula.
# - test_fair_brier_sums_the_classes / test_climatology_is_the_pooled_forecast / test_kinds.
# - test_probability_scores: smoothing, Brier, and log loss for stated probabilities.
# - test_calibrated_forecasts_look_calibrated: flat PIT and a diagonal reliability diagram.
# - test_scorecard: skill is positive for an informative forecast and about zero for the pooled one; sim noise
#   shrinks with more sims; merging two scorecards equals scoring everything on one.
# END
import random
from collections import Counter

import pytest

from evaluators.scoring import (Scorecard, brier, climatology, fair_brier, fair_crps, histogram, kind_of, log_loss,
                                pit, probability, reliability)


def _mean(values):
    values = list(values)
    return sum(values) / len(values)


def test_fair_crps_is_unbiased():
    rng = random.Random(1)
    draw = lambda m: [rng.gauss(0, 1) for _ in range(m)]
    small = _mean(fair_crps(draw(3), rng.gauss(0, 1)) for _ in range(40_000))
    large = _mean(fair_crps(draw(200), rng.gauss(0, 1)) for _ in range(2_000))
    assert small == pytest.approx(large, abs=0.02)
    assert large == pytest.approx(1 / 3.14159 ** 0.5, abs=0.03)  # the CRPS of a perfect standard normal forecast


def test_binary_fair_crps_is_fair_brier():
    samples = [True] * 3 + [False] * 7
    p, m = 0.3, 10
    for actual in (True, False):
        assert fair_crps(samples, actual) == pytest.approx((p - actual) ** 2 - p * (1 - p) / (m - 1))


def test_fair_brier_sums_the_classes():
    samples = ["run"] * 5 + ["pass"] * 4 + ["punt"]
    expected = sum(fair_crps([x == c for x in samples], "pass" == c) for c in ("run", "pass", "punt"))
    assert fair_brier(samples, "pass") == pytest.approx(expected)
    assert fair_brier(["run"] * 10, "run") == 0
    assert fair_brier(["run"] * 10, "pass") == 2


def test_climatology_is_the_pooled_forecast():
    for kind, outcomes in (("numeric", [0.0, 1.0, 1.0, 4.0, 9.0]), ("binary", [True, False, False, True, False]),
                           ("categorical", ["a", "b", "b", "c", "b"])):
        pooled = _mean((fair_brier if kind == "categorical" else fair_crps)(outcomes[:i] + outcomes[i + 1:], y)
                       for i, y in enumerate(outcomes))  # each case forecast with every other case's outcome
        assert climatology(kind, Counter(outcomes)) == pytest.approx(pooled), kind


def test_kinds():
    assert [kind_of(v) for v in (True, "run", 3, 2.5)] == ["binary", "categorical", "numeric", "numeric"]
    with pytest.raises(TypeError):
        kind_of(None)


def test_probability_scores():
    assert probability([True] * 10) == pytest.approx(10.5 / 11)
    assert probability([False] * 10) == pytest.approx(0.5 / 11)
    assert brier(0.7, True) == pytest.approx(0.09) and brier(0.7, False) == pytest.approx(0.49)
    assert log_loss(0.5, True) == pytest.approx(0.6931, abs=1e-4) and log_loss(0.9, False) > log_loss(0.9, True)


def test_calibrated_forecasts_look_calibrated():
    rng = random.Random(2)
    pits = [pit([rng.randint(0, 5) for _ in range(50)], rng.randint(0, 5), rng.random()) for _ in range(5_000)]
    assert all(0.07 < share < 0.13 for share in histogram(pits))
    pairs = [(p, rng.random() < p) for p in (rng.random() for _ in range(20_000))]
    assert all(abs(forecast - observed) < 0.04 for forecast, observed, _ in reliability(pairs))


def _case(rng):
    center = rng.choice([0, 10, 20])
    return center, center + rng.gauss(0, 2), rng.choice(["run", "pass"]) if center else "punt"


def test_scorecard():
    rng = random.Random(3)
    informed, pooled, first, second = Scorecard(), Scorecard(), Scorecard(), Scorecard()
    cases = [_case(rng) for _ in range(600)]
    for i, (center, yards, action) in enumerate(cases):
        samples = [center + rng.gauss(0, 2) for _ in range(40)]
        informed.add("yards", samples, yards)
        informed.add("yards (few sims)", samples[:8], yards)
        informed.add("big play", [x > 12 for x in samples], yards > 12)
        informed.add("action", [rng.choice(["run", "pass"]) if center else "punt" for _ in range(40)], action)
        informed.add("empty", [None, 3.0], yards)
        pooled.add("yards", [rng.choice(cases)[1] for _ in range(40)], yards)
        (first if i % 2 else second).add("yards", samples, yards)
    rows = {r["name"]: r for r in informed.rows()}
    assert rows["yards"]["kind"] == "numeric" and rows["yards"]["n"] == 600 and rows["yards"]["sims"] == 40
    assert rows["yards"]["skill"] > 0.7 and rows["big play"]["skill"] > 0.5 and rows["action"]["skill"] > 0.3
    assert rows["yards"]["sim_se"] < rows["yards (few sims)"]["sim_se"] < rows["yards"]["se"]
    assert 40 < rows["yards"]["sims_needed"] <= 10_000
    assert rows["empty"]["n"] == 0 and rows["empty"]["unscored"] == 600 and rows["empty"]["score"] is None
    assert abs(pooled.rows()[0]["skill"]) < 0.05
    assert len(informed.pit("yards")) == 10 and informed.reliability("big play") and informed.reliability("action")
    merged = second.merge(first).rows()[0]
    assert (merged["n"], merged["score"]) == (600, pytest.approx(rows["yards"]["score"]))
