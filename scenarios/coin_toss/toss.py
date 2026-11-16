# START
# The coin toss scenario: the toss, the winner's choice, and what the choice means under the rules.
# - TossContext(game, players, overtime): the input. overtime is True for the toss before overtime.
# - TossPredictors(coin_toss, toss_choice): one function per event; load_toss_predictors(default=None,
#   **overrides) loads each event's default implementation (events.predictor), or the ones named.
# - allowed_choices(ctx) -> tuple[str, ...]: receive, kick, and (not in overtime) defer.
# - run_coin_toss(ctx, predictors, rng) -> Toss: winner, choice, who kicks off now, and who kicks off the
#   second half (after an overtime toss: the third overtime period of a postseason game).
# Rules: the team that doesn't choose first chooses at the second half, and always takes the ball. So a
#   winner that defers kicks first and receives the second half; one that receives kicks off the second half;
#   one that chooses to kick kicks off both halves. In overtime the loser of the toss chooses first two
#   periods later, so the winner kicks off then.
# END
import dataclasses
from dataclasses import dataclass
from typing import Callable

from events import predictor
from scenarios.play import Game, IllegalChoice, Player


@dataclass(frozen=True)
class TossContext:
    game: Game
    players: tuple[Player, ...]    # active players on both teams
    overtime: bool = False


@dataclass(frozen=True)
class Toss:
    winner: str
    choice: str                    # receive, kick, or defer
    kicking: str                   # kicks off now
    receiving: str
    second_half_kicking: str       # kicks off the second half (overtime: the third period after this toss)
    overtime: bool


@dataclass(frozen=True)
class TossPredictors:
    coin_toss: Callable            # (ctx, rng) -> team
    toss_choice: Callable          # (ctx, winner, allowed, rng) -> choice


def load_toss_predictors(default: str | None = None, **overrides: str) -> TossPredictors:
    events = [f.name for f in dataclasses.fields(TossPredictors)]
    unknown = sorted(set(overrides) - set(events))
    if unknown:
        raise ValueError(f"not coin toss events: {unknown}")
    return TossPredictors(**{event: predictor(event, overrides.get(event, default)) for event in events})


def allowed_choices(ctx) -> tuple[str, ...]:
    return ("receive", "kick") if ctx.overtime else ("receive", "kick", "defer")


def run_coin_toss(ctx, predictors, rng) -> Toss:
    teams = (ctx.game.home, ctx.game.away)
    winner = predictors.coin_toss(ctx, rng)
    if winner not in teams:
        raise IllegalChoice(f"{winner} isn't playing in {ctx.game.game_id}")
    loser = teams[0] if winner == teams[1] else teams[1]
    allowed = allowed_choices(ctx)
    choice = predictors.toss_choice(ctx, winner, allowed, rng)
    if choice not in allowed:
        raise IllegalChoice(f"toss choice {choice} not in {allowed}")
    kicking, receiving = (loser, winner) if choice == "receive" else (winner, loser)
    later = loser if choice == "defer" else winner
    return Toss(winner, choice, kicking, receiving, later, ctx.overtime)
