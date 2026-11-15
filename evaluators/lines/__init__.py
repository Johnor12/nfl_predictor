# START
# lines: betting lines as forecasts (see README.md).
# - lines(games) -> list[Line]: every game line and player prop of the games ({season: [game id]}, from
#   evaluators.sample.sample_games), with what really happened.
# - Line(market, key, line, p_over, actual): a threshold on a number and the market's probability of going over.
# - score_lines(lines, samples=None) -> list[dict]: the market's scores per market, and a simulator's on the
#   same lines when given its samples ({key: simulated values}).
# - no_vig(odds, other) -> float: a fair probability from a two-way bet's American odds.
# - write_report(games, samples=None, path=None) -> Path: evaluation_output/lines_<seasons>.md.
# - lines_table(rows) -> list[str]: score_lines' rows as a markdown table, for other reports.
# - CLI: `python -m evaluators.lines [--seasons 2021-2026] [--games 160]`.
# END
from evaluators.lines.lines import Line, lines, no_vig, score_lines
from evaluators.lines.report import lines_table, write_report

__all__ = ["lines", "Line", "score_lines", "no_vig", "write_report", "lines_table"]
