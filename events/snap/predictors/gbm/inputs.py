# START
# The run-or-pass model's inputs: what the offense knows at the snap, as one row of numbers.
# - NAMES: the feature names, in the model's column order.
# - features(ctx) -> list[float]: one play's values (nan where unknown). The same function reads a simulated
#   play (predict) and a real one (train.py), so the two can't drift apart.
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


def features(ctx) -> list[float]:
    s, g = ctx.situation, ctx.game
    passes, runs, drive, last = _game(ctx.history, s.offense)
    return [
        g.season, s.down, s.distance, 100 - s.x, s.quarter, s.clock, s.clock + 900 * (s.quarter in (1, 3)),
        s.score[s.offense] - s.score[s.defense], s.timeouts[s.offense], s.timeouts[s.defense],
        s.clock_running, s.offense == g.home,
        passes, runs, drive, last.kind != "run" if last else math.nan, last.yards if last else math.nan,
    ]


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
