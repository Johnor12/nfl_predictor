# START
# Player roles and situation buckets: the keys priors are counted and sampled by.
# - role(player) -> str: position plus depth rank for skill players ("RB1", "WR3"), else the position.
# - group(player) -> str: coarse group for weighting tacklers, sackers, and fouling players (OL, DL, LB, DB, ...).
# - dist_bucket(distance), field_bucket(x), air_bucket(air_yards), script(situation): bucket keys.
# - goal_bucket(yards_to_goal): goal-to-go bucket; fg_bin(distance): field goal distance bin.
# END

SKILL = ("QB", "RB", "WR", "TE")


def role(player) -> str:
    if player.position in SKILL:
        rank = player.rank(player.position)
        return f"{player.position}{min(rank, 3) if rank else 3}"
    return player.position


def group(player) -> str:
    return {"FB": "RB", "K": "ST", "P": "ST", "LS": "ST"}.get(player.position, player.position)


def dist_bucket(distance) -> str:
    if distance <= 1:
        return "1"
    if distance <= 3:
        return "2-3"
    if distance <= 6:
        return "4-6"
    return "7-10" if distance <= 10 else "11+"


def field_bucket(x) -> str:
    return str(min(9, max(0, int(x // 10))))


def air_bucket(air_yards) -> str:
    if air_yards <= 0:
        return "behind"
    if air_yards < 10:
        return "short"
    return "medium" if air_yards < 20 else "deep"


def script(s) -> str:
    """Game script: late in a half with the score pushing the offense to hurry or to bleed the clock."""
    lead = s.score[s.offense] - s.score[s.defense]
    if s.quarter == 4 and s.clock <= 300 and lead < 0 or s.quarter == 2 and s.clock <= 120:
        return "hurry"
    if s.quarter == 4 and s.clock <= 300 and lead > 0:
        return "bleed"
    return "normal"


def goal_bucket(to_goal) -> str:
    """Distance-to-goal bucket for goal-to-go priors (1-10 yards)."""
    return "1-2" if to_goal <= 2 else "3-5" if to_goal <= 5 else "6-10"


def fg_bin(distance) -> str:
    for upper in (29, 39, 44, 49, 54, 59):
        if distance <= upper:
            return str(upper)
    return "60+"
