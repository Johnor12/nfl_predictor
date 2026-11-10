# START
# The play scenario's public API.
# - run_play(ctx, predictors, rng) -> PlayResult: simulate one play.
# - validate_play(result) -> list[str]: broken invariants (empty if valid).
# - describe_play(result) -> str / describe_situation(situation) -> str: narration.
# - validate_context(ctx) -> list[str]: problems with an input.
# - Inputs: PlayContext, Game, Player, Situation, PlaySummary. Errors: IllegalChoice (a predictor broke the rules).
# - Predictors: Predictors (one function per event) and load_predictors (each event's implementation by name).
# - Output: PlayResult; the facts in its record: Sack, Pass, Carry, LooseBall, Kick, read with facts(record, type).
# - Helpers for predictors: rel/to_x (team yard lines), eligible_receivers, field_goal_distance, allowed_units,
#   FREE_KICKS, CATALOG (fouls).
# END
from scenarios.play.chain import IllegalChoice, allowed_units, run_play
from scenarios.play.context import FREE_KICKS, Game, PlayContext, PlaySummary, Player, Situation, validate_context
from scenarios.play.describe import describe_play, describe_situation
from scenarios.play.field import eligible_receivers, field_goal_distance, rel, to_x
from scenarios.play.penalties import CATALOG
from scenarios.play.predictors import Predictors, load_predictors
from scenarios.play.record import Carry, Kick, LooseBall, Pass, PlayResult, Sack, facts
from scenarios.play.validate import validate_play

__all__ = [
    "run_play", "validate_play", "describe_play", "describe_situation", "validate_context", "IllegalChoice",
    "PlayContext", "Game", "Player", "Situation", "PlaySummary", "Predictors", "load_predictors",
    "PlayResult", "Sack", "Pass", "Carry", "LooseBall", "Kick", "facts",
    "rel", "to_x", "eligible_receivers", "field_goal_distance", "allowed_units", "FREE_KICKS", "CATALOG",
]
