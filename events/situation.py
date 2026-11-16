# START
# What is known before a scrimmage snap, as numbers: the inputs the trained predictors share. The same
# functions read a simulated play (a predictor) and a real one (its train.py), so the two can't drift apart.
# - NAMES / features(ctx) -> list[float]: the situation and the offense's game so far (nan where unknown).
# - PERSONNEL / personnel(group) -> list[float]: the offense's personnel group ("12+") as its backs, tight
#   ends, and linemen beyond five (nan without a group).
# - DROPBACKS, SNAPS: the play kinds that are dropbacks, and those that are runs or dropbacks.
# Internals: _game (the offense's plays in this game so far, from the history).
# END
import math

DROPBACKS = ("pass", "sack", "scramble")
SNAPS = ("run",) + DROPBACKS
NAMES = (
    # the situation
    "season", "down", "distance", "to_goal", "quarter", "clock", "half_seconds", "lead", "timeouts",
    "defense_timeouts", "clock_running", "home",
    # this game so far: the offense's dropbacks and runs, the snaps of this drive, and the last of them
    "game_passes", "game_runs", "drive_plays", "last_pass", "last_yards",
)
PERSONNEL = ("backs", "tight_ends", "extra_linemen")


def features(ctx) -> list[float]:
    s, g = ctx.situation, ctx.game
    passes, runs, drive, last = _game(ctx.history, s.offense)
    return [
        g.season, s.down, s.distance, 100 - s.x, s.quarter, s.clock, s.clock + 900 * (s.quarter in (1, 3)),
        s.score[s.offense] - s.score[s.defense], s.timeouts[s.offense], s.timeouts[s.defense],
        s.clock_running, s.offense == g.home,
        passes, runs, drive, last.kind != "run" if last else math.nan, last.yards if last else math.nan,
    ]


def personnel(group) -> list[float]:
    if not group:
        return [math.nan] * 3
    return [int(group[0]), int(group[1]), group.count("+")]


def _game(history, offense):
    """The offense's dropbacks and runs in this game, the snaps of its current drive, and the last of them
    (a play wiped out by a penalty doesn't end the drive, and isn't the last snap)."""
    passes = runs = drive = 0
    last = None
    for play in history:
        if play.offense == offense and play.kind in SNAPS:
            passes += play.kind != "run"
            runs += play.kind == "run"
    for play in reversed(history):
        if play.offense != offense or play.kind not in SNAPS + ("no_play",):
            break
        if play.kind in SNAPS:
            drive += 1
            last = last or play
    return passes, runs, drive, last
