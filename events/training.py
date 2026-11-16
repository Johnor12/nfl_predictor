# START
# Training tables for model predictors: every real play of a season as one row of an event's inputs and output.
# - table(name, seasons, example, columns) -> DataFrame: `example(sample) -> row | None` (a module-level
#   function) reads one real play (a shared.priors.Sample); None skips it. A season's rows are cached in
#   .cache/training/<name>_<season>.parquet and built where they aren't.
# - build(tables, seasons): builds the missing ones of several tables ({name: (example, columns)}) in one
#   pass over each season's real plays, the seasons in parallel processes. Reading the plays is what costs,
#   so several tables take about as long as one.
# - trainers() -> list of modules: every trained predictor's train.py (events/<event>/predictors/<name>/),
#   each with TABLES ({name: (example, columns)}) and train(season).
# - train_cli(tables, train): a train.py's command line: `train(season)` for the season or range of seasons
#   named (`2026`, `2021-2026`; the six most recent without one), their tables built first.
# - CLI: `python -m events.training [2026 | 2021-2026]` retrains every trained predictor: all their tables in
#   one pass, then every model.
# Internals: _season (one season's missing tables), _seasons (the command line's seasons), WORKERS.
# END
import importlib
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from shared.nflverse import SEASONS, real_samples

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "training"
WORKERS = int(os.environ.get("NFL_TRAINING_WORKERS", 0)) or None  # a season's plays take about 2.5 GB each


def _path(name, season) -> Path:
    return CACHE / f"{name}_{season}.parquet"


def _season(season, tables):
    missing = {name: spec for name, spec in tables.items() if not _path(name, season).exists()}
    if not missing:
        return
    rows = {name: [] for name in missing}
    for sample in real_samples(season):
        for name, (example, _) in missing.items():
            row = example(sample)
            if row is not None:
                rows[name].append(row)
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, (_, columns) in missing.items():
        pd.DataFrame(rows[name], columns=list(columns)).astype(float).to_parquet(_path(name, season))


def build(tables, seasons):
    seasons = list(seasons)
    with ProcessPoolExecutor(WORKERS) as pool:
        list(pool.map(_season, seasons, [tables] * len(seasons)))


def table(name, seasons, example, columns) -> pd.DataFrame:
    seasons = list(seasons)
    build({name: (example, columns)}, seasons)
    return pd.concat([pd.read_parquet(_path(name, season)) for season in seasons], ignore_index=True)


def trainers() -> list:
    paths = sorted((ROOT / "events").glob("*/predictors/*/train.py"))
    return [importlib.import_module(".".join(path.relative_to(ROOT).with_suffix("").parts)) for path in paths]


def _seasons() -> range:
    first, _, last = (sys.argv[1] if len(sys.argv) > 1 else f"{SEASONS[-6]}-{SEASONS[-1]}").partition("-")
    return range(int(first), int(last or first) + 1)


def train_cli(tables, train):
    seasons = _seasons()
    build(tables, [s for s in SEASONS if s < seasons[-1]])  # every season's rows, built together
    for season in seasons:
        print(train(season))


if __name__ == "__main__":
    modules = trainers()
    train_cli({name: spec for module in modules for name, spec in module.TABLES.items()},
              lambda season: [module.train(season) for module in modules])
