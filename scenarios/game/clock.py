# START
# The game clock's rules: periods, the two-minute warning, and what happens when time runs out.
# - QUARTER, TIMEOUTS (per half), OVERTIME_TIMEOUTS (regular season), WARNING, RUNOFF, CHALLENGES (per team
#   and game, before any it earns): constants, in seconds where they are times.
# - has_warning(game, quarter): whether the period has a two-minute warning.
# - cut_before_snap(game, s, result) -> "period_end" | "two_minute_warning" | None: the running clock reached
#   the end of the period, or the two-minute warning, before the ball was snapped.
# - at_timeout(game, s, seconds) -> float: the clock when a timeout is called `seconds` into the play clock.
# - last_period(game, quarter): the period's end ends the game (unless the score is tied after the fourth).
# - try_matters(game, s): whether a try after time has expired is played (it's skipped when the game is
#   ending and it can't change who wins).
# - takes_runoff(s): the hardcoded choice of the defense to take a 10-second runoff.
# - challengers(game, rules, s, timeouts, used) -> teams: who may challenge the play that started from `s`.
# - injury_timeouts(game, s, result) -> teams: who is charged for an injury stoppage after the play.
# - overtime_setup(game, rules) -> (format, seconds per period, timeouts per team).
# END
from events.pre_snap import PreSnap
from scenarios.play import facts

QUARTER = 900
TIMEOUTS = 3
OVERTIME_TIMEOUTS = 2
WARNING = 120
RUNOFF = 10
CHALLENGES = 2


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


def challengers(game, rules, s, timeouts, used) -> tuple[str, ...]:
    """The teams that may challenge the play that started from `s`. After the two-minute warning of a half and
    in overtime only the replay official starts a review. A team needs a timeout to lose (`timeouts`, after
    the play) and a challenge left: two a game, and a third once it has won enough of them (`used` is each
    team's challenges so far, True for one it won)."""
    if s.quarter > 4 or (has_warning(game, s.quarter) and s.clock <= WARNING):
        return ()

    def left(rulings) -> bool:
        return len(rulings) < CHALLENGES or (len(rulings) == CHALLENGES and sum(rulings) >= rules.third_challenge_wins)

    return tuple(team for team in (s.offense, s.defense) if timeouts[team] > 0 and left(used[team]))


def injury_timeouts(game, s, result) -> tuple[str, ...]:
    """The teams charged a timeout for an injury on the play: after the two-minute warning, a team with an
    injured player, unless the other team fouled, possession changed, or the play was a try, a free kick, or
    a field goal that was good."""
    if not result.injuries or s.kind != "scrimmage" or not (has_warning(game, s.quarter) and s.clock <= WARNING):
        return ()
    if result.next.offense != s.offense or any(how == "field_goal" for _, _, how in result.scores):
        return ()
    hurt = {result.context.by_id[injury.player].team for injury in result.injuries}
    fouled = {foul.team for foul in result.accepted + result.declined}
    return tuple(team for team, opponent in ((s.offense, s.defense), (s.defense, s.offense))
                 if team in hurt and opponent not in fouled)
