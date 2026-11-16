# START
# lines: betting lines, the market's expectations gathered as benchmarks (see README.md).
# - game_lines(season) -> DataFrame: each game's closing spread, total, and moneylines, with prices.
# - player_lines(season, weeks=None, games=None) -> DataFrame: each game's player prop lines (closing and
#   opening), with their prices where the book published them.
# - STATS: the props kept, ESPN's name -> our stat name. COMBINED: the props on a sum of stats.
# - value(stat, line) -> float: a stat's (or a combined stat's) value in a stat line.
# END
from shared.lines.lines import COMBINED, STATS, game_lines, player_lines, value

__all__ = ["game_lines", "player_lines", "STATS", "COMBINED", "value"]
