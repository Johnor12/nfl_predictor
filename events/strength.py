# START
# Who is playing, as numbers: the inputs about the teams, coaches, referee, players, and conditions that the
# trained predictors share (events.situation is the play itself). The same functions read a simulated play
# and a real one, so the two can't drift apart.
# - rates(who, top, bottom) -> [float, float]: how often `who` did `top` per `bottom` in this season's earlier
#   games, and over earlier seasons (nan where there is no `bottom` yet). `who` is anything with `stats` and
#   `career`: a team's, coach's, or referee's `Form` (ctx.game.form(...)), or a `Player`.
# - rating(who, over, per, shrink) -> float: how far above what was expected `who` has been per `per`, as
#   one number: his `over` stat (what he did less what the situations called for: `pass_cmp_over`,
#   `dropbacks_over`) of this season and of the earlier ones (which count EARLIER), over his `per` stat plus
#   `shrink`. 0 is the league, and what somebody without a past gets. Read it exactly: it is already shrunk.
# - total(who, stat) -> float: the stat's total in this season's earlier games: how much a season rate rests on.
# - experience(player) -> float: his years in the league. position(player) -> float: his position group as a
#   number a tree can split on (POSITIONS: receivers, tight ends, backs, quarterbacks, then everyone else).
# - quarterback(ctx, lineups) -> Player | None: the offense's quarterback on the field.
# - weather(game) -> [temperature, wind, outdoors] (nan where the game's data doesn't say).
# Keep a model to a few of these. Many numbers about one team are a fingerprint of its season, and a model
# given one learns the teams it was trained on instead of what a past rate says about the next game
# (MAINTAINER.md). Prefer a rating to a pair of rates where the data has an expectation to measure against:
# a raw rate is mostly the situations a team was in (how deep it threw, whether it was behind).
# END
import math

POSITIONS = {"WR": 0, "TE": 1, "RB": 2, "FB": 2, "QB": 3}
EARLIER = 0.5  # what the earlier seasons' totals count for in a rating, next to this season's


def rates(who, top, bottom) -> list[float]:
    return [stats.get(top, 0.0) / stats[bottom] if stats.get(bottom) else math.nan for stats in (who.stats, who.career)]


def rating(who, over, per, shrink) -> float:
    """How far above what was expected `who` has been per `per`: this season's `over` and the earlier
    seasons' together (those count EARLIER), shrunk toward 0 (the league) by `shrink` of `per`."""
    top = who.stats.get(over, 0.0) + EARLIER * who.career.get(over, 0.0)
    return top / (who.stats.get(per, 0.0) + EARLIER * who.career.get(per, 0.0) + shrink)


def total(who, stat) -> float:
    return who.stats.get(stat, 0.0)


def experience(player) -> float:
    return math.nan if player.years_exp is None else player.years_exp


def position(player) -> float:
    return POSITIONS.get(player.position, len(POSITIONS))


def quarterback(ctx, lineups):
    return next((ctx.by_id[pid] for pid in lineups.offense.players if ctx.by_id[pid].position == "QB"), None)


def weather(game) -> list[float]:
    known = lambda value: math.nan if value is None else value  # noqa: E731
    return [known(game.temperature), known(game.wind), math.nan if game.roof is None else game.roof in ("outdoors", "open")]

