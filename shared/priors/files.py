# START
# Priors files: priors_<season>.json, stored next to the predictor that samples them.
# - priors_of(file) -> load(season) -> dict: a cached loader for the priors files in `file`'s folder. Each
#   top-level key comes from the latest season's file that has it and isn't after the requested season (the
#   earliest file if all are later). So a season's file only holds what that season's data can say, and a
#   predictor still gets the rest (2025's on-field personnel when predicting 2026).
# - THROUGH: the environment variable NFL_PRIORS_THROUGH=<season> ignores the files of later seasons, for an
#   out-of-sample check (2026's plays scored with priors that have never seen them).
# - save_priors(priors, file, season) -> Path: writes priors_<season>.json in `file`'s folder.
# END
import json
import os
from functools import lru_cache
from pathlib import Path

THROUGH = "NFL_PRIORS_THROUGH"


def priors_of(file):
    folder = Path(file).resolve().parent

    @lru_cache(maxsize=None)
    def load(season: int) -> dict:
        files = {int(path.stem.split("_")[1]): path for path in folder.glob("priors_*.json")}
        latest = min(season, int(os.environ.get(THROUGH, season)))
        merged = {}
        for s in [s for s in sorted(files) if s <= latest] or [min(files)]:
            merged.update(json.loads(files[s].read_text()))
        return merged

    return load


def save_priors(priors: dict, file, season: int) -> Path:
    path = Path(file).resolve().parent / f"priors_{season}.json"
    path.write_text(json.dumps(priors, indent=1, sort_keys=True) + "\n")
    return path
