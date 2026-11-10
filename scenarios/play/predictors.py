# START
# The play's predictors: one function per event, bundled.
# - Predictors: dataclass of event functions, in chain order. Each event's package (events/<event>/) defines
#   its signature and output type. Swap one with dataclasses.replace(predictors, carry=my_carry).
# - load_predictors(default="baseline", **overrides) -> Predictors: each event's implementation by name, from
#   events/<event>/predictors/<name>/ (its `predict`), e.g. load_predictors("baseline", carry="tuned").
# END
import dataclasses
from dataclasses import dataclass
from importlib import import_module
from typing import Callable


@dataclass(frozen=True)
class Predictors:
    lineups: Callable              # (ctx, rng) -> Lineups
    offensive_formation: Callable  # (ctx, lineups, rng) -> Formation
    defensive_formation: Callable  # (ctx, lineups, formation, rng) -> DefensiveFormation
    pre_snap: Callable             # (ctx, lineups, formation, allowed_fouls, rng) -> PreSnap
    snap: Callable                 # (ctx, lineups, formation, defense, allowed_actions, rng) -> Snap
    pass_rush: Callable            # (ctx, lineups, formation, defense, rng) -> PassRush
    target: Callable               # (ctx, lineups, formation, eligible, rng) -> Target
    pass_result: Callable          # (ctx, lineups, target, rng) -> PassResult
    carry: Callable                # (ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd
    loose_ball: Callable           # (ctx, lineups, cause, x, last_team, rng) -> Recovery
    punt_kick: Callable            # (ctx, lineups, punter, rng) -> PuntKick
    punt_result: Callable          # (ctx, lineups, landing_x, allowed, rng) -> PuntResult
    kick_attempt: Callable         # (ctx, lineups, kicker, distance, rng) -> KickAttempt
    free_kick: Callable            # (ctx, lineups, onside, rng) -> FreeKick
    kick_result: Callable          # (ctx, lineups, landing_x, allowed, rng) -> KickResult
    fouls: Callable                # (ctx, lineups, record, allowed_fouls, rng) -> tuple[Foul, ...]
    injuries: Callable             # (ctx, lineups, record, rng) -> tuple[Injury, ...]


def load_predictors(default: str = "baseline", **overrides: str) -> Predictors:
    events = [f.name for f in dataclasses.fields(Predictors)]
    unknown = sorted(set(overrides) - set(events))
    if unknown:
        raise ValueError(f"not play events: {unknown}")
    return Predictors(**{event: import_module(f"events.{event}.predictors.{overrides.get(event, default)}").predict
                         for event in events})
