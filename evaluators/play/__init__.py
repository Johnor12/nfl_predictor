# START
# play: scores the play scenario and each of its event predictors against real plays (see README.md).
# - evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None) ->
#   Evaluation.
# - Evaluation: seasons, games, sims, plays, failures, and card (a scoring.Scorecard).
# - write_report(evaluation, path=None) -> Path: evaluation_output/play_<seasons>.md.
# - CLI: `python -m evaluators.play [--seasons 2021-2026] [--games 160] [--sims 100] [--swap carry=tuned]`.
# END
from evaluators.play.evaluate import Evaluation, evaluate
from evaluators.play.report import write_report

__all__ = ["evaluate", "Evaluation", "write_report"]
