# START
# The game's predictors, bundled.
# - GamePredictors(play, toss, timeout): the play scenario's Predictors, the coin toss scenario's
#   TossPredictors, and the timeout event's function.
# - load_game_predictors(default="baseline", **overrides) -> GamePredictors: each event's implementation by
#   name from events/<event>/predictors/<name>/, e.g. load_game_predictors("baseline", timeout="tuned",
#   carry="tuned"). An override is routed to whichever bundle has the event.
# END
import dataclasses
from dataclasses import dataclass
from importlib import import_module
from typing import Callable

from scenarios.coin_toss import TossPredictors, load_toss_predictors
from scenarios.play import Predictors, load_predictors


@dataclass(frozen=True)
class GamePredictors:
    play: Predictors
    toss: TossPredictors
    timeout: Callable              # (ctx, rng) -> Timeout | None; ctx is the next play's PlayContext


def load_game_predictors(default: str = "baseline", **overrides: str) -> GamePredictors:
    play = {f.name for f in dataclasses.fields(Predictors)}
    toss = {f.name for f in dataclasses.fields(TossPredictors)}
    unknown = sorted(set(overrides) - play - toss - {"timeout"})
    if unknown:
        raise ValueError(f"not game events: {unknown}")
    pick = lambda events: {event: name for event, name in overrides.items() if event in events}
    return GamePredictors(load_predictors(default, **pick(play)), load_toss_predictors(default, **pick(toss)),
                          import_module(f"events.timeout.predictors.{overrides.get('timeout', default)}").predict)
