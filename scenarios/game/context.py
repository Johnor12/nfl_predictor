# START
# Game scenario inputs.
# - GameContext(game, players): everything known at kickoff: the game (teams, venue, weather, coaches,
#   referee, season, playoff) and both teams' active players.
# - validate_game_context(ctx) -> list[str]: problems with an input (empty if it's usable): the same checks
#   the play scenario makes on the opening kickoff.
# END
from dataclasses import dataclass

from scenarios.play import Game, PlayContext, Player, Situation, validate_context
from shared.rulebook import rules_for


@dataclass(frozen=True)
class GameContext:
    game: Game
    players: tuple[Player, ...]    # active players on both teams


def validate_game_context(ctx: GameContext) -> list[str]:
    g, rules = ctx.game, rules_for(ctx.game.season)
    opening = Situation("kickoff", g.home, g.away, float(rules.kickoff_line), None, None, {g.home: 0, g.away: 0},
                        1, 900.0, False, rules.admin_play_clock, {g.home: 3, g.away: 3})
    return validate_context(PlayContext(g, opening, ctx.players))
