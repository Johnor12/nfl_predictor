# START
# game: scores the game scenario against real games and betting lines (see README.md).
# - evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None,
#   lines=()) -> Evaluation.
# - evaluate_games(games, sims, seed, predictors, workers, lines) -> (card, samples, failures): the same for
#   a list of games with real outcomes.
# - game_outputs(ctx, outcome) -> {(name, subject): value}: the scored outputs of a real or simulated game.
# - Evaluation: seasons, sims, games, failures, card (a scoring.Scorecard), lines, samples.
# - write_report(evaluation, path=None) -> Path: evaluation_output/game_<seasons>.md.
# - CLI: `python -m evaluators.game [--seasons 2021-2026] [--games 160] [--sims 100] [--swap carry=tuned]
#   [--no-lines]`.
# END
from evaluators.game.evaluate import Evaluation, evaluate, evaluate_games, game_outputs
from evaluators.game.report import write_report

__all__ = ["evaluate", "evaluate_games", "game_outputs", "Evaluation", "write_report"]
