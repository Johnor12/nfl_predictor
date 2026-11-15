# START
# Building priors from real plays: what each event's priors.py (observe(tally, sample)) works with.
# - Sample: one real play: its PlayContext, RealPlay.actual, the nflverse pbp row, the FTN charting row (or
#   None), and the participation row (who was on the field; None where the season has no such data).
# - Tally: raw counts (tally.c[name][key] += 1) and values (tally.hist[name].append(x)); a name like
#   "unit|3|4-6|7" nests everything after the first "|" as a sub-key. priors() -> the JSON-ready dict, with
#   values turned into {"rounded value": count} histograms (clamped to -20..110).
# - present(value) -> bool: not None and not NaN.
# Readers of nflverse rows that more than one event needs:
# - flag(sample) -> (foul name, "offense" | "defense") | None: the flag on the play, in the play scenario's
#   foul names (FOULS maps nflverse's, to the foul enforced the same way where the scenario has no foul of
#   that name; a pair is the name by side). PRESNAP: the fouls that belong to the pre-snap event.
# - flagrant(sample) -> bool: the flagged player was disqualified.
# Readers of the participation row (None when the season has no such data, or the row is unusable):
# - personnel(sample) -> str: the offense's personnel group: backs and tight ends ("11", "12"), with a "+" for
#   each lineman past five.
# - package(sample) -> str: the defense's package by its defensive backs: goal_line (3 or fewer), base,
#   nickel, dime (6 or more).
# - played(sample) -> (offense ids, defense ids): the 11 players each team had on the field.
# - kickoff_result(sample) -> (zone, result) | None: a kickoff that came down in the landing zone or end
#   zone: return, touchback, fair_catch, or muff.
# - nullified(sample) -> run, pass, punt, field_goal, or kickoff: what a play wiped out by a penalty was
#   (nflverse labels it no_play; its description still says).
# - timeout_case(sample) -> (context, "offense" | "defense" | "none"): the play's context as it stood before
#   any timeout was called (the clock as it was, the caller's timeout given back), and who called one. Only
#   the context and actual are read, so a shared.nflverse RealPlay does as well as a Sample.
# END
import dataclasses
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

FOULS = {
    "False Start": "false_start", "Delay of Game": "delay_of_game", "Encroachment": "encroachment",
    "Neutral Zone Infraction": "neutral_zone_infraction", "Defensive Offside": "defensive_offside",
    "Defensive Too Many Men on Field": "defensive_too_many_men", "Illegal Formation": "illegal_formation",
    "Illegal Shift": "illegal_shift", "Illegal Motion": "illegal_shift", "Offensive Offside": "false_start",
    "Offensive Holding": "offensive_holding", "Defensive Holding": "defensive_holding",
    "Illegal Contact": "illegal_contact", "Defensive Pass Interference": "defensive_pass_interference",
    "Offensive Pass Interference": "offensive_pass_interference",
    "Ineligible Downfield Pass": "ineligible_downfield_pass", "Intentional Grounding": "intentional_grounding",
    "Roughing the Passer": "roughing_the_passer", "Roughing the Kicker": "roughing_the_kicker",
    "Running Into the Kicker": "running_into_the_kicker", "Fair Catch Interference": "fair_catch_interference",
    "Face Mask": "face_mask", "Horse Collar Tackle": "face_mask", "Unnecessary Roughness": "unnecessary_roughness",
    "Illegal Blindside Block": "unnecessary_roughness", "Lowering the Head to Make Forcible Contact": "unnecessary_roughness",
    "Chop Block": "unnecessary_roughness", "Low Block": "unnecessary_roughness", "Tripping": "unnecessary_roughness",
    "Unsportsmanlike Conduct": "unsportsmanlike_conduct", "Taunting": "unsportsmanlike_conduct",
    "Illegal Block Above the Waist": "illegal_block_in_the_back",
    "Offensive Too Many Men on Field": "offensive_too_many_men", "Illegal Forward Pass": "illegal_forward_pass",
    "Illegal Touch Pass": "illegal_touch_pass", "Illegal Touch Kick": "illegal_touch_kick",
    "Player Out of Bounds on Kick": "illegal_touch_kick", "Ineligible Downfield Kick": "illegal_touch_kick",
    "Kick Catch Interference": "fair_catch_interference", "Hip Drop Tackle": "unnecessary_roughness",
    "Disqualification": "unnecessary_roughness",
    # names from earlier seasons
    "Personal Foul": "unnecessary_roughness", "Lowering the Head to Initiate Contact": "unnecessary_roughness",
    "Clipping": "unnecessary_roughness", "Illegal Crackback": "unnecessary_roughness",
    "Illegal Double-Team Block": "unnecessary_roughness", "Player Out of Bounds on Punt": "illegal_touch_kick",
    "Defensive 12 On-field": "defensive_too_many_men", "Offensive 12 On-field": "offensive_too_many_men",
    "Illegal Use of Hands": ("offensive_holding", "defensive_holding"),
    "Illegal Substitution": ("offensive_too_many_men", "defensive_too_many_men"),
}
PRESNAP = {"false_start", "delay_of_game", "encroachment", "neutral_zone_infraction", "defensive_offside",
           "defensive_too_many_men", "offensive_too_many_men", "illegal_formation", "illegal_shift"}


@dataclass(frozen=True)
class Sample:
    context: object
    actual: dict
    row: object
    charting: object
    participation: object = None


def present(value) -> bool:
    return value is not None and value == value


def _histogram(values, low=-20, high=110) -> dict:
    return dict(Counter(str(int(min(high, max(low, round(v))))) for v in values if present(v)))


class Tally:
    def __init__(self):
        self.c = defaultdict(Counter)
        self.hist = defaultdict(list)

    def priors(self) -> dict:
        out = {}
        items = [(key, dict(counter)) for key, counter in self.c.items()]
        items += [(key, _histogram(values)) for key, values in self.hist.items()]
        for key, value in items:
            name, _, sub = key.partition("|")
            if sub:
                out.setdefault(name, {})[sub] = value
            else:
                out[name] = value
        return out


def flag(sample):
    row = sample.row
    name = FOULS.get(row.penalty_type) if row.penalty == 1 else None
    if name is None:
        return None
    side = "offense" if row.penalty_team == sample.context.situation.offense else "defense"
    return (name if isinstance(name, str) else name[side == "defense"]), side


def flagrant(sample) -> bool:
    return "Disqualification" in str(sample.row.desc)


def _positions(text) -> Counter:
    return Counter({position: int(count) for count, position in re.findall(r"(\d+) (\w+)", str(text))})


def personnel(sample):
    row = sample.participation
    if row is None or not present(row.offense_personnel):
        return None
    counts = _positions(row.offense_personnel)
    backs, receivers = counts["RB"] + counts["FB"], counts["TE"] + counts["WR"]
    quarterbacks = counts.get("QB", 1)  # before 2023 one quarterback and five linemen go without saying
    linemen = counts["C"] + counts["G"] + counts["T"] + counts["OL"] or 5
    if quarterbacks != 1 or linemen < 5 or 1 + backs + receivers + linemen != 11:
        return None
    return f"{backs}{counts['TE']}" + "+" * (linemen - 5)


def package(sample):
    row = sample.participation
    if row is None or not present(row.defense_personnel):
        return None
    counts = _positions(row.defense_personnel)
    if sum(counts.values()) != 11:
        return None
    backs = sum(counts[position] for position in ("CB", "S", "FS", "SS", "DB"))
    return "goal_line" if backs <= 3 else "base" if backs == 4 else "nickel" if backs == 5 else "dime"


def played(sample):
    row, ctx = sample.participation, sample.context
    if row is None or not (present(row.offense_players) and present(row.defense_players)):
        return None
    ids = f"{row.offense_players};{row.defense_players}".split(";")  # in every season's ids, unlike players_on_play
    teams = {team: tuple(pid for pid in ids if pid in ctx.by_id and ctx.by_id[pid].team == team)
             for team in (ctx.situation.offense, ctx.situation.defense)}
    return tuple(teams.values()) if all(len(players) == 11 for players in teams.values()) else None


def kickoff_result(sample):
    s, row = sample.context.situation, sample.row
    if sample.actual["action"] != "kickoff" or s.kind != "kickoff" or not present(row.kick_distance):
        return None
    if row.kickoff_out_of_bounds == 1 or row.penalty_type in ("Kickoff Out of Bounds", "Kickoff Short of Landing Zone"):
        return None
    land = s.x + row.kick_distance
    if land < 80:  # short of the landing zone
        return None
    result = ("touchback" if row.touchback == 1 else "fair_catch" if row.kickoff_fair_catch == 1
              else "muff" if row.fumble == 1 and row.return_yards == 0 else "return")
    return "end_zone" if land >= 100 else "landing_zone", result


def nullified(sample) -> str:
    play = str(sample.row.desc).lower().split("penalty")[0]
    if "punt" in play:
        return "punt"
    if "field goal" in play or "extra point" in play:
        return "field_goal"
    if " kicks " in play:
        return "kickoff"
    if " pass " in play or "sacked" in play or "scrambles" in play:
        return "pass"
    return "run"


def timeout_case(sample):
    ctx, team = sample.context, sample.actual.get("timeout")
    s = ctx.situation
    if team not in s.timeouts:
        return ctx, "none"
    before = dataclasses.replace(s, clock_running=sample.actual["timeout_clock_running"],
                                 timeouts={**s.timeouts, team: min(3, s.timeouts[team] + 1)})
    return dataclasses.replace(ctx, situation=before), "offense" if team == s.offense else "defense"
