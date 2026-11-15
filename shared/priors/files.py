# START
# Priors files: priors_<season>.json, stored next to the predictor that samples them. A season's file holds
# the counts of that season's plays week by week ({week: {key: counts}}), and only the keys its data can say.
# - priors_of(file, rules=None, decay=None) -> load(season, week) -> dict: a cached loader for the priors
#   files in `file`'s folder. A game is predicted from what was played before it: the earlier seasons and its
#   own season's earlier weeks. Each top-level key is the sum of their counts, a season counting `decay`
#   times the one after it (DECAY unless given).
#   `rules` ({key: rulebook fields}) keeps a key to the seasons played under the same rules as the game's.
#   A key no earlier season has (the first season of a rule, or of a data source) comes from the whole of the
#   first season that does.
# - DECAY: a season's weight relative to the next one. NFL_PRIORS_DECAY=<decay> overrides it everywhere, to
#   measure another value.
# - save_priors(by_week, file, season) -> Path: writes priors_<season>.json in `file`'s folder, a line per week.
# Internals: _weeks (a cached file), _season (its weeks summed), _pool (the weighted sum of nested counts).
# END
import json
import os
from functools import lru_cache
from pathlib import Path

from shared.rulebook import same_rules

DECAY = 0.5


def _pool(parts):
    """[(counts, weight)] -> their weighted sum, key by key (keys sorted: sampling must not depend on order)."""
    if not isinstance(parts[0][0], dict):
        return sum(value * weight for value, weight in parts)
    keys = sorted({key for counts, _ in parts for key in counts})
    return {key: _pool([(counts[key], weight) for counts, weight in parts if key in counts]) for key in keys}


@lru_cache(maxsize=None)
def _weeks(path) -> dict:
    return {int(week): priors for week, priors in json.loads(path.read_text()).items()}


@lru_cache(maxsize=None)
def _season(path) -> dict:
    return _pool([(priors, 1) for priors in _weeks(path).values()] or [({}, 1)])


def priors_of(file, rules=None, decay=None):
    folder = Path(file).resolve().parent

    @lru_cache(maxsize=None)
    def load(season: int, week: int) -> dict:
        paths = {int(path.stem.split("_")[1]): path for path in folder.glob("priors_*.json")}
        whole = {s: _season(path) for s, path in paths.items()}
        played = [(priors, 1) for w, priors in _weeks(paths[season]).items() if w < week] if season in paths else []
        so_far = _pool(played or [({}, 1)])  # the game's own season, up to its week
        weight = float(os.environ.get("NFL_PRIORS_DECAY", DECAY if decay is None else decay))
        pooled = {}
        for key in sorted({key for priors in whole.values() for key in priors}):
            have = [s for s in sorted(whole) if key in whole[s]]
            same = [s for s in have if same_rules(s, season, (rules or {}).get(key, ()))] or have
            parts = [(whole[s][key], s) for s in same if s < season]
            if not parts:
                parts = [(whole[same[0]][key], same[0])]  # nothing earlier: the first season with it, whole
            elif key in so_far:
                parts.append((so_far[key], season))
            pooled[key] = _pool([(counts, weight ** (parts[-1][1] - s)) for counts, s in parts])
        return pooled

    return load


def save_priors(by_week: dict, file, season: int) -> Path:
    """One line per week, so a rebuild's diff is the weeks that changed."""
    lines = [f'"{week}": {json.dumps(by_week[week], sort_keys=True)}' for week in sorted(by_week)]
    path = Path(file).resolve().parent / f"priors_{season}.json"
    path.write_text("{\n" + ",\n".join(lines) + "\n}\n")
    return path
