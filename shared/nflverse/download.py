# START
# Downloading and caching nflverse files under .cache/nflverse/ (gitignored).
# - load(name, season=None, refresh=False) -> DataFrame: read a cached file, downloading it first if missing
#   or stale. None for a file in OPTIONAL that nflverse hasn't published for the season (remembered in a
#   .missing file next to the cache). Team codes are the current ones in every file and season (TEAMS: the
#   2016 Raiders are LV, as in the play-by-play).
#   Stale: a file that can still change (the current season's, or one covering every season: "games",
#   "players") downloaded more than MAX_AGE ago, and its .missing marker the same. A past season's file is
#   only downloaded again with refresh=True. If a refresh fails (offline), the cached copy is used, and the
#   next process tries again.
# - SEASONS: the seasons the system covers.
# - FILES: the nflverse release files we use, by name. "games" is the schedule (with referees, weather,
#   coaches, and betting lines) from the nfldata repo and covers all seasons. "player_stats" is every
#   player's stat line per game. "participation" is who was on the field for each play, with the personnel
#   groups and formation (2016 on, published after the season). "snap_counts" is each player's snaps per
#   game (2013 on). "ftn" is charting (2022 on). "depth_charts" changed format in 2025 (see depth.py).
#   "pfr_def", "pfr_pass", "pfr_rush", and "pfr_rec" are Pro Football Reference's charting of each player's
#   game (2018 on): pressures, missed tackles, what a defender allowed in coverage, drops, yards after
#   contact. "players" is one row per player with his ids in every system (gsis, pfr, espn, pff) and covers
#   all seasons.
# END
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "nflverse"
RELEASES = "https://github.com/nflverse/nflverse-data/releases/download/"
FILES = {
    "pbp": RELEASES + "pbp/play_by_play_{season}.parquet",
    "ftn": RELEASES + "ftn_charting/ftn_charting_{season}.parquet",
    "participation": RELEASES + "pbp_participation/pbp_participation_{season}.parquet",
    "snap_counts": RELEASES + "snap_counts/snap_counts_{season}.parquet",
    "rosters": RELEASES + "weekly_rosters/roster_weekly_{season}.parquet",
    "depth_charts": RELEASES + "depth_charts/depth_charts_{season}.parquet",
    "injuries": RELEASES + "injuries/injuries_{season}.parquet",
    "player_stats": RELEASES + "stats_player/stats_player_week_{season}.parquet",
    "pfr_def": RELEASES + "pfr_advstats/advstats_week_def_{season}.parquet",
    "pfr_pass": RELEASES + "pfr_advstats/advstats_week_pass_{season}.parquet",
    "pfr_rush": RELEASES + "pfr_advstats/advstats_week_rush_{season}.parquet",
    "pfr_rec": RELEASES + "pfr_advstats/advstats_week_rec_{season}.parquet",
    "players": RELEASES + "players/players.parquet",
    "games": "https://github.com/nflverse/nfldata/raw/master/data/games.csv",
}
SEASONS = range(2011, 2027)  # the first season the rulebook covers through the current one
OPTIONAL = ("participation", "ftn", "snap_counts", "pfr_def", "pfr_pass", "pfr_rush", "pfr_rec")
TEAMS = {"OAK": "LV", "SD": "LAC", "STL": "LA", "SL": "LA", "ARZ": "ARI", "BLT": "BAL", "CLV": "CLE", "HST": "HOU"}
TEAM_COLUMNS = ("team", "club_code", "home_team", "away_team", "opponent")
MAX_AGE = 6 * 3600  # seconds before a file that can still change is downloaded again
_FAILED = set()  # files whose refresh failed in this process: their cached copy is used until the next one


def load(name: str, season: int | None = None, refresh: bool = False) -> pd.DataFrame | None:
    url = FILES[name].format(season=season)
    path = CACHE / url.rsplit("/", 1)[1]
    missing = path.with_suffix(".missing")
    cached = path if path.exists() else missing if missing.exists() else None
    live = "{season}" not in FILES[name] or season == SEASONS[-1]
    stale = cached is not None and live and time.time() - cached.stat().st_mtime > MAX_AGE
    if refresh or cached is None or (stale and path not in _FAILED):
        _download(name, url, path, missing, cached)
    if missing.exists():
        return None
    frame = pd.read_csv(path) if path.suffix == ".csv" else pd.read_parquet(path)
    if name == "games" and season is not None:
        frame = frame[frame.season == season]
    columns = [column for column in TEAM_COLUMNS if column in frame.columns]
    return frame.assign(**{column: frame[column].replace(TEAMS) for column in columns})


def _download(name, url, path, missing, cached):
    request = urllib.request.Request(url, headers={"User-Agent": "nfl-predictor"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
    except OSError as error:  # HTTPError and URLError are OSErrors
        if name in OPTIONAL and getattr(error, "code", None) == 404 and not path.exists():
            CACHE.mkdir(parents=True, exist_ok=True)
            missing.touch()
            return
        if cached is None:
            raise
        print(f"nflverse: couldn't refresh {path.name} ({error}); using the cached copy", file=sys.stderr)
        _FAILED.add(path)
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.{os.getpid()}.part")  # other processes may be reading the file
    partial.write_bytes(data)
    os.replace(partial, path)
    missing.unlink(missing_ok=True)
