# START
# Stat crediting: every player's and team's stat line, computed only from the play record's facts.
# - credit(ctx, rules, los, record, live, enforcement) -> {player_id: {stat: value}}
# - team_totals(ctx, player_stats, penalty_yards) -> {team: {stat: value}}: the sum of player stats, plus the
#   penalty yards of a foul charged to nobody.
# Conventions (a box score's): passing/rushing/receiving yards run from the line of scrimmage to where the
# carry ended (the spot of a fumble; the goal line on a touchdown); air yards from the line to the target,
# yards after the catch from there on; return yards from where possession was gained; sack yards are the
# passer's (sack_yards), not rushing yards; tries credit only two_pt (no attempts or yards); a no-play
# credits only the penalty. A player who takes a lateral gets the yards from there on, in the same category,
# without an attempt, reception, or return; the passer's yards run to the end of the last lateral.
# A first down (pass_, rush_, rec_first_downs) is a carry that reached the line to gain or scored. A sack is
# also a tackle (an assist each when it is shared). A tackle for loss (tfl) is the first tackler's on a run
# or a catch that ended behind the line, and a sack made alone that lost yards. A safety is the first
# tackler's or sacker's.
# A touchdown on an interception return is a def_td, on a kick return or a loose ball of a kick play a
# special_teams_td, on any other recovery a fumble_ret_td. penalty_yards are the yards a player's accepted
# foul cost his team.
# Charted stats (what Pro Football Reference's charters count), on scrimmage downs: a defender's hurries,
# blitzes, missed_tackles, and pressures (a hurry, a hit, or a sack); what he allowed in coverage
# (coverage_targets, _cmp, _yds, _td); a passer's pressured (hurried, hit, or sacked), hurried, hit (without
# a sack), blitzed, bad_throws, and pass_drops; a receiver's drops; a carrier's broken tackles
# (rush_broken_tackles, rec_broken_tackles) and a runner's rush_yds_before_contact and _after_contact.
# END
from collections import defaultdict

from events.offensive_formation import Formation
from events.pass_rush import PassRush
from scenarios.play.field import field_goal_distance, rel
from scenarios.play.record import Carry, Kick, LooseBall, Pass, Sack, facts

RETURNS = {
    "interception": ("int_ret_yds", "int_ret_td", "def_td"),
    "punt_return": ("punt_ret_yds", "punt_ret_td", "special_teams_td"),
    "kick_return": ("kick_ret_yds", "kick_ret_td", "special_teams_td"),
    "recovery": ("fumble_ret_yds", "fumble_ret_td", None),
}
RETURN_COUNTS = {"punt_return": "punt_returns", "kick_return": "kick_returns"}
RUNS = ("run", "scramble", "kneel")


def _last_carry(record, i):
    """Where the ball caught at record[i] ended up: the catch's carry, or the last lateral after it."""
    carries = [f for f in record[i + 1:] if isinstance(f, Carry)]
    last = carries[0]
    for c in carries[1:]:
        if not c.lateral:
            break
        last = c
    return last


def credit(ctx, rules, los, record, live, enforcement) -> dict[str, dict[str, float]]:
    st = defaultdict(lambda: defaultdict(float))
    s = ctx.situation

    def add(pid, key, value=1.0):
        if pid:
            st[pid][key] += value

    for foul, yards in zip(enforcement.accepted, enforcement.foul_yards):
        add(foul.player, "penalties")
        add(foul.player, "penalty_yards", yards)
    if enforcement.final.no_play:
        return {pid: {k: v for k, v in line.items() if v} for pid, line in st.items()}
    is_try = s.kind == "try"
    kicked = bool(facts(record, Kick))

    def gained(c, start):
        return rel(ctx, c.team, c.end) - rel(ctx, c.team, start)

    def moved_chains(c):
        if s.kind != "scrimmage" or c.team != s.offense or c.how in ("fumble", "lateral"):
            return False
        return c.how == "touchdown" or rel(ctx, c.team, c.end) >= rel(ctx, c.team, los) + s.distance

    for i, f in enumerate(record):
        if isinstance(f, Pass):
            if is_try:
                if f.result == "complete" and _last_carry(record, i).how == "touchdown":
                    add(f.passer, "two_pt")
                    add(_last_carry(record, i).player, "two_pt")
                continue
            add(f.passer, "pass_att")
            add(f.receiver, "targets")
            add(f.coverage, "coverage_targets")
            add(f.receiver, "drops", f.drop)
            add(f.passer, "pass_drops", f.drop)
            add(f.passer, "bad_throws", f.bad_throw)
            if f.receiver:
                air = rel(ctx, s.offense, f.x) - rel(ctx, s.offense, los)
                add(f.passer, "pass_air_yds", air)
                add(f.receiver, "target_air_yds", air)
            if f.result == "complete":
                first, last = record[i + 1], _last_carry(record, i)
                add(f.passer, "pass_cmp")
                add(f.receiver, "receptions")
                add(f.passer, "pass_yds", gained(last, los))
                add(f.passer, "pass_yac", gained(last, f.x))
                add(f.receiver, "rec_yac", gained(first, f.x))
                add(f.passer, "pass_td", last.how == "touchdown")
                add(f.coverage, "coverage_cmp")
                add(f.coverage, "coverage_yds", gained(last, los))
                add(f.coverage, "coverage_td", last.how == "touchdown")
                add(f.passer, "pass_first_downs", moved_chains(last))
                add(last.player, "rec_first_downs", moved_chains(last))
            elif f.result == "intercepted":
                add(f.passer, "int_thrown")
                add(f.defender, "interceptions")
            add(f.defender, "passes_defended")
        elif isinstance(f, PassRush):
            for pid in f.hitters:
                add(pid, "qb_hits")
            if not is_try:
                passer, sacked = facts(record, Formation)[0].qb, f.result in ("sack", "strip_sack")
                for pid in sorted(set(f.hurriers + f.hitters + f.sackers)):
                    add(pid, "pressures")
                for pid in f.hurriers:
                    add(pid, "hurries")
                for pid in f.blitzers:
                    add(pid, "blitzes")
                add(passer, "pressured", bool(sacked or f.hurriers or f.hitters))
                add(passer, "hurried", bool(f.hurriers))
                add(passer, "hit", bool(f.hitters) and not sacked)
                add(passer, "blitzed", bool(f.blitzers))
        elif isinstance(f, Sack):
            alone, lost = len(f.sackers) == 1, rel(ctx, s.offense, los) - rel(ctx, s.offense, f.x)
            add(f.passer, "sacked")
            for pid in f.sackers:
                add(pid, "sacks", 1 / len(f.sackers))
                add(pid, "tackles" if alone else "assists")
                add(pid, "tfl", alone and lost > 0 and not is_try)
            if not is_try:
                add(f.passer, "sack_yards", lost)
        elif isinstance(f, Carry):
            for pid in f.tacklers:
                add(pid, "tackles" if len(f.tacklers) == 1 else "assists")
            for pid in f.missed:
                add(pid, "missed_tackles", not is_try)
            touchdown = f.how == "touchdown"
            if f.kind in RUNS:
                if is_try:
                    add(f.player, "two_pt", touchdown)
                    continue
                add(f.player, "rush_att", not f.lateral)
                add(f.player, "rush_yds", gained(f, f.start if f.lateral else los))
                add(f.player, "rush_td", touchdown)
                add(f.player, "rush_first_downs", f.kind != "kneel" and moved_chains(f))
                add(f.player, "rush_broken_tackles", f.broken)
                if f.contact is not None and not f.lateral:
                    add(f.player, "rush_yds_before_contact", f.contact)
                    add(f.player, "rush_yds_after_contact", gained(f, los) - f.contact)
            elif f.kind == "catch" and not is_try:
                add(f.player, "rec_yds", gained(f, f.start if f.lateral else los))
                add(f.player, "rec_td", touchdown)
                add(f.player, "rec_broken_tackles", f.broken)
            elif f.kind in RETURNS:
                yards, td, box = RETURNS[f.kind]
                if f.kind in RETURN_COUNTS:
                    add(f.player, RETURN_COUNTS[f.kind], not f.lateral)
                add(f.player, yards, gained(f, f.start))
                add(f.player, "special_teams_td" if kicked and not box else td, touchdown)
                add(f.player, box, touchdown and bool(box))
            if f.kind in ("run", "scramble", "catch") and not is_try and f.tacklers and gained(f, los) < 0:
                add(f.tacklers[0], "tfl")
        elif isinstance(f, LooseBall):
            if f.cause in ("fumble", "bad_snap"):
                add(f.fumbler, "fumbles")
                add(f.forced_by, "forced_fumbles")
                if f.team is not None and f.team != f.last_team:
                    add(f.fumbler, "fumbles_lost")
            add(f.player, "fumble_recoveries")
        elif isinstance(f, Kick):
            if f.result == "blocked":
                add(f.player, "kicks_blocked")
            if f.kind == "punt":
                add(f.kicker, "punts")
                if f.land is not None:
                    add(f.kicker, "punt_yds", min(f.land, 100) - f.x)
                if f.result == "fair_catch":
                    add(f.player, "fair_catches")
            elif f.kind in ("field_goal", "fair_catch_kick", "pat"):
                attempts, made = ("xp_att", "xp_made") if f.kind == "pat" else ("fg_att", "fg_made")
                add(f.kicker, attempts)
                add(f.kicker, made, f.result == "good")
                if f.kind != "pat" and f.result == "good":
                    add(f.kicker, "fg_made_yds", field_goal_distance(rules, f.x, f.kind == "fair_catch_kick"))
            else:
                add(f.kicker, "kickoffs")
                add(f.kicker, "kickoff_touchbacks", f.result == "touchback")
    if live is not None and live.how == "safety" and not is_try:
        downed = [f for f in record if isinstance(f, (Sack, Carry))]
        last = downed[-1] if downed else None
        by = last.sackers if isinstance(last, Sack) else last.tacklers if isinstance(last, Carry) else ()
        add(by[0] if by else None, "safeties")
    return {pid: {k: v for k, v in line.items() if v} for pid, line in st.items()}


def team_totals(ctx, player_stats, penalty_yards) -> dict[str, dict[str, float]]:
    s = ctx.situation
    out = {s.offense: defaultdict(float), s.defense: defaultdict(float)}
    for pid, line in player_stats.items():
        for key, value in line.items():
            out[ctx.by_id[pid].team][key] += value
    for team, yards in penalty_yards.items():  # a foul charged to nobody still cost the team its yards
        if yards - out[team]["penalty_yards"]:
            out[team]["penalty_yards"] = yards
    return {team: {k: v for k, v in line.items() if v} for team, line in out.items()}
