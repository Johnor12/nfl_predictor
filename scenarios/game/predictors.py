# START
# The game's predictors, bundled.
# - GamePredictors(play, toss, timeout, challenge): the play scenario's Predictors, the coin toss scenario's
#   TossPredictors, and the timeout and challenge events' functions (GAME_EVENTS).
# - load_game_predictors(default=None, **overrides) -> GamePredictors: each event's default implementation
#   (events.predictor), or the one named `default` for every event; an override names one event's, e.g.
#   load_game_predictors(timeout="tuned", carry="tuned"), and is routed to whichever bundle has the event.
# END
import dataclasses
from dataclasses import dataclass
from typing import Callable

from events import predictor
from scenarios.coin_toss import TossPredictors, load_toss_predictors
from scenarios.play import Predictors, load_predictors


@dataclass(frozen=True)
class GamePredictors:
    play: Predictors
    toss: TossPredictors
    timeout: Callable              # (ctx, called, rng) -> Timeout | None; ctx is the next play's PlayContext
    challenge: Callable            # (ctx, outcome, allowed, rng) -> Challenge | None; ctx is the last play's


GAME_EVENTS = ("timeout", "challenge")  # the game scenario's own events


def load_game_predictors(default: str | None = None, **overrides: str) -> GamePredictors:
    play = {f.name for f in dataclasses.fields(Predictors)}
    toss = {f.name for f in dataclasses.fields(TossPredictors)}
    unknown = sorted(set(overrides) - play - toss - set(GAME_EVENTS))
    if unknown:
        raise ValueError(f"not game events: {unknown}")
    pick = lambda events: {event: name for event, name in overrides.items() if event in events}
    return GamePredictors(load_predictors(default, **pick(play)), load_toss_predictors(default, **pick(toss)),
                          *(predictor(event, overrides.get(event, default)) for event in GAME_EVENTS))
