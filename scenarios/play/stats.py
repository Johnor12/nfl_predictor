# START
# Stat crediting: every player's and team's stat line, computed only from the play record's facts.
# - credit(ctx, los, record, final, accepted) -> {player_id: {stat: value}}
# - team_totals(ctx, los, record, final, stats, penalty_yards) -> {team: {stat: value}}: the sum of player
#   stats plus team-only items (sack_yards, penalty_yards).
# Conventions: passing/rushing/receiving yards run from the line of scrimmage to where the carry ended (the
# spot of a fumble; the goal line on a touchdown); return yards from where possession was gained; sack yards
# are a team stat, not the passer's; tries credit only two_pt (no attempts or yards); a no-play credits only
# the penalty.
# END
from collections import defaultdict

from scenarios.play.events import PassRush
from scenarios.play.field import rel
from scenarios.play.record import Carry, Kick, LooseBall, Pass, Sack, facts

RETURNS = {
    "interception": ("int_ret_yds", "int_ret_td"),
    "punt_return": ("punt_ret_yds", "punt_ret_td"),
    "kick_return": ("kick_ret_yds", "kick_ret_td"),
    "recovery": ("fumble_ret_yds", "fumble_ret_td"),
}
RETURN_COUNTS = {"punt_return": "punt_returns", "kick_return": "kick_returns"}


def _next_carry(record, i):
    return next(f for f in record[i + 1:] if isinstance(f, Carry))


def credit(ctx, los, record, final, accepted) -> dict[str, dict[str, float]]:
    st = defaultdict(lambda: defaultdict(float))

    def add(pid, key, value=1.0):
        if pid:
            st[pid][key] += value

    for foul in accepted:
        add(foul.player, "penalties")
    if final.no_play:
        return {pid: dict(line) for pid, line in st.items()}
    is_try = ctx.situation.kind == "try"

    def gained(c):
        return rel(ctx, c.team, c.end) - rel(ctx, c.team, los)

    for i, f in enumerate(record):
        if isinstance(f, Pass):
            if is_try:
                if f.result == "complete" and _next_carry(record, i).how == "touchdown":
                    add(f.passer, "two_pt")
                    add(f.receiver, "two_pt")
                continue
            add(f.passer, "pass_att")
            add(f.receiver, "targets")
            if f.result == "complete":
                c = _next_carry(record, i)
                add(f.passer, "pass_cmp")
                add(f.receiver, "receptions")
                add(f.passer, "pass_yds", gained(c))
                add(f.receiver, "rec_yds", gained(c))
                if c.how == "touchdown":
                    add(f.passer, "pass_td")
                    add(f.receiver, "rec_td")
            elif f.result == "intercepted":
                add(f.passer, "int_thrown")
                add(f.defender, "interceptions")
            add(f.defender, "passes_defended")
        elif isinstance(f, PassRush):
            for pid in f.hitters:
                add(pid, "qb_hits")
        elif isinstance(f, Sack):
            add(f.passer, "sacked")
            for pid in f.sackers:
                add(pid, "sacks", 1 / len(f.sackers))
        elif isinstance(f, Carry):
            for pid in f.tacklers:
                add(pid, "tackles" if len(f.tacklers) == 1 else "assists")
            touchdown = f.how == "touchdown"
            if f.kind in ("run", "scramble", "kneel"):
                if is_try:
                    add(f.player, "two_pt", touchdown)
                    continue
                add(f.player, "rush_att")
                add(f.player, "rush_yds", gained(f))
                add(f.player, "rush_td", touchdown)
            elif f.kind in RETURNS:
                yards, td = RETURNS[f.kind]
                if f.kind in RETURN_COUNTS:
                    add(f.player, RETURN_COUNTS[f.kind])
                add(f.player, yards, rel(ctx, f.team, f.end) - rel(ctx, f.team, f.start))
                add(f.player, td, touchdown)
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
            elif f.kind in ("field_goal", "pat"):
                attempts, made = ("fg_att", "fg_made") if f.kind == "field_goal" else ("xp_att", "xp_made")
                add(f.kicker, attempts)
                add(f.kicker, made, f.result == "good")
            else:
                add(f.kicker, "kickoffs")
                add(f.kicker, "kickoff_touchbacks", f.result == "touchback")
    return {pid: {k: v for k, v in line.items() if v} for pid, line in st.items()}


def team_totals(ctx, los, record, final, player_stats, penalty_yards) -> dict[str, dict[str, float]]:
    s = ctx.situation
    out = {s.offense: defaultdict(float), s.defense: defaultdict(float)}
    for pid, line in player_stats.items():
        for key, value in line.items():
            out[ctx.by_id[pid].team][key] += value
    if not final.no_play and s.kind != "try":
        for sack in facts(record, Sack):
            out[s.offense]["sack_yards"] += rel(ctx, s.offense, los) - rel(ctx, s.offense, sack.x)
    for team, yards in penalty_yards.items():
        if yards:
            out[team]["penalty_yards"] += yards
    return {team: dict(line) for team, line in out.items()}
