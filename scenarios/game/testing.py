# START
# Test support for the game scenario: synthetic inputs and cheap random ("chaos") predictors.
# - synthetic_game(season=2026, playoff=False) -> GameContext: HOME against AWAY with synthetic rosters.
# - chaos_game_predictors(timeouts=0.03) -> GamePredictors: the play scenario's chaos predictors, a random
#   toss and choice, and timeouts called at random by a team that has one, for fuzzing the invariants.
# - with_events(predictors, **events) -> GamePredictors: replace events with other functions, whichever
#   bundle they are in (with_events(base, timeout=never, pre_snap=slow)).
# END
import dataclasses

from scenarios.coin_toss import TossPredictors
from scenarios.game.context import GameContext
from scenarios.game.predictors import GamePredictors
from scenarios.play import Game
from scenarios.play.testing import chaos_predictors, synthetic_roster


def synthetic_game(season: int = 2026, playoff: bool = False) -> GameContext:
    game = Game("test", season, 1, "HOME", "AWAY", playoff=playoff)
    return GameContext(game, synthetic_roster("HOME") + synthetic_roster("AWAY"))


def chaos_game_predictors(timeouts: float = 0.03) -> GamePredictors:
    def coin_toss(ctx, rng):
        return rng.choice([ctx.game.home, ctx.game.away])

    def toss_choice(ctx, winner, allowed, rng):
        return rng.choice(allowed)

    def timeout(ctx, rng):
        able = sorted(team for team, left in ctx.situation.timeouts.items() if left)
        return rng.choice(able) if able and rng.random() < timeouts else None

    return GamePredictors(chaos_predictors(), TossPredictors(coin_toss, toss_choice), timeout)


def with_events(predictors: GamePredictors, **events) -> GamePredictors:
    play = {f.name for f in dataclasses.fields(predictors.play)}
    toss = {f.name for f in dataclasses.fields(predictors.toss)}
    pick = lambda names: {event: fn for event, fn in events.items() if event in names}
    return dataclasses.replace(predictors, play=dataclasses.replace(predictors.play, **pick(play)),
                               toss=dataclasses.replace(predictors.toss, **pick(toss)), **pick({"timeout"}))
