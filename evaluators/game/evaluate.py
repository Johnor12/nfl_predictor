# START
# Scoring the game scenario against real games, and the timeout predictor against real timeouts.
# - evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None,
#   lines=()) -> Evaluation: every played game of the seasons (`games` of them, sampled by
#   evaluators.sample_games) is simulated `sims` times from its inputs at kickoff and scored against what
#   happened; games run in parallel processes. `lines` are evaluators.lines Lines: the simulated values
#   behind each one are kept so the simulator can be scored on them.
# - Evaluation: seasons, sims, games, failures (simulated games that raised or broke an invariant),
#   card (a scoring.Scorecard with outputs named "game: margin", "team: pass_yds", "player: rec_yds (WR1)",
#   "timeout: caller (...)"), lines, and samples ({line key: simulated values}, for lines.score_lines).
# - evaluate_games(games, sims, seed, predictors, workers, lines) -> (card, samples, failures): the same for
#   a list of shared.nflverse RealGames (or anything with .context and .actual).
# - game_outputs(ctx, outcome) -> {(name, subject): value}: the scored outputs, read the same way from a
#   real outcome (RealGame.actual) and a simulated one (simulators.game.summarize). subject is None, a team,
#   or a player id.
# - TEAM_STATS, PLAYER_STATS: the stats scored for each team, and for each depth chart role (a 3 means third
#   or lower).
# Internals: _evaluate_game (one game's scorecard and line samples), _line_values (a line's simulated
#   values), _score_games (the games as jobs of a pool, their scorecards merged), _played (a season's sampled
#   games), _score_timeouts (the timeout predictor sampled on every real play's situation, a season at a
#   time). evaluate runs all three in one pool of processes: reading a season and scoring its timeouts are
#   jobs like a game is, so nothing waits on the parent process.
# END
import random
from dataclasses import dataclass

from evaluators import executor
from evaluators.sample import EVALUATED, sample_games
from evaluators.scoring import Scorecard
from scenarios.game import load_game_predictors
from shared.nflverse import real_games, real_plays
from shared.priors import role, timeout_case
from simulators.game import simulate_game

TEAM_STATS = ("pass_yds", "pass_att", "rush_yds", "rush_att", "sacked", "penalties", "punts", "fg_att")
RUSHER = ("rush_yds", "rush_att", "rec_yds", "receptions")
RECEIVER = ("rec_yds", "receptions")
PLAYER_STATS = {
    "QB1": ("pass_yds", "pass_att", "pass_cmp", "pass_td", "int_thrown", "rush_yds"),
    "RB1": RUSHER, "RB2": RUSHER, "WR1": RECEIVER, "WR2": RECEIVER, "WR3": RECEIVER, "TE1": RECEIVER,
    "TE2": RECEIVER, "K": ("fg_made", "xp_made"),
}


@dataclass
class Evaluation:
    seasons: list
    sims: int
    games: int
    failures: int
    card: Scorecard
    lines: list
    samples: dict


def game_outputs(ctx, outcome) -> dict:
    game = ctx.game
    out = {("game: margin", None): float(outcome["margin"]), ("game: total", None): float(outcome["total"]),
           ("game: home win", None): outcome["margin"] > 0, ("game: overtime", None): bool(outcome["overtime"]),
           ("game: plays", None): float(outcome["plays"])}
    for team in (game.home, game.away):
        stats = outcome["teams"][team]
        out["team: points", team] = float(outcome["points"][team])
        out["team: turnovers", team] = float(stats.get("int_thrown", 0) + stats.get("fumbles_lost", 0))
        for stat in TEAM_STATS:
            out[f"team: {stat}", team] = float(stats.get(stat, 0))
    for player in ctx.players:
        position = role(player)
        if position in PLAYER_STATS:
            stats = outcome["players"].get(player.id, {})
            for stat in PLAYER_STATS[position]:
                out[f"player: {stat} ({position})", player.id] = float(stats.get(stat, 0))
            if position not in ("QB1", "K"):
                out[f"player: touchdown ({position})", player.id] = stats.get("rush_td", 0) + stats.get("rec_td", 0) > 0
    return out


def _line_values(sim, key) -> list:
    if key[0] in ("margin", "total"):
        return [float(value) for value in sim.values(key[0])]
    stat, _, player_id = key
    return sim.player(player_id, stat)


def _evaluate_game(game, sims, seed, predictors, keys):
    sim = simulate_game(game.context, predictors or load_game_predictors("baseline"), sims, seed)
    card = Scorecard()
    simulated = [game_outputs(game.context, outcome) for outcome in sim.outcomes]
    for (name, subject), value in game_outputs(game.context, game.actual).items():
        card.add(name, [outputs[name, subject] for outputs in simulated], value)
    return card, {key: _line_values(sim, key) for key in keys}, len(sim.failures)


def _score_games(pool, games, sims, seed, predictors, lines):
    keys = {}
    for line in lines:
        keys.setdefault(line.key[1], set()).add(line.key)
    parts = list(pool.map(_evaluate_game, games, [sims] * len(games), [seed] * len(games), [predictors] * len(games),
                          [sorted(keys.get(game.context.game.game_id, ())) for game in games]))
    card, samples = Scorecard(), {}
    for part, values, _ in parts:
        card.merge(part)
        samples.update(values)
    return card, samples, sum(failures for _, _, failures in parts)


def evaluate_games(games, sims: int = 100, seed: int = 0, predictors=None, workers: int | None = None, lines=()):
    with executor(1 if len(games) == 1 else workers) as pool:
        return _score_games(pool, games, sims, seed, predictors, lines)


def _played(season, games) -> list:
    return [game for game in real_games(season, games=games) if game.actual]


def _score_timeouts(season, games, predict, sims, seed) -> Scorecard:
    card, rng = Scorecard(), random.Random(f"{seed} timeouts {season}")
    for play in real_plays(season, games=games):
        ctx, caller = timeout_case(play)
        s = ctx.situation
        side = {s.offense: "offense", s.defense: "defense", None: "none"}
        left = s.clock + (900 if s.quarter in (1, 3) else 0)
        label = "last 2:00 of a half" if left <= 120 else "rest of the game"
        card.add(f"timeout: caller ({label})", [side[predict(ctx, rng)] for _ in range(sims)], caller)
    return card


def evaluate(seasons=EVALUATED, weeks=None, games=None, sims: int = 100, seed: int = 0, predictors=None,
             workers: int | None = None, lines=()) -> Evaluation:
    sample = sample_games(seasons, weeks, games)
    timeout = (predictors or load_game_predictors("baseline")).timeout
    with executor(workers) as pool:  # each season's games are read and its timeouts scored while games are simulated
        loading = [pool.submit(_played, season, ids) for season, ids in sample.items()]
        timeouts = [pool.submit(_score_timeouts, season, ids, timeout, sims, seed) for season, ids in sample.items()]
        played = [game for games in loading for game in games.result()]
        card, samples, failures = _score_games(pool, played, sims, seed, predictors, lines)
        for part in timeouts:
            card.merge(part.result())
    return Evaluation(sorted(sample), sims, len(played), failures, card, list(lines), samples)
