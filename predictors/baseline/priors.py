# START
# Builds the baseline predictors' priors (counts and histograms) from a season of real plays.
# - build_priors(season) -> dict: every prior the baseline predictors sample from (see the keys below).
# - save_priors(priors, season) / load_priors(season): JSON at predictors/baseline/priors_<season>.json.
# - FOULS: nflverse penalty names -> our foul catalog names.
# - CLI: `python -m predictors.baseline.priors 2026` rebuilds and saves the file.
# Counts are kept raw (not normalized) so small samples stay visible; the predictors normalize when sampling.
# Hand-set values (personnel, timing, onside kicks, injuries' length) live in predictors.py, not here.
# END
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from nflverse import load, real_plays
from predictors.baseline.roles import air_bucket, dist_bucket, fg_bin, field_bucket, goal_bucket, group, role, script

HERE = Path(__file__).resolve().parent
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


def _hist(values, low=-20, high=110):
    return dict(Counter(str(int(min(high, max(low, round(v))))) for v in values if pd.notna(v)))


def _category(action):
    return {"run": "run", "scramble": "run", "kneel": "run", "pass": "pass", "sack": "pass", "spike": "pass",
            "punt": "punt", "field_goal": "field_goal", "extra_point": "field_goal", "kickoff": "kickoff"}.get(action)


def _nullified(desc):
    """The kind of play a penalty wiped out (nflverse labels those rows no_play), from its description."""
    play = str(desc).lower().split("penalty")[0]
    if "punt" in play:
        return "punt"
    if "field goal" in play or "extra point" in play:
        return "field_goal"
    if " kicks " in play:
        return "kickoff"
    if " pass " in play or "sacked" in play or "scrambles" in play:
        return "pass"
    return "run"


def build_priors(season: int) -> dict:
    plays = real_plays(season)
    pbp = load("pbp", season)
    ftn = load("ftn", season).set_index(["nflverse_game_id", "nflverse_play_id"])
    c = defaultdict(Counter)       # c[prior][key] -> count
    hist = defaultdict(list)       # hist[prior] -> values
    fouls = defaultdict(Counter)   # fouls[category][type|side] -> count
    snaps = Counter()              # plays per foul category
    for rp in plays:
        ctx, s, actual = rp.context, rp.context.situation, rp.actual
        row = pbp.loc[rp.row]
        players = ctx.by_id
        f = ftn.loc[(row.game_id, int(row.play_id))] if (row.game_id, int(row.play_id)) in ftn.index else None
        action = actual["action"]
        presnap = row.penalty == 1 and FOULS.get(row.penalty_type) in PRESNAP
        if s.kind in ("scrimmage", "try"):
            snaps["presnap"] += 1
        category = _category(action) if action != "no_play" else None if presnap else _nullified(row.desc)
        if category:
            snaps[category] += 1
        if row.penalty == 1 and row.penalty_type in FOULS and (presnap or category):
            side = "offense" if row.penalty_team == s.offense else "defense"
            fouls["presnap" if presnap else category][f"{FOULS[row.penalty_type]}|{side}"] += 1
        if action == "no_play":
            continue
        if "injured" in str(row.desc):
            c["injury"]["injured"] += 1
        c["injury"]["plays"] += 1
        down_dist = f"{s.down}|{dist_bucket(s.distance)}" if s.kind == "scrimmage" else None

        if s.kind == "scrimmage":
            unit = {"punt": "punt", "field_goal": "field_goal"}.get(action, "offense")
            if action != "kneel":
                c[f"unit|{down_dist}|{field_bucket(s.x)}"][unit] += 1
            if action in ("run", "scramble", "pass", "sack"):
                c[f"pass_rate|{script(s)}|{down_dist}"]["pass" if action != "run" else "run"] += 1
                c[f"shotgun|{down_dist}"]["shotgun" if row.shotgun == 1 else "under_center"] += 1
                if f is not None and f.n_defense_box > 0:
                    hist[f"box|{down_dist}"].append(f.n_defense_box)
        if s.kind == "try":
            c["two_point"]["attempt" if row.two_point_attempt == 1 else "kick"] += 1
            if row.two_point_attempt == 1:
                c["two_point_play"]["pass" if action in ("pass", "sack") else "run"] += 1
                c["two_point_result"][str(row.two_point_conv_result)] += 1
            if action == "extra_point":
                c["pat"][str(row.extra_point_result)] += 1
            continue

        if action == "run":
            rusher = players.get(row.rusher_player_id)
            if rusher:
                c["run_carrier"][role(rusher)] += 1
        if action in ("run", "scramble") or (action == "pass" and row.complete_pass == 1):
            kind = "catch" if action == "pass" else action
            yards = row.yards_after_catch if kind == "catch" else row.yards_gained
            to_goal = row.yardline_100 - (row.air_yards if kind == "catch" else 0)
            if to_goal >= 50:  # far from the goal line, so long gains aren't cut short by touchdowns
                hist[kind].append(yards)
            elif 0 < to_goal <= 10 and kind != "scramble":  # goal to go: gains compressed by the end zone
                hist[f"{kind}_goal|{goal_bucket(to_goal)}"].append(yards)
            c[f"carry_end|{kind}"]["fumble" if row.fumble == 1 else "out_of_bounds" if row.out_of_bounds == 1 else "tackled"] += 1
        if action in ("pass", "sack", "scramble"):
            throwaway = f is not None and bool(f.is_throw_away)
            outcome = "sack" if action == "sack" else "scramble" if action == "scramble" else "throwaway" if throwaway else "throw"
            c["dropback"][outcome] += 1
            if f is not None and f.n_pass_rushers > 0:
                hist["rushers"].append(f.n_pass_rushers)
        if action == "sack":
            hist["sack_yards"].append(-row.yards_gained)
            c["strip_sack"]["fumble" if row.fumble == 1 else "no"] += 1
            for pid in (row.sack_player_id, row.half_sack_1_player_id):
                if pid in players:
                    c["sacker"][group(players[pid])] += 1
        if action == "pass" and pd.notna(row.receiver_player_id):
            receiver = players.get(row.receiver_player_id)
            if receiver:
                c["target"][role(receiver)] += 1
            if pd.notna(row.air_yards):
                result = "intercepted" if row.interception == 1 else "complete" if row.complete_pass == 1 else "incomplete"
                if row.yardline_100 <= 10:
                    hist[f"air_yards_goal|{goal_bucket(row.yardline_100)}"].append(row.air_yards)
                    c[f"pass_result_goal|{goal_bucket(row.yardline_100)}"][result] += 1
                else:
                    hist["air_yards"].append(row.air_yards)
                    c[f"pass_result|{air_bucket(row.air_yards)}"][result] += 1
            if pd.notna(row.pass_location):
                c["direction"][row.pass_location] += 1
            c["qb_hit"]["hit" if row.qb_hit == 1 else "no"] += 1
            if row.incomplete_pass == 1:
                c["defended"]["yes" if pd.notna(row.pass_defense_1_player_id) else "no"] += 1
        if row.interception == 1:
            hist["interception"].append(row.return_yards)
        if row.fumble == 1 and action in ("run", "scramble", "pass", "sack"):
            c["fumble_recovery"]["lost" if row.fumble_lost == 1 else "kept"] += 1
        for pid in (row.solo_tackle_1_player_id, row.assist_tackle_1_player_id, row.tackle_with_assist_1_player_id):
            if pid in players:
                c[f"tackler|{'kick' if action in ('punt', 'kickoff') else 'scrimmage'}"][group(players[pid])] += 1
        if action in ("run", "pass", "scramble") and (pd.notna(row.solo_tackle_1_player_id) or pd.notna(row.assist_tackle_1_player_id)):
            c["assisted"]["yes" if pd.notna(row.assist_tackle_1_player_id) else "no"] += 1

        if action == "punt":
            if row.punt_blocked == 1:
                c["punt_blocked"]["yes"] += 1
                continue
            c["punt_blocked"]["no"] += 1
            hist[f"punt_distance|{field_bucket(s.x)}"].append(row.kick_distance)
            land = s.x + row.kick_distance if pd.notna(row.kick_distance) else None
            if land is not None and land < 100:
                bucket = "inside_10" if land >= 90 else "inside_20" if land >= 80 else "open"
                result = ("fair_catch" if row.punt_fair_catch == 1 else "downed" if row.punt_downed == 1
                          else "out_of_bounds" if row.punt_out_of_bounds == 1 else "touchback" if row.touchback == 1
                          else "muff" if row.fumble == 1 and row.return_yards == 0 else "return")
                if result != "touchback":
                    c[f"punt_result|{bucket}"][result] += 1
            if pd.notna(row.punt_returner_player_id) and row.punt_fair_catch != 1:
                hist["punt_return"].append(row.return_yards)
        if action == "field_goal":
            distance = row.kick_distance
            if pd.notna(distance):
                c[f"fg|{fg_bin(distance)}"][str(row.field_goal_result)] += 1
        if action == "kickoff" and s.kind == "kickoff":
            if row.kickoff_out_of_bounds == 1 or row.penalty_type == "Kickoff Out of Bounds":
                c["kickoff_oob"]["yes"] += 1
                continue
            c["kickoff_oob"]["no"] += 1
            if pd.isna(row.kick_distance):
                continue
            hist["kickoff_distance"].append(row.kick_distance)
            land = s.x + row.kick_distance
            if row.penalty_type == "Kickoff Short of Landing Zone" or land < 80:
                continue
            zone = "end_zone" if land >= 100 else "landing_zone"
            result = "touchback" if row.touchback == 1 else "muff" if row.fumble == 1 and row.return_yards == 0 else "return"
            c[f"kickoff_result|{zone}"][result] += 1
            if result == "return":
                hist["kick_return"].append(row.return_yards)

    priors = {"season": season, "plays": len(plays)}
    for key, counter in c.items():
        name, _, sub = key.partition("|")
        target = priors.setdefault(name, {})
        if sub:
            target[sub] = dict(counter)
        else:
            priors[name] = dict(counter)
    for key, values in hist.items():
        name, _, sub = key.partition("|")
        if sub:
            priors.setdefault(name, {})[sub] = _hist(values)
        else:
            priors[name] = _hist(values)
    priors["fouls"] = {category: {k: v / snaps[category] for k, v in counter.items()} for category, counter in fouls.items()}
    return priors


def save_priors(priors: dict, season: int) -> Path:
    path = HERE / f"priors_{season}.json"
    path.write_text(json.dumps(priors, indent=1, sort_keys=True))
    return path


def load_priors(season: int) -> dict:
    return json.loads((HERE / f"priors_{season}.json").read_text())


if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    print(save_priors(build_priors(year), year))
