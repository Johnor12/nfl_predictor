# START
# The coaching staff of every team in every game: the head coach, the offensive and defensive coordinators,
# and who called the plays on each side of the ball.
# - staff(season) -> {(game id, team): Staff}: every game in the season's schedule, played or not. A role
#   nobody is known to hold is None (a team without a coordinator of that title, or a game the play-caller
#   file doesn't have yet).
# - ROLES: the roles, as `Staff`'s field names.
# Three sources, the later ones overriding the earlier:
# - the schedule's head coaches (load("games")), for a game the play-caller file doesn't have.
# - the play-caller file (load("play_callers")): per team and game, the head coach and both play callers.
# - staff.csv, which is ours: a row per stint (season, team, role, name, first_week, last_week, source). It
#   has every coordinator (nobody publishes them), and the few head coaches and play callers the other two
#   sources have wrong. A stint covers the team's games of those weeks; an empty name means nobody.
# END
from functools import lru_cache
from pathlib import Path

import pandas as pd

from scenarios.play import Staff
from shared.nflverse.download import load

ROLES = ("head_coach", "offensive_coordinator", "defensive_coordinator", "offensive_play_caller", "defensive_play_caller")
STINTS = Path(__file__).with_name("staff.csv")
CALLERS = {"off_play_caller": "offensive_play_caller", "def_play_caller": "defensive_play_caller"}


@lru_cache(maxsize=None)
def staff(season: int) -> dict:
    schedule, callers = load("games", season), load("play_callers", season)
    assert schedule is not None and callers is not None
    sides = [schedule[["game_id", "week", f"{side}_team", f"{side}_coach"]].set_axis(["game_id", "week", "team", "scheduled"], axis=1)
             for side in ("home", "away")]
    callers = callers.rename(columns=CALLERS).drop(columns=["season", "week"])
    rows = pd.concat(sides, ignore_index=True).merge(callers, on=["game_id", "team"], how="left")
    rows["head_coach"] = rows.head_coach.fillna(rows.scheduled)
    rows = rows.astype(object).where(rows.notna(), None).to_dict("records")
    stints = pd.read_csv(STINTS)
    stints = stints[stints.season == season].astype(object).where(stints.notna(), None).to_dict("records")
    for row in rows:
        for stint in stints:
            if stint["team"] == row["team"] and stint["first_week"] <= row["week"] <= stint["last_week"]:
                row[stint["role"]] = stint["name"]
    return {(row["game_id"], row["team"]): Staff(*(row.get(role) for role in ROLES)) for row in rows}
