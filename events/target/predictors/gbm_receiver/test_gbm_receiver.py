# START
# Tests of the trained receiver choice (no network needed; they use the committed model files).
# - test_who_is_thrown_to_follows_his_targets: among the eligible players, the one who has been thrown to
#   most is thrown to most, and the others still get theirs; a quarterback or a lineman isn't chosen while
#   a receiver is eligible, and is the baseline's choice when nobody else is.
# - test_plays_are_valid: synthetic plays with the trained receiver choice pass the validator.
# END
import dataclasses
import random

from events.target.predictors import gbm_receiver
from events.target.predictors.gbm_receiver.inputs import NAMES, candidates
from scenarios.play import load_predictors, run_play, validate_play
from scenarios.play.testing import synthetic_context, with_history

PREDICTORS = load_predictors("baseline", target="gbm_receiver")
MIDFIELD = dict(kind="scrimmage", offense="HOME", defense="AWAY", x=50.0, quarter=2, clock=600.0,
                score={"HOME": 10, "AWAY": 10}, down=1, distance=10.0)


def test_who_is_thrown_to_follows_his_targets():
    ctx = synthetic_context(random.Random(0), **MIDFIELD)
    ctx = with_history(ctx, "HOME-WR2", {"targets": 90.0, "offense_snaps": 500.0, "target_air_yds": 900.0})
    ctx = with_history(ctx, "HOME-WR1", {"targets": 20.0, "offense_snaps": 500.0, "target_air_yds": 200.0})
    eligible = ("HOME-QB1", "HOME-WR1", "HOME-WR2", "HOME-WR3", "HOME-TE1", "HOME-RB1")
    rows = candidates(ctx, [ctx.by_id[pid] for pid in eligible[1:]], True)
    assert all(len(row) == len(NAMES) for row in rows) and abs(rows[1][NAMES.index("share")] - 90 / 110) < 1e-9
    formation = dataclasses.replace(PREDICTORS.offensive_formation(ctx, PREDICTORS.lineups(ctx, random.Random(0)),
                                                                   random.Random(0)), under_center=False)
    rng = random.Random(0)
    thrown_to = [gbm_receiver.receiver(ctx, formation, eligible, rng) for _ in range(2000)]
    assert thrown_to.count("HOME-WR2") > 1.5 * thrown_to.count("HOME-WR1") > 0 and "HOME-QB1" not in thrown_to
    assert thrown_to.count("HOME-WR1") > thrown_to.count("HOME-WR3") > 0
    assert gbm_receiver.receiver(ctx, formation, ("HOME-QB1", "HOME-OL1"), rng) in ("HOME-QB1", "HOME-OL1")


def test_plays_are_valid():
    for seed in range(300):
        rng = random.Random(seed)
        assert validate_play(run_play(synthetic_context(rng), PREDICTORS, rng)) == [], seed
