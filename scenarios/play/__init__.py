# START
# The play scenario's public API.
# - run_play(ctx, predictors, rng) -> PlayResult: simulate one play.
# - validate_play(result) -> list[str]: broken invariants (empty if valid).
# - describe_play(result) -> str / describe_situation(situation) -> str: narration.
# - validate_context(ctx) -> list[str]: problems with an input.
# - Inputs: PlayContext, Game, Player, Situation, PlaySummary. Predictor interface: Predictors and the
#   event output types in events.py. Errors: IllegalChoice (a predictor broke the rules).
# - Helpers for predictors: rel/to_x (team yard lines), eligible_receivers, allowed_units, CATALOG (fouls).
# END
from scenarios.play.chain import IllegalChoice, allowed_units, run_play
from scenarios.play.context import FREE_KICKS, Game, PlayContext, PlaySummary, Player, Situation, validate_context
from scenarios.play.describe import describe_play, describe_situation
from scenarios.play.events import Predictors
from scenarios.play.field import eligible_receivers, rel, to_x
from scenarios.play.fouls import CATALOG
from scenarios.play.record import PlayResult
from scenarios.play.validate import validate_play

__all__ = [
    "run_play", "validate_play", "describe_play", "describe_situation", "validate_context", "IllegalChoice",
    "PlayContext", "Game", "Player", "Situation", "PlaySummary", "Predictors", "PlayResult", "FREE_KICKS",
    "allowed_units", "eligible_receivers", "rel", "to_x", "CATALOG",
]
