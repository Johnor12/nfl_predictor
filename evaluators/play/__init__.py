# START
# play: scores the play scenario and each of its event predictors against real plays (see README.md).
# - evaluate(season=2026, weeks=None, sims=100, seed=0, predictors=None, workers=None) -> Evaluation.
# - Evaluation: season, weeks, sims, plays, failures, and card (a scoring.Scorecard).
# - write_report(evaluation, path=None) -> Path: evaluation_output/play_<season>.md.
# - CLI: `python -m evaluators.play --season 2026 [--weeks 1-3] [--sims 100] [--swap carry=tuned]`.
# END
from evaluators.play.evaluate import Evaluation, evaluate
from evaluators.play.report import write_report

__all__ = ["evaluate", "Evaluation", "write_report"]
