# START
# Rebuilds every event's baseline priors from a season of real plays, in one pass.
# - build(season, weeks=None) -> {event: priors dict}: feeds each real play (a shared.priors.Sample) to
#   every events/<event>/predictors/baseline/priors.py observe(tally, sample).
# - save(season) -> list[Path]: builds and writes each event's priors_<season>.json next to its predictor.
# - CLI: `python -m events.baseline_priors 2026`.
# END
import sys
from importlib import import_module
from pathlib import Path

from shared.nflverse import real_samples
from shared.priors import Tally, save_priors

HERE = Path(__file__).resolve().parent


def _builders() -> dict:
    events = sorted(path.parts[-4] for path in HERE.glob("*/predictors/baseline/priors.py"))
    return {event: import_module(f"events.{event}.predictors.baseline.priors") for event in events}


def build(season: int, weeks=None) -> dict[str, dict]:
    builders = _builders()
    tallies = {event: Tally() for event in builders}
    for sample in real_samples(season, weeks):
        for event, builder in builders.items():
            builder.observe(tallies[event], sample)
    return {event: tally.priors() for event, tally in tallies.items()}


def save(season: int) -> list[Path]:
    builders = _builders()
    return [save_priors(priors, builders[event].__file__, season) for event, priors in build(season).items()]


if __name__ == "__main__":
    for path in save(int(sys.argv[1]) if len(sys.argv) > 1 else 2026):
        print(path)
