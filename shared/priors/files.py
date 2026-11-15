# START
# Priors files: priors_<season>.json, stored next to the predictor that samples them. A season's file holds
# the counts of that season's plays, and only the keys its data can say.
# - priors_of(file, rules=None, decay=None) -> load(season) -> dict: a cached loader for the priors files in
#   `file`'s folder. A game is predicted from the seasons before its own: each top-level key is the sum of
#   those seasons' counts, a season counting `decay` times the one after it (DECAY unless given).
#   `rules` ({key: rulebook fields}) keeps a key to the seasons played under the same rules as the game's.
#   A key no earlier season has (the first season of a rule, or of a data source) comes from the first
#   season that does.
# - THROUGH: the environment variable NFL_PRIORS_THROUGH=<season> pools the seasons through that one instead
#   of through the season before the game's (2026, to forecast an upcoming 2026 game with this season's
#   games; an earlier season, to hold data back).
# - DECAY: a season's weight relative to the next one. NFL_PRIORS_DECAY=<decay> overrides it everywhere, to
#   measure another value.
# - save_priors(priors, file, season) -> Path: writes priors_<season>.json in `file`'s folder.
# Internals: _read (a cached file), _pool (the weighted sum of nested counts).
# END
import json
import os
from functools import lru_cache
from pathlib import Path

from shared.rulebook import same_rules

THROUGH = "NFL_PRIORS_THROUGH"
DECAY = 0.5


@lru_cache(maxsize=None)
def _read(path) -> dict:
    return json.loads(path.read_text())


def _pool(parts):
    """[(counts, weight)] -> their weighted sum, key by key (keys sorted: sampling must not depend on order)."""
    if not isinstance(parts[0][0], dict):
        return sum(value * weight for value, weight in parts)
    keys = sorted({key for counts, _ in parts for key in counts})
    return {key: _pool([(counts[key], weight) for counts, weight in parts if key in counts]) for key in keys}


def priors_of(file, rules=None, decay=None):
    folder = Path(file).resolve().parent

    @lru_cache(maxsize=None)
    def load(season: int) -> dict:
        files = {int(path.stem.split("_")[1]): _read(path) for path in folder.glob("priors_*.json")}
        through = int(os.environ.get(THROUGH, season - 1))
        weight = float(os.environ.get("NFL_PRIORS_DECAY", DECAY if decay is None else decay))
        pooled = {}
        for key in sorted({key for priors in files.values() for key in priors}):
            have = [s for s in sorted(files) if key in files[s]]
            same = [s for s in have if same_rules(s, season, (rules or {}).get(key, ()))] or have
            seasons = [s for s in same if s <= through] or same[:1]
            pooled[key] = _pool([(files[s][key], weight ** (seasons[-1] - s)) for s in seasons])
        return pooled

    return load


def save_priors(priors: dict, file, season: int) -> Path:
    path = Path(file).resolve().parent / f"priors_{season}.json"
    path.write_text(json.dumps(priors, indent=1, sort_keys=True) + "\n")
    return path
