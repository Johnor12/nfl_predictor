# START
# The coin toss scenario: the toss, the winner's choice, and what the choice means under the rules.
# - TossContext(game, players, overtime): the input. overtime is True for the toss before overtime.
# - TossPredictors(coin_toss, toss_choice): one function per event; load_toss_predictors(default, **overrides)
#   loads each event's implementation by name from events/<event>/predictors/<name>/.
# - allowed_choices(ctx) -> tuple[str, ...]: receive, kick, and (not in overtime) defer.
# - run_coin_toss(ctx, predictors, rng) -> Toss: winner, choice, who kicks off now, and who kicks off the
#   second half (None for an overtime toss).
# Rules: the team that doesn't choose first chooses at the second half, and always takes the ball. So a
#   winner that defers kicks first and receives the second half; one that receives kicks off the second half;
#   one that chooses to kick kicks off both halves.
# END
import dataclasses
from dataclasses import dataclass
from importlib import import_module
from typing import Callable

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
    second_half_kicking: str | None
    overtime: bool


@dataclass(frozen=True)
class TossPredictors:
    coin_toss: Callable            # (ctx, rng) -> team
    toss_choice: Callable          # (ctx, winner, allowed, rng) -> choice


def load_toss_predictors(default: str = "baseline", **overrides: str) -> TossPredictors:
    events = [f.name for f in dataclasses.fields(TossPredictors)]
    unknown = sorted(set(overrides) - set(events))
    if unknown:
        raise ValueError(f"not coin toss events: {unknown}")
    return TossPredictors(**{event: import_module(f"events.{event}.predictors.{overrides.get(event, default)}").predict
                             for event in events})


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
    later = None if ctx.overtime else loser if choice == "defer" else winner
    return Toss(winner, choice, kicking, receiving, later, ctx.overtime)
