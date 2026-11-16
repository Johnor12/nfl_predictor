# START
# Rebuilds every event's baseline priors from a season of real plays, in one pass.
# - build(season, weeks=None) -> {event: {week: priors dict}}: feeds each real play (a shared.priors.Sample)
#   to every events/<event>/predictors/baseline/priors.py observe(tally, sample), with a tally per week. A
#   priors.py with an observe_totals(tally, totals) also gets each week's stat lines added up by position
#   group (a shared.priors.Totals): what is only counted per player and game, like the charting.
# - save(season) -> list[Path]: builds and writes each event's priors_<season>.json next to its predictor.
# - CLI: `python -m events.baseline_priors 2026`, or `2011-2026` for a range of seasons (the default), built
#   in parallel processes.
# END
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from importlib import import_module
from pathlib import Path

from shared.nflverse import SEASONS, load, real_samples, stat_lines
from shared.priors import Tally, Totals, save_priors

HERE = Path(__file__).resolve().parent


def _builders() -> dict:
    events = sorted(path.parts[-4] for path in HERE.glob("*/predictors/baseline/priors.py"))
    return {event: import_module(f"events.{event}.predictors.baseline.priors") for event in events}


def _totals(season, weeks) -> dict:
    """{week: Totals}: the season's stat lines added up by week and position group."""
    lines = stat_lines(season)
    groups = load("players").drop_duplicates("gsis_id").set_index("gsis_id").position_group.replace("SPEC", "ST")
    lines = lines.assign(group=lines.player_id.map(groups)).drop(columns=["game_id", "player_id", "team"])
    summed = lines[lines.week.isin(list(weeks))] if weeks is not None else lines
    summed = summed.groupby(["week", "group"]).sum()
    return {week: Totals({name: line.to_dict() for name, line in summed.loc[week].iterrows()})
            for week in summed.index.unique("week")}


def build(season: int, weeks=None) -> dict[str, dict]:
    builders = _builders()
    tallies = {event: defaultdict(Tally) for event in builders}
    for sample in real_samples(season, weeks):
        for event, builder in builders.items():
            builder.observe(tallies[event][sample.context.game.week], sample)
    for week, totals in _totals(season, weeks).items():
        for event, builder in builders.items():
            if hasattr(builder, "observe_totals"):
                builder.observe_totals(tallies[event][int(week)], totals)
    return {event: {week: tally.priors() for week, tally in by_week.items()} for event, by_week in tallies.items()}


def save(season: int) -> list[Path]:
    builders = _builders()
    return [save_priors(by_week, builders[event].__file__, season) for event, by_week in build(season).items()]


if __name__ == "__main__":
    first, _, last = (sys.argv[1] if len(sys.argv) > 1 else f"{SEASONS[0]}-{SEASONS[-1]}").partition("-")
    with ProcessPoolExecutor() as pool:
        for paths in pool.map(save, range(int(first), int(last or first) + 1)):
            print(len(paths), "files:", paths[0].name)
