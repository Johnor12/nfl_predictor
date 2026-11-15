# START
# The game clock's rules: periods, the two-minute warning, and what happens when time runs out.
# - QUARTER, TIMEOUTS (per half), OVERTIME_TIMEOUTS (regular season), WARNING, RUNOFF: constants, in seconds
#   where they are times.
# - has_warning(game, quarter): whether the period has a two-minute warning.
# - cut_before_snap(game, s, result) -> "period_end" | "two_minute_warning" | None: the running clock reached
#   the end of the period, or the two-minute warning, before the ball was snapped.
# - at_timeout(game, s, seconds) -> float: the clock when a timeout is called `seconds` into the play clock.
# - last_period(game, quarter): the period's end ends the game (unless the score is tied after the fourth).
# - try_matters(game, s): whether a try after time has expired is played (it's skipped when the game is
#   ending and it can't change who wins).
# - takes_runoff(s): the hardcoded choice of the defense to take a 10-second runoff.
# - overtime_setup(game, rules) -> (format, seconds per period, timeouts per team).
# END
from events.pre_snap import PreSnap
from scenarios.play import facts

QUARTER = 900
TIMEOUTS = 3
OVERTIME_TIMEOUTS = 2
WARNING = 120
RUNOFF = 10


def has_warning(game, quarter) -> bool:
    return quarter in (2, 4) or (quarter > 4 and (not game.playoff or quarter % 2 == 0))


def cut_before_snap(game, s, result) -> str | None:
    if not s.clock_running:
        return None
    used = sum(f.seconds for f in facts(result.record, PreSnap))
    if used >= s.clock:
        return "period_end"
    if has_warning(game, s.quarter) and s.clock > WARNING >= s.clock - used:
        return "two_minute_warning"
    return None


def at_timeout(game, s, seconds) -> float:
    """A running clock runs until the timeout is called, which is before it reaches the two-minute warning
    or the end of the period: a team calling one gets it in."""
    if not s.clock_running:
        return s.clock
    floor = WARNING if has_warning(game, s.quarter) and s.clock > WARNING else 0
    return max(s.clock - seconds, min(s.clock, floor + 1.0))


def last_period(game, quarter) -> bool:
    return quarter == 4 or (quarter > 4 and not game.playoff)


def try_matters(game, s) -> bool:
    if not last_period(game, s.quarter):
        return True
    return -2 <= s.score[s.offense] - s.score[s.defense] <= 0


def takes_runoff(s) -> bool:
    return s.quarter == 2 or s.score[s.defense] >= s.score[s.offense]


def overtime_setup(game, rules) -> tuple[str, int, int]:
    if game.playoff:
        return rules.playoff_overtime_format, rules.playoff_overtime_seconds, TIMEOUTS
    return rules.overtime_format, rules.overtime_seconds, OVERTIME_TIMEOUTS
