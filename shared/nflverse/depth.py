# START
# Depth charts in one shape for every season.
# - depth_charts(season) -> DataFrame: team, dt (when the chart was published, sortable against a game's
#   date), gsis_id, pos_abb (the slot, in the names nflverse uses from 2025 on), pos_rank.
# From 2025 on nflverse publishes dated snapshots. Before that it has one chart per team and week, with the
# teams' own slot names: it is dated the day before the week's first game, and SLOTS renames the common
# slots (a name it doesn't list is kept, and only matters to code that asks for that slot).
# END
import pandas as pd

from shared.nflverse.download import load

COLUMNS = ["team", "dt", "gsis_id", "pos_abb", "pos_rank"]
SLOTS = {
    "K": "PK", "KOR": "KR", "HB": "RB", "CB": "LCB", "NCB": "NB", "S": "SS", "DE": "LDE", "LE": "LDE", "RE": "RDE",
    "EDGE": "LDE", "RUSH": "RDE", "DT": "LDT", "OLB": "SLB", "LOLB": "SLB", "ROLB": "WLB", "SAM": "SLB",
    "WILL": "WLB", "ILB": "MLB", "MIKE": "MLB",
}


def depth_charts(season: int) -> pd.DataFrame:
    depth = load("depth_charts", season)
    if "dt" in depth.columns:
        return depth[depth.dt >= f"{season}-08-01"][COLUMNS]
    first_game = pd.to_datetime(load("games", season).groupby(["week", "game_type"]).gameday.min())
    published = (first_game - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d").rename("dt").reset_index()
    depth = depth.merge(published, on=["week", "game_type"])  # drops the charts that aren't for a game week
    return depth.assign(team=depth.club_code, pos_abb=depth.depth_position.str.strip().replace(SLOTS),
                        pos_rank=depth.depth_team.astype(int))[COLUMNS]
