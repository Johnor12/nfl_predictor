# START
# Downloading and caching nflverse files under .cache/nflverse/ (gitignored).
# - load(name, season=None, refresh=False) -> DataFrame: read a cached file, downloading it first if missing.
#   None for a file in OPTIONAL that nflverse hasn't published for the season (remembered in a .missing
#   file next to the cache, so it is only asked for again with refresh=True).
# - FILES: the nflverse release files we use, by name. "games" is the schedule (with referees, weather,
#   coaches, and betting lines) from the nfldata repo and covers all seasons. "player_stats" is every
#   player's stat line per game. "participation" is who was on the field for each play, with the personnel
#   groups and formation (published after the season). "snap_counts" is each player's snaps per game.
# END
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
    "games": "https://github.com/nflverse/nfldata/raw/master/data/games.csv",
}
OPTIONAL = ("participation",)


def load(name: str, season: int | None = None, refresh: bool = False) -> pd.DataFrame | None:
    url = FILES[name].format(season=season)
    path = CACHE / url.rsplit("/", 1)[1]
    missing = path.with_suffix(".missing")
    if missing.exists() and not refresh:
        return None
    if refresh or not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "nfl-predictor"})
        try:
            with urllib.request.urlopen(request) as response:
                path.write_bytes(response.read())
        except urllib.error.HTTPError as error:
            if name not in OPTIONAL or error.code != 404:
                raise
            missing.touch()
            return None
        missing.unlink(missing_ok=True)
    frame = pd.read_csv(path) if path.suffix == ".csv" else pd.read_parquet(path)
    if name == "games" and season is not None:
        frame = frame[frame.season == season]
    return frame
