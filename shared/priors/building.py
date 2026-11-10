# START
# Building priors from real plays: what each event's priors.py (observe(tally, sample)) works with.
# - Sample: one real play: its PlayContext, RealPlay.actual, the nflverse pbp row, and the FTN charting row (or None).
# - Tally: raw counts (tally.c[name][key] += 1) and values (tally.hist[name].append(x)); a name like
#   "unit|3|4-6|7" nests everything after the first "|" as a sub-key. priors() -> the JSON-ready dict, with
#   values turned into {"rounded value": count} histograms (clamped to -20..110).
# - present(value) -> bool: not None and not NaN.
# Readers of nflverse rows that more than one event needs:
# - flag(sample) -> (foul name, "offense" | "defense") | None: the flag on the play, in the play scenario's
#   foul names (FOULS maps nflverse's). PRESNAP: the fouls that belong to the pre-snap event.
# - kickoff_result(sample) -> (zone, result) | None: a kickoff that came down in the landing zone or end zone.
# END
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
}
PRESNAP = {"false_start", "delay_of_game", "encroachment", "neutral_zone_infraction", "defensive_offside",
           "defensive_too_many_men", "illegal_formation", "illegal_shift"}


@dataclass(frozen=True)
class Sample:
    context: object
    actual: dict
    row: object
    charting: object


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
    return name, "offense" if row.penalty_team == sample.context.situation.offense else "defense"


def kickoff_result(sample):
    s, row = sample.context.situation, sample.row
    if sample.actual["action"] != "kickoff" or s.kind != "kickoff" or not present(row.kick_distance):
        return None
    if row.kickoff_out_of_bounds == 1 or row.penalty_type in ("Kickoff Out of Bounds", "Kickoff Short of Landing Zone"):
        return None
    land = s.x + row.kick_distance
    if land < 80:  # short of the landing zone
        return None
    result = "touchback" if row.touchback == 1 else "muff" if row.fumble == 1 and row.return_yards == 0 else "return"
    return "end_zone" if land >= 100 else "landing_zone", result
