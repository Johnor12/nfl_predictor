# START
# The game's invariants (see RULES.md).
# - validate_game(result, plays=True) -> list[str]: what's broken (empty if the game is valid). With
#   plays=False the plays themselves aren't re-checked with the play scenario's validate_play.
# Internals: _timeline walks the record once, checking each play's situation against what came before it
#   (score, possession and spot, clock, timeouts, the kickoffs that start a half or overtime, and players
#   sidelined by an injury); _totals checks the result against the sum of its plays; _ending checks how the
#   game ended.
# END
from scenarios.coin_toss import Toss
from scenarios.game import clock
from scenarios.game.record import Stoppage
from scenarios.game.roster import REST_OF_GAME
from scenarios.play import validate_play
from shared.rulebook import rules_for

SPOT = ("kind", "offense", "x", "down", "distance")


def validate_game(result, plays: bool = True) -> list[str]:
    if not result.plays:
        return ["no plays"]
    errors = []
    if plays:
        errors += [f"play {i}: {error}" for i, play in enumerate(result.plays) for error in validate_play(play)]
    return errors + _timeline(result) + _totals(result) + _ending(result)


def _sidelined(result) -> dict:
    out = {}
    for player, first, missed in result.absences:
        last = len(result.plays) if missed >= REST_OF_GAME else first + missed
        out.setdefault(player, []).append(range(first, last))
    return out


def _timeline(result) -> list[str]:
    game, rules = result.context.game, rules_for(result.context.game.season)
    errors, sidelined = [], _sidelined(result)
    score = {game.home: 0, game.away: 0}
    timeouts = {game.home: clock.TIMEOUTS, game.away: clock.TIMEOUTS}
    opening = kicker = prev = None
    index, warned = 0, False
    for entry in result.record:
        if isinstance(entry, Toss):
            kicker = entry.kicking
            if entry.overtime:
                timeouts = dict.fromkeys(timeouts, clock.overtime_setup(game, rules)[2])
            else:
                opening = entry
        elif isinstance(entry, Stoppage):
            if entry.kind == "timeout":
                timeouts[entry.team] -= 1
            warned = entry.kind == "two_minute_warning" or (warned and entry.kind != "period_end")
            if entry.kind == "period_end" and entry.quarter == 2:
                if prev.next.kind == "try":
                    errors.append("the first half ended before the try")
                kicker = opening.second_half_kicking
                timeouts = dict.fromkeys(timeouts, clock.TIMEOUTS)
        else:
            s, where = entry.context.situation, f"play {index}"
            if s.score != score:
                errors.append(f"{where}: score {s.score}, expected {score}")
            if s.timeouts != timeouts or min(timeouts.values()) < 0:
                errors.append(f"{where}: timeouts {s.timeouts}, expected {timeouts}")
            if not 0 <= s.clock <= clock.QUARTER:
                errors.append(f"{where}: clock {s.clock}")
            if clock.has_warning(game, s.quarter) and s.clock <= clock.WARNING and not warned and (
                    prev is not None and prev.context.situation.quarter == s.quarter):
                errors.append(f"{where}: inside two minutes without a two-minute warning")
            if kicker:
                if (s.kind, s.offense, s.x) != ("kickoff", kicker, rules.kickoff_line):
                    errors.append(f"{where}: expected a kickoff by {kicker}")
            elif prev is not None:
                expected = prev.next
                if any(getattr(s, key) != getattr(expected, key) for key in SPOT):
                    errors.append(f"{where}: starts from a different spot than the last play left")
                if s.quarter == expected.quarter and s.clock > expected.clock + 1e-9:
                    errors.append(f"{where}: the clock went up")
                if s.quarter not in (expected.quarter, expected.quarter + 1):
                    errors.append(f"{where}: quarter {s.quarter} after {expected.quarter}")
            on_field = entry.record[0].offense.players + entry.record[0].defense.players
            for pid in on_field:
                if any(index in missed for missed in sidelined.get(pid, ())):
                    errors.append(f"{where}: {pid} is on the field while sidelined")
            score, kicker, prev = entry.next.score, None, entry
            index += 1
    return errors


def _totals(result) -> list[str]:
    errors = []
    points = dict.fromkeys(result.score, 0)
    stats, team_stats = {}, {team: {} for team in result.score}
    for play in result.plays:
        for team, value, _ in play.scores:
            points[team] += value
        for totals, lines in ((stats, play.stats), (team_stats, play.team_stats)):
            for key, line in lines.items():
                for stat, value in line.items():
                    totals.setdefault(key, {})[stat] = totals.setdefault(key, {}).get(stat, 0.0) + value
    if points != result.score or result.plays[-1].next.score != result.score:
        errors.append(f"final score {result.score} isn't the sum of the scoring plays {points}")
    for name, got, expected in (("player", result.stats, stats), ("team", result.team_stats, team_stats)):
        if any(abs(got.get(key, {}).get(stat, 0.0) - value) > 1e-6
               for key, line in expected.items() for stat, value in line.items()) or set(got) != set(expected):
            errors.append(f"{name} stats aren't the sum of the plays' stats")
    return errors


def _ending(result) -> list[str]:
    game, errors = result.context.game, []
    home, away = result.score[game.home], result.score[game.away]
    winner = None if home == away else game.home if home > away else game.away
    if result.winner != winner:
        errors.append(f"winner {result.winner} with the score {result.score}")
    if result.quarters != result.plays[-1].context.situation.quarter or result.quarters < 4:
        errors.append(f"{result.quarters} periods played")
    if winner is None and (game.playoff or result.quarters < 5):
        errors.append("a tie without a regular season overtime")
    last = result.record[-1]
    timed_out = isinstance(last, Stoppage) and last.kind == "period_end" and clock.last_period(game, last.quarter)
    if not timed_out and not (result.quarters > 4 and winner):
        errors.append("the game ended before time ran out")
    return errors
