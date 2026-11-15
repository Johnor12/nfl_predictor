# START
# Training tables for model predictors: every real play of a season as one row of an event's inputs and output.
# - table(name, seasons, example, columns) -> DataFrame: `example(sample) -> row | None` (a module-level
#   function) reads one real play (a shared.priors.Sample); None skips it. A season's rows are cached in
#   .cache/training/<name>_<season>.parquet and built in parallel processes where they aren't.
# Internals: _season (one season's rows, from the cache or from its real plays).
# END
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from shared.nflverse import real_samples

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
