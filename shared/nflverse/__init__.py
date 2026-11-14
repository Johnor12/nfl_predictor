# START
# nflverse: real NFL data, downloaded and cached locally, and converted into play scenario inputs.
# - load(name, season) -> DataFrame: a cached nflverse file (pbp, ftn, participation, snap_counts, rosters,
#   depth_charts, injuries, player_stats, games); None for a participation file that isn't published.
# - real_plays(season, weeks=None) -> list[RealPlay]: every real play as a PlayContext plus what happened.
# - RealPlay: (context, actual, row) where actual is a dict of the real outcome.
# - real_samples(season, weeks=None) -> iterator of shared.priors.Sample: each real play with its nflverse rows.
# - real_games(season, weeks=None) -> list[RealGame]: every game as a GameContext plus what happened (None
#   if it hasn't been played).
# - STAT_COLUMNS: the play scenario's stat names -> nflverse's player stats columns.
# END
from shared.nflverse.contexts import RealPlay, real_plays, real_samples
from shared.nflverse.download import load
from shared.nflverse.games import STAT_COLUMNS, RealGame, real_games

__all__ = ["load", "real_plays", "real_samples", "RealPlay", "real_games", "RealGame", "STAT_COLUMNS"]
