# START
# nflverse: real NFL data, downloaded and cached locally, and converted into play scenario inputs.
# - load(name, season) -> DataFrame: a cached nflverse file (pbp, ftn, rosters, depth_charts, injuries,
#   player_stats, games).
# - real_plays(season, weeks=None) -> list[RealPlay]: every real play as a PlayContext plus what happened.
# - RealPlay: (context, actual, row) where actual is a dict of the real outcome.
# - real_samples(season, weeks=None) -> iterator of shared.priors.Sample: each real play with its nflverse rows.
# END
from shared.nflverse.contexts import RealPlay, real_plays, real_samples
from shared.nflverse.download import load

__all__ = ["load", "real_plays", "real_samples", "RealPlay"]
