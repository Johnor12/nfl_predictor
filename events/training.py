# START
# Training tables for model predictors: every real play of a season as one row of an event's inputs and output.
# - table(name, seasons, example, columns) -> DataFrame: `example(sample) -> row | None` (a module-level
#   function) reads one real play (a shared.priors.Sample); None skips it. A season's rows are cached in
#   .cache/training/<name>_<season>.parquet and built in parallel processes where they aren't.
# - train_cli(name, example, columns, train): a train.py's command line: `train(season)` for the season or
#   range of seasons named (`2026`, `2021-2026`; the six most recent without one), their tables built first.
# Internals: _season (one season's rows, from the cache or from its real plays).
# END
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from shared.nflverse import SEASONS, real_samples

CACHE = Path(__file__).resolve().parents[1] / ".cache" / "training"


def _season(name, season, example, columns) -> pd.DataFrame:
    path = CACHE / f"{name}_{season}.parquet"
    if not path.exists():
        rows = [row for row in map(example, real_samples(season)) if row is not None]
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows, columns=list(columns)).astype(float).to_parquet(path)
    return pd.read_parquet(path)


def table(name, seasons, example, columns) -> pd.DataFrame:
    seasons = list(seasons)
    with ProcessPoolExecutor() as pool:
        parts = pool.map(_season, [name] * len(seasons), seasons, [example] * len(seasons), [columns] * len(seasons))
        return pd.concat(parts, ignore_index=True)


def train_cli(name, example, columns, train):
    first, _, last = (sys.argv[1] if len(sys.argv) > 1 else f"{SEASONS[-6]}-{SEASONS[-1]}").partition("-")
    seasons = range(int(first), int(last or first) + 1)
    table(name, [s for s in SEASONS if s < seasons[-1]], example, columns)  # every season's rows, built together
    for season in seasons:
        print(train(season).name)
