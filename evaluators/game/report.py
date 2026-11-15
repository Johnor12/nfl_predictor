# START
# The game evaluation report.
# - write_report(evaluation, path=None) -> Path: markdown at evaluation_output/game_<seasons>.md: the game
#   scenario's scores (game, team, and player outputs), the timeout predictor's, the betting lines scored for
#   the market and for the simulator (when the evaluation was given lines), PIT histograms for the numeric
#   outputs, and reliability for the yes/no and categorical ones.
# END
from pathlib import Path

from evaluators.sample import label
from evaluators.game.evaluate import PLAYER_STATS
from evaluators.lines import lines_table, score_lines
from evaluators.scoring import GUIDE, OUT, pit_table, reliability_table, score_table

LEVELS = ("game", "team", "player")


def write_report(evaluation, path=None) -> Path:
    seasons = label(evaluation.seasons)
    path = Path(path) if path else OUT / f"game_{seasons}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = evaluation.card.rows()
    level = lambda row: row["name"].split(": ")[0]
    role = lambda row: next((i for i, name in enumerate(PLAYER_STATS) if row["name"].endswith(f"({name})")), 0)
    scenario = sorted((r for r in rows if level(r) in LEVELS), key=lambda r: (LEVELS.index(level(r)), role(r)))
    events = [r for r in rows if level(r) not in LEVELS]
    numeric = [r["name"] for r in scenario + events if r["kind"] == "numeric"]
    other = [r["name"] for r in scenario + events if r["kind"] != "numeric"]
    lines = [f"# Game evaluation, {seasons}", "",
             f"- real games: {evaluation.games}, each simulated {evaluation.sims} times from its inputs at kickoff",
             f"- simulated games that raised or broke an invariant: {evaluation.failures}", "", *GUIDE,
             "", "## Game scenario", "",
             "game: one case per game (margin is home minus away). team: one per team and game. player: one per "
             "active player with that depth chart role and game (a 3 means third or lower), whether or not he "
             "played.", "", *score_table(scenario),
             "", "## Event predictors", "",
             "The timeout predictor alone, sampled on every real play's situation as it stood before any timeout. "
             "The coin toss isn't in the data, so its predictors aren't scored.", "", *score_table(events)]
    if evaluation.lines:
        lines += ["", "## Betting lines", "",
                  "The market's lines scored against what happened, and the simulator on the same lines. Brier and "
                  "log loss score the probability of going over (moneyline: the home team wins; a player prop's "
                  "market probability is 50%, because prices aren't published); MAE is the line's (or the "
                  "simulated median's) error. Lower is better.", "",
                  *lines_table(score_lines(evaluation.lines, evaluation.samples))]
    lines += ["", "## PIT histograms", "",
              "Where the real outcome fell in the forecast distribution. Calibrated is 10% everywhere; weight at "
              "both ends means the forecast is too narrow, in the middle too wide, at one end biased.", "",
              *pit_table(evaluation.card, numeric),
              "", "## Reliability", "",
              "How often things happened when the forecast gave them that probability. Calibrated when the two "
              "percentages match.", "", *reliability_table(evaluation.card, other), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
