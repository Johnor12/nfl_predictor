# START
# Priors files: priors_<season>.json, stored next to the predictor that samples them.
# - priors_of(file) -> load(season) -> dict: a cached loader for the priors files in `file`'s folder. It
#   returns the latest season's file that isn't after the requested season (the earliest file if there is none).
# - save_priors(priors, file, season) -> Path: writes priors_<season>.json in `file`'s folder.
# END
import json
from functools import lru_cache
from pathlib import Path


def priors_of(file):
    folder = Path(file).resolve().parent

    @lru_cache(maxsize=None)
    def load(season: int) -> dict:
        seasons = [int(path.stem.split("_")[1]) for path in folder.glob("priors_*.json")]
        earlier = [s for s in seasons if s <= season]
        return json.loads((folder / f"priors_{max(earlier) if earlier else min(seasons)}.json").read_text())

    return load


def save_priors(priors: dict, file, season: int) -> Path:
    path = Path(file).resolve().parent / f"priors_{season}.json"
    path.write_text(json.dumps(priors, indent=1, sort_keys=True) + "\n")
    return path
