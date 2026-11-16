# START
# Test support for the game scenario: synthetic inputs and cheap random ("chaos") predictors.
# - synthetic_game(season=2026, playoff=False) -> GameContext: HOME against AWAY with synthetic rosters.
# - chaos_game_predictors(timeouts=0.03, challenges=0.03) -> GamePredictors: the play scenario's chaos
#   predictors, a random toss and choice, timeouts called at random by a team that may, and challenges made
#   and won at random by one that may, for fuzzing the invariants.
# - with_events(predictors, **events) -> GamePredictors: replace events with other functions, whichever
#   bundle they are in (with_events(base, timeout=never, pre_snap=slow)).
# END
import dataclasses

from events.challenge import Challenge
from events.timeout import Timeout
from scenarios.coin_toss import TossPredictors
from scenarios.game.context import GameContext
from scenarios.game.predictors import GAME_EVENTS, GamePredictors
from scenarios.play import Game
from scenarios.play.testing import chaos_predictors, synthetic_roster


def synthetic_game(season: int = 2026, playoff: bool = False) -> GameContext:
    game = Game("test", season, 1, "HOME", "AWAY", playoff=playoff)
    return GameContext(game, synthetic_roster("HOME") + synthetic_roster("AWAY"))


def chaos_game_predictors(timeouts: float = 0.03, challenges: float = 0.03) -> GamePredictors:
    def coin_toss(ctx, rng):
        return rng.choice([ctx.game.home, ctx.game.away])

    def toss_choice(ctx, winner, allowed, rng):
        return rng.choice(allowed)

    def timeout(ctx, called, rng):
        able = sorted(team for team, left in ctx.situation.timeouts.items() if left and team != called)
        often = 0.3 if called else timeouts  # a second one in the same dead ball
        return Timeout(rng.choice(able), rng.uniform(0, 40)) if able and rng.random() < often else None

    def challenge(ctx, outcome, allowed, rng):
        return Challenge(rng.choice(allowed), rng.random() < 0.5) if rng.random() < challenges else None

    return GamePredictors(chaos_predictors(), TossPredictors(coin_toss, toss_choice), timeout, challenge)


def with_events(predictors: GamePredictors, **events) -> GamePredictors:
    play = {f.name for f in dataclasses.fields(predictors.play)}
    toss = {f.name for f in dataclasses.fields(predictors.toss)}
    pick = lambda names: {event: fn for event, fn in events.items() if event in names}
    return dataclasses.replace(predictors, play=dataclasses.replace(predictors.play, **pick(play)),
                               toss=dataclasses.replace(predictors.toss, **pick(toss)), **pick(GAME_EVENTS))
