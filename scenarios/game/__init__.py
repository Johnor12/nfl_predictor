# START
# The game scenario's public API.
# - run_game(ctx, predictors, rng) -> GameResult: simulate one game.
# - validate_game(result, plays=True) -> list[str]: broken invariants (empty if valid).
# - describe_game(result, plays=False) -> str: a box score, and the whole timeline with plays=True.
# - validate_game_context(ctx) -> list[str]: problems with an input.
# - Input: GameContext(game, players). Predictors: GamePredictors and load_game_predictors.
# - Output: GameResult; the entries in its record besides PlayResults: Toss (from the coin toss scenario) and
#   Stoppage.
# END
from scenarios.coin_toss import Toss
from scenarios.game.context import GameContext, validate_game_context
from scenarios.game.describe import describe_game
from scenarios.game.game import run_game
from scenarios.game.predictors import GamePredictors, load_game_predictors
from scenarios.game.record import GameResult, Stoppage
from scenarios.game.validate import validate_game

__all__ = ["run_game", "validate_game", "describe_game", "validate_game_context", "GameContext",
           "GamePredictors", "load_game_predictors", "GameResult", "Stoppage", "Toss"]
