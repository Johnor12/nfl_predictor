# START
# Which games an evaluation covers; shared by the evaluators' CLIs and evaluate functions.
# - EVALUATED: the seasons an evaluation covers by default: the six most recent.
# - sample_games(seasons, weeks=None, n=None) -> {season: [game id]}: the played games of the seasons (and
#   weeks): those with a result and stat lines, so a game just played waits for its box score and charting
#   (shared.nflverse.stat_lines) rather than being scored against none. With n, a sample of n of them:
#   always the same games, and a larger sample contains a smaller one, so two evaluations compare on the
#   same cases.
# - label(seasons) -> str: "2026" or "2021-2026", for report titles and file names.
# END
import random

from shared.nflverse import SEASONS, load, stat_lines

EVALUATED = SEASONS[-6:]


def sample_games(seasons, weeks=None, n=None) -> dict[int, list[str]]:
    played = []
    for season in seasons:
        schedule = load("games", season)
        assert schedule is not None  # the schedule covers every season
        schedule = schedule[schedule.result.notna() & schedule.game_id.isin(stat_lines(season).game_id)]
        if weeks is not None:
            schedule = schedule[schedule.week.isin(list(weeks))]
        played += [(season, game_id) for game_id in schedule.game_id]
    if n is not None:
        random.Random(0).shuffle(played)
        played = sorted(played[:n])
    sample = {}
    for season, game_id in played:
        sample.setdefault(season, []).append(game_id)
    return sample


def label(seasons) -> str:
    seasons = sorted(seasons)
    return str(seasons[0]) if len(seasons) == 1 else f"{seasons[0]}-{seasons[-1]}"
