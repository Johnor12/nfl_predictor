# START
# lines: betting lines as forecasts (see README.md).
# - lines(season, weeks=None) -> list[Line]: every game line and player prop, with what really happened.
# - Line(market, key, line, p_over, actual): a threshold on a number and the market's probability of going over.
# - score_lines(lines, samples=None) -> list[dict]: the market's scores per market, and a simulator's on the
#   same lines when given its samples ({key: simulated values}).
# - no_vig(odds, other) -> float: a fair probability from a two-way bet's American odds.
# - write_report(season, weeks=None, samples=None, path=None) -> Path: evaluation_output/lines_<season>.md.
# - CLI: `python -m evaluators.lines --season 2026 [--weeks 1-3]`.
# END
from evaluators.lines.lines import Line, lines, no_vig, score_lines
from evaluators.lines.report import write_report

__all__ = ["lines", "Line", "score_lines", "no_vig", "write_report"]
