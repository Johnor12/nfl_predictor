# START
# The play evaluation report.
# - write_report(evaluation, path=None) -> Path: markdown at evaluation_output/play_<season>.md: the play
#   scenario's scores, each event predictor's scores (in chain order), PIT histograms for the numeric outputs,
#   and reliability for the yes/no and categorical ones.
# END
import dataclasses
from pathlib import Path

from evaluators.scoring import GUIDE, OUT, pit_table, reliability_table, score_table
from scenarios.play import Predictors

EVENTS = [f.name for f in dataclasses.fields(Predictors)]


def write_report(evaluation, path=None) -> Path:
    path = Path(path) if path else OUT / f"play_{evaluation.season}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = evaluation.card.rows()
    play = [r for r in rows if r["name"].startswith("play: ")]
    events = sorted((r for r in rows if not r["name"].startswith("play: ")),
                    key=lambda r: (EVENTS.index(r["name"].split(": ")[0]), r["name"]))
    numeric = [r["name"] for r in play + events if r["kind"] == "numeric"]
    other = [r["name"] for r in play + events if r["kind"] != "numeric"]
    lines = [f"# Play evaluation, {evaluation.season}", "",
             f"- weeks: {', '.join(map(str, evaluation.weeks))}",
             f"- real plays: {evaluation.plays}, each simulated {evaluation.sims} times",
             f"- simulated plays that raised or broke an invariant: {evaluation.failures}", "", *GUIDE,
             "- unscored: real cases left with fewer than 2 samples (for an event, mostly no simulated run sent "
             "out the same unit as the real play, so there was no stand-in for the inputs the data doesn't record).",
             "", "## Play scenario", "", "Every real play's inputs, simulated end to end.", "", *score_table(play),
             "", "## Event predictors", "",
             "Each predictor alone: its real inputs (stand-ins for what the data doesn't record), sampled and "
             "scored against the event's real output.", "", *score_table(events),
             "", "## PIT histograms", "",
             "Where the real outcome fell in the forecast distribution. Calibrated is 10% everywhere; weight at "
             "both ends means the forecast is too narrow, in the middle too wide, at one end biased.", "",
             *pit_table(evaluation.card, numeric),
             "", "## Reliability", "",
             "How often things happened when the forecast gave them that probability (every class of a "
             "categorical output is one forecast). Calibrated when the two percentages match.", "",
             *reliability_table(evaluation.card, other), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
