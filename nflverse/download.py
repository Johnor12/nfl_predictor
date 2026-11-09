# START
# Downloading and caching nflverse files under .cache/nflverse/ (gitignored).
# - load(name, season=None, refresh=False) -> DataFrame: read a cached file, downloading it first if missing.
# - FILES: the nflverse release files we use, by name. "games" is the schedule (with referees, weather,
#   coaches, and betting lines) from the nfldata repo and covers all seasons.
# END
import urllib.request
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "nflverse"
RELEASES = "https://github.com/nflverse/nflverse-data/releases/download/"
FILES = {
    "pbp": RELEASES + "pbp/play_by_play_{season}.parquet",
    "ftn": RELEASES + "ftn_charting/ftn_charting_{season}.parquet",
    "rosters": RELEASES + "weekly_rosters/roster_weekly_{season}.parquet",
    "depth_charts": RELEASES + "depth_charts/depth_charts_{season}.parquet",
    "injuries": RELEASES + "injuries/injuries_{season}.parquet",
    "games": "https://github.com/nflverse/nfldata/raw/master/data/games.csv",
}


def load(name: str, season: int | None = None, refresh: bool = False) -> pd.DataFrame:
    url = FILES[name].format(season=season)
    path = CACHE / url.rsplit("/", 1)[1]
    if refresh or not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "nfl-predictor"})
        with urllib.request.urlopen(request) as response:
            path.write_bytes(response.read())
    frame = pd.read_csv(path) if path.suffix == ".csv" else pd.read_parquet(path)
    if name == "games" and season is not None:
        frame = frame[frame.season == season]
    return frame
