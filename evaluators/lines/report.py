# START
# The betting lines report.
# - write_report(games, samples=None, path=None) -> Path: markdown at
#   evaluation_output/lines_<seasons>.md, for the games given as {season: [game id]}: how the market's lines scored against what happened (the accuracy a
#   simulator is aiming for), the moneyline's reliability, and, given a simulator's samples, its scores on
#   the same lines.
# - lines_table(rows) -> list[str]: score_lines' rows as a markdown table (the sim columns when they are there).
# END
from pathlib import Path

from evaluators.sample import label
from evaluators.lines.lines import favorites, lines, score_lines
from evaluators.scoring import OUT, reliability

COLUMNS = [("market", "market"), ("n", "n"), ("went over", "over"), ("Brier", "brier"), ("log loss", "log_loss"),
           ("MAE", "mae"), ("sim Brier", "sim_brier"), ("sim log loss", "sim_log_loss"), ("sim MAE", "sim_mae"),
           ("sim CRPS", "sim_crps")]


def _cell(key, value) -> str:
    if value is None:
        return "-"
    return str(value) if key in ("market", "n") else f"{100 * value:.1f}%" if key == "over" else f"{value:.3f}"


def lines_table(rows) -> list[str]:
    columns = [(title, key) for title, key in COLUMNS if rows and key in rows[0]]
    return ["| " + " | ".join(title for title, _ in columns) + " |", "|---" * len(columns) + "|",
            *("| " + " | ".join(_cell(key, row[key]) for _, key in columns) + " |" for row in rows)]


def write_report(games, samples=None, path=None) -> Path:
    seasons = label(games)
    path = Path(path) if path else OUT / f"lines_{seasons}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    every = lines(games)
    text = [f"# Betting lines, {seasons}", "",
            f"- games: {sum(map(len, games.values()))}",
            f"- lines: {len(every)} ({sum(l.actual is not None for l in every)} with a result)",
            "- moneyline: the home team to win. spread: the home team to beat the spread. total: over. A player "
            "stat: over. Player props are scored at 50%, because their prices aren't published.",
            "- Brier and log loss score the market's probability of going over (lower is better; a coin flip "
            "scores 0.250 and 0.693). MAE is the line's error as a forecast of the number itself.",
            "- sim columns: the simulator's scores on the same lines.", "", *lines_table(score_lines(every, samples))]
    text += ["", "## Moneyline reliability", "",
             "The favorite's probability against how often the favorite won.", "",
             "| favorite's probability | won | games |", "|---|---|---|"]
    text += [f"| {100 * p:.0f}% | {100 * won:.0f}% | {n} |" for p, won, n in reliability(favorites(every))]
    path.write_text("\n".join(text) + "\n", encoding="utf-8")
    return path
