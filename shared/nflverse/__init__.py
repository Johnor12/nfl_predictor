# START
# nflverse: real NFL data, downloaded and cached locally, and converted into play scenario inputs.
# - load(name, season) -> DataFrame: a cached nflverse file (pbp, ftn, participation, snap_counts, rosters,
#   depth_charts, injuries, player_stats, pfr_def/pass/rush/rec, players, games); None for a file nflverse
#   hasn't published for the season.
# - real_plays(season, weeks=None) -> list[RealPlay]: every real play as a PlayContext plus what happened.
# - RealPlay: (context, actual, row) where actual is a dict of the real outcome.
# - real_samples(season, weeks=None) -> iterator of shared.priors.Sample: each real play with its nflverse rows.
# - real_games(season, weeks=None) -> list[RealGame]: every game as a GameContext plus what happened (None
#   if it hasn't been played).
# - stat_lines(season) -> DataFrame: what every player did in every game (game_id, week, player_id, team, and a
#   column per stat): the box score (STAT_COLUMNS) and, from 2018 on, what PFR charted (CHARTED).
# - STAT_COLUMNS: the play scenario's stat names -> the nflverse player stats columns they are the sum of.
# - ON_FIELD: the stats of a team's plays that are also counted for each player on the field (Player.stats'
#   on_<stat> and on_allowed_<stat>).
# - TEAM_STATS: the stats in a team's, coach's, or referee's form (Game.forms).
# - SEASONS: the seasons the system covers (2011 on).
# END
from shared.nflverse.contexts import RealPlay, real_plays, real_samples
from shared.nflverse.download import SEASONS, load
from shared.nflverse.form import ON_FIELD, TEAM_STATS
from shared.nflverse.games import RealGame, real_games
from shared.nflverse.stat_lines import CHARTED, STAT_COLUMNS, stat_lines

__all__ = ["SEASONS", "load", "real_plays", "real_samples", "RealPlay", "real_games", "RealGame", "stat_lines",
           "STAT_COLUMNS", "CHARTED", "ON_FIELD", "TEAM_STATS"]
