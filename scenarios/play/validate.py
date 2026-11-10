# START
# The play validator: the invariants every play the scenario produces must satisfy.
# - validate_play(result) -> list[str]: broken invariants (empty if the play is valid).
# Checks: 11 legal players per side and a legal formation; players with stats were on the field; carriers
# and tacklers on the right teams; passing = receiving yards, completions = receptions, interceptions
# thrown = made; sacks aren't rushes; tries add no yardage; no-plays credit only penalties; fumble
# bookkeeping; team stats = player sums; scores only through scoring events; possession changes explained;
# field position reconciles with the yardage (plays without loose balls); the next situation is legal.
# END
from events.lineups import Lineups
from events.offensive_formation import Formation
from scenarios.play.context import FREE_KICKS, KINDS
from scenarios.play.field import formation_errors, lineup_errors, other, rel
from scenarios.play.record import Carry, Kick, LooseBall, Pass, facts

SCORE_VALUES = {"touchdown": 6, "field_goal": 3, "extra_point": 1, "two_point": 2, "defensive_two_point": 2}
TEAM_SUMMED = ("pass_yds", "rec_yds", "rush_yds", "tackles", "sacks", "penalties", "punt_yds")


def validate_play(result) -> list[str]:
    ctx, record, st = result.context, result.record, result.stats
    s, nxt = ctx.situation, result.next
    off, de = s.offense, s.defense
    errors = []

    def total(key, team=None):
        return sum(line.get(key, 0) for pid, line in st.items() if team in (None, ctx.by_id[pid].team))

    lineups = facts(record, Lineups)[0]
    errors += lineup_errors(ctx, lineups)
    for formation in facts(record, Formation):
        errors += formation_errors(ctx, lineups, formation)
    on_field = {off: set(lineups.offense.players), de: set(lineups.defense.players)}
    errors += [f"{pid} has stats but wasn't on the field" for pid in st if pid not in on_field[off] | on_field[de]]
    carries = facts(record, Carry)
    for c in carries:
        if c.player not in on_field[c.team]:
            errors.append(f"carrier {c.player} isn't on the field for {c.team}")
        if any(t not in on_field[other(ctx, c.team)] for t in c.tacklers):
            errors.append(f"a tackler of {c.player} isn't on the field for the other team")

    if abs(total("pass_yds") - total("rec_yds")) > 1e-6:
        errors.append(f"passing yards {total('pass_yds')} != receiving yards {total('rec_yds')}")
    if total("pass_cmp") != total("receptions"):
        errors.append("completions != receptions")
    if total("int_thrown") != total("interceptions"):
        errors.append("interceptions thrown != interceptions made")
    runs = [c for c in carries if c.kind in ("run", "scramble", "kneel")]
    if not result.no_play and s.kind != "try" and total("rush_att") != len(runs):
        errors.append("rushing attempts != designed runs + scrambles + kneels")
    if s.kind == "try" and any(total(k) for k in ("pass_yds", "rush_yds", "rec_yds", "pass_att", "rush_att")):
        errors.append("a try credited yardage or attempts")
    if result.no_play and any(k != "penalties" for line in st.values() for k in line):
        errors.append("a no-play credited stats besides penalties")
    lost = sum(1 for b in facts(record, LooseBall) if b.cause in ("fumble", "bad_snap") and b.team not in (None, b.last_team))
    if not result.no_play and total("fumbles_lost") != lost:
        errors.append("lost fumbles != opponent recoveries")
    if total("forced_fumbles") > total("fumbles"):
        errors.append("more forced fumbles than fumbles")
    for team in (off, de):
        for key in TEAM_SUMMED:
            if abs(result.team_stats[team].get(key, 0) - total(key, team)) > 1e-6:
                errors.append(f"{team} team {key} != sum of player {key}")

    errors += _scoring_errors(result)
    errors += _possession_errors(result)
    errors += _situation_errors(nxt)
    if result.elapsed < 0:
        errors.append("negative elapsed time")
    errors += _reconcile(result)
    return errors


def _scoring_errors(result):
    s, nxt = result.context.situation, result.next
    errors = []
    for team in (s.offense, s.defense):
        if nxt.score[team] - s.score[team] != sum(p for t, p, _ in result.scores if t == team):
            errors.append(f"{team}'s score changed without a matching scoring event")
    touchdowns = {c.team for c in facts(result.record, Carry) if c.how == "touchdown"}
    good_kicks = [k for k in facts(result.record, Kick) if k.result == "good"]
    for team, points, how in result.scores:
        expected = (1 if s.kind == "try" else 2) if how == "safety" else SCORE_VALUES.get(how)
        if points != expected:
            errors.append(f"{how} worth {points}")
        if how in ("touchdown", "two_point", "defensive_two_point") and (team not in touchdowns or result.no_play):
            errors.append(f"{how} for {team} without a touchdown carry")
        if how in ("field_goal", "extra_point") and (not good_kicks or result.no_play):
            errors.append(f"{how} without a good kick")
    return errors


def _possession_errors(result):
    ctx, nxt, record, final = result.context, result.next, result.record, result.final
    s = ctx.situation
    if s.kind == "scrimmage" and nxt.kind == "scrimmage" and nxt.offense != s.offense:
        explained = (any(p.result == "intercepted" for p in facts(record, Pass))
                     or any(b.team == s.defense or (b.team is None and rel(ctx, s.offense, b.recovery_x) >= 100)
                            for b in facts(record, LooseBall))
                     or any(k.kind in ("punt", "field_goal") and k.result != "blocked" for k in facts(record, Kick))
                     or (s.down == 4 and s.offense in (final.team, result.live and result.live.team)))
        if not explained:
            return ["possession changed without an interception, lost fumble, kick, or turnover on downs"]
    if s.kind in FREE_KICKS and nxt.kind == "scrimmage" and nxt.offense == s.offense and not result.no_play:
        if not (any(k.result == "kicking_recovery" for k in facts(record, Kick))
                or any(b.team == s.offense or (b.team is None and rel(ctx, s.defense, b.recovery_x) >= 100)
                       for b in facts(record, LooseBall))):
            return ["kicking team kept the ball without recovering the kick"]
    if s.kind == "try" and not (nxt.kind == "kickoff" and nxt.offense == s.offense) and nxt.kind != "try":
        return ["a try must be followed by the scoring team's kickoff"]
    return []


def _situation_errors(nxt):
    errors = []
    if nxt.kind not in KINDS:
        errors.append(f"next play kind {nxt.kind}")
    if not 0 < nxt.x < 100:
        errors.append(f"next play at {nxt.x}, outside the field of play")
    if nxt.kind == "scrimmage":
        if nxt.down not in (1, 2, 3, 4):
            errors.append(f"next down {nxt.down}")
        if not 0 < nxt.distance <= 100 - nxt.x + 1e-9:
            errors.append(f"next distance {nxt.distance} at {nxt.x}")
    return errors


def _reconcile(result):
    """Field position change = offensive/return yardage + penalty yardage (plays without loose balls)."""
    ctx, record, s, nxt, final = result.context, result.record, result.context.situation, result.next, result.final
    skip = ("touchback", "kick_missed", "kick_out_of_bounds", "kick_short", "safety", "touchdown")
    if (s.kind != "scrimmage" or nxt.kind != "scrimmage" or facts(record, LooseBall)
            or final.how in skip or (result.live and result.live.how in skip)
            or any(f.timing == "return" for f in result.accepted)):
        return []

    def yards(team, *keys):
        return sum(line.get(k, 0) for pid, line in result.stats.items() if ctx.by_id[pid].team == team for k in keys)

    def penalty(team):
        return result.penalty_yards[other(ctx, team)] - result.penalty_yards[team]

    if final.team == s.offense and not final.kick:
        expected = (s.x + yards(s.offense, "rush_yds", "rec_yds") + penalty(s.offense)
                    - result.team_stats[s.offense].get("sack_yards", 0))
        actual = nxt.x if nxt.offense == s.offense else 100 - nxt.x
    else:
        starts = ([p.x for p in facts(record, Pass) if p.result == "intercepted"]
                  + [k.land for k in facts(record, Kick) if k.kind == "punt" and k.land is not None])
        if len(starts) != 1 or result.no_play:
            return []
        team = nxt.offense
        expected = rel(ctx, team, starts[0]) + yards(team, "int_ret_yds", "punt_ret_yds") + penalty(team)
        actual = nxt.x
    if abs(expected - actual) > 1e-6:
        return [f"field position doesn't reconcile: yardage says {expected:.1f}, next play at {actual:.1f}"]
    return []
