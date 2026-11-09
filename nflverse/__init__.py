# START
# nflverse: real NFL data, downloaded and cached locally, and converted into play scenario inputs.
# - load(name, season) -> DataFrame: a cached nflverse file (pbp, ftn, rosters, depth_charts, injuries, games).
# - real_plays(season, weeks=None) -> list[RealPlay]: every real play as a PlayContext plus what happened.
# - RealPlay: (context, actual, row) where actual is a dict of the real outcome.
# END
from nflverse.contexts import RealPlay, real_plays
from nflverse.download import load

__all__ = ["load", "real_plays", "RealPlay"]
