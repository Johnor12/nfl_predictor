# START
# Season-versioned NFL rule constants. Nothing outside this file hardcodes a season-dependent value.
# - Rules: dataclass of constants (yard lines are measured from the named team's own goal line).
# - rules_for(season): builds the Rules for a season by applying rule changes in order.
# Values are from memory of the rulebook and should be checked against the official rules per season.
# END
from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    season: int
    # scrimmage
    touchback_line: int = 20            # touchbacks after punts, interceptions, fumbles (receiving team's yard line)
    pat_line: int = 15                  # try by kick is snapped from the opponent's 15 (the 2 before 2015)
    two_point_line: int = 2             # try by run/pass is snapped from the opponent's 2
    defensive_try_points: bool = True   # defense scores 2 by returning a try to the other end zone (2015+)
    field_goal_snap_depth: int = 7      # holder's depth behind the line of scrimmage
    end_zone_depth: int = 10
    # free kicks
    kickoff_line: int = 35              # kicking team's yard line (the 30 before 2011)
    safety_kick_line: int = 20
    kickoff_touchback_line: int = 35    # receiving team's yard line on a kickoff touchback
    dynamic_kickoff: bool = True        # 2024+ alignment and landing zone
    landing_zone_start: int = 20        # landing zone: receiving team's 20 to its goal line
    landing_zone_touchback_line: int = 20  # dynamic: lands in landing zone, then goes into the end zone
    kickoff_short_line: int = 40        # dynamic: short of the landing zone or out of bounds -> receiving team's 40
    kickoff_out_of_bounds_line: int = 40
    kickoff_fair_catch: bool = False    # fair catch allowed on kickoffs (not under the dynamic kickoff)
    onside_declared: str = "trailing"   # when an onside kick may be declared: "any", "trailing_q4", "trailing"
    onside_min_distance: int = 10
    # clock
    play_clock: int = 40
    admin_play_clock: int = 25
    # discipline
    unsportsmanlike_ejection: bool = True  # two unsportsmanlike fouls disqualify (2016+)


def rules_for(season: int) -> Rules:
    if season < 2011:
        raise ValueError(f"no rulebook for {season}")
    r = dict(season=season)
    if season < 2015:
        r.update(pat_line=2, defensive_try_points=False)
    if season < 2016:
        r.update(unsportsmanlike_ejection=False)
    if season < 2024:
        r.update(dynamic_kickoff=False, onside_declared="any", kickoff_fair_catch=True,
                 kickoff_touchback_line=25 if season >= 2016 else 20)
    if season == 2024:
        r.update(kickoff_touchback_line=30, onside_declared="trailing_q4")
    return Rules(**r)
