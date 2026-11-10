# START
# Markdown for a scorecard, shared by the evaluators' reports.
# - OUT: the folder reports are written to (evaluation_output/, gitignored).
# - GUIDE: a few lines on how to read the tables.
# - score_table(rows) -> list[str]: one line per output: n, sims, score, reference, skill, standard errors,
#   and the sims needed to resolve a 1% change.
# - pit_table(card, names) -> list[str]: PIT histograms (share of outcomes per tenth of the forecast range).
# - reliability_table(card, names) -> list[str]: forecast probability vs how often it happened, by bin.
# END
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "evaluation_output"
GUIDE = [
    "How to read this:",
    "- score: the mean fair score over the cases (fair CRPS for numbers, in the output's units; fair Brier "
    "for yes/no and categories). Lower is better.",
    "- reference: the score of forecasting every case with the overall distribution of real outcomes.",
    "- skill: 1 - score / reference. Above 0 beats the reference; 1 is perfect.",
    "- se: standard error of the score over the cases. sim se: the part caused by simulating a finite number "
    "of times.",
    "- sims for 1%: sims per case for a 1% change in the score to stand clear of sim noise (capped at 10,000).",
]


def _num(value, digits=4) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def score_table(rows) -> list[str]:
    lines = ["| output | kind | n | unscored | sims | score | reference | skill | se | sim se | sims for 1% |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        skill = "-" if r["skill"] is None else f"{100 * r['skill']:+.1f}%"
        lines.append(f"| {r['name']} | {r['kind']} | {r['n']} | {r['unscored']} | {_num(r['sims'], 0)} "
                     f"| {_num(r['score'])} | {_num(r['reference'])} | {skill} | {_num(r['se'])} "
                     f"| {_num(r['sim_se'])} | {r['sims_needed'] or '-'} |")
    return lines


def pit_table(card, names) -> list[str]:
    lines = ["| output | " + " | ".join(f"{10 * i}-{10 * i + 10}%" for i in range(10)) + " |", "|---" * 11 + "|"]
    for name in names:
        shares = card.pit(name)
        if shares:
            lines.append(f"| {name} | " + " | ".join(f"{100 * s:.0f}%" for s in shares) + " |")
    return lines


def reliability_table(card, names) -> list[str]:
    lines = ["| output | forecast -> observed (n), by forecast probability |", "|---|---|"]
    for name in names:
        bins = card.reliability(name)
        if bins:
            cells = ", ".join(f"{100 * p:.0f}% -> {100 * observed:.0f}% ({n})" for p, observed, n in bins)
            lines.append(f"| {name} | {cells} |")
    return lines
