# START
# Scoring the game scenario against real games, and the timeout predictor against real timeouts.
# - evaluate(season=2026, weeks=None, sims=100, seed=0, predictors=None, workers=None, lines=()) ->
#   Evaluation: every played game of the weeks is simulated `sims` times from its inputs at kickoff and
#   scored against what happened; games run in parallel processes. `lines` are evaluators.lines Lines: the
#   simulated values behind each one are kept so the simulator can be scored on them.
# - Evaluation: season, weeks, sims, games, failures (simulated games that raised or broke an invariant),
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
#   values), _score_timeouts (the timeout predictor sampled on every real play's situation).
# END
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from evaluators.scoring import Scorecard
from scenarios.game import load_game_predictors
from shared.nflverse import real_games, real_samples
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
    season: int
    weeks: list
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


def evaluate_games(games, sims: int = 100, seed: int = 0, predictors=None, workers: int | None = None, lines=()):
    keys = {}
    for line in lines:
        keys.setdefault(line.key[1], set()).add(line.key)
    jobs = [games, [sims] * len(games), [seed] * len(games), [predictors] * len(games),
            [sorted(keys.get(game.context.game.game_id, ())) for game in games]]
    if workers == 1 or len(games) == 1:
        parts = list(map(_evaluate_game, *jobs))
    else:
        with ProcessPoolExecutor(workers) as pool:
            parts = list(pool.map(_evaluate_game, *jobs))
    card, samples = Scorecard(), {}
    for part, values, _ in parts:
        card.merge(part)
        samples.update(values)
    return card, samples, sum(failures for _, _, failures in parts)


def _score_timeouts(card, season, weeks, predict, sims, seed):
    rng = random.Random(f"{seed} timeouts")
    for sample in real_samples(season, weeks):
        ctx, caller = timeout_case(sample)
        s = ctx.situation
        side = {s.offense: "offense", s.defense: "defense", None: "none"}
        left = s.clock + (900 if s.quarter in (1, 3) else 0)
        label = "last 2:00 of a half" if left <= 120 else "rest of the game"
        card.add(f"timeout: caller ({label})", [side[predict(ctx, rng)] for _ in range(sims)], caller)


def evaluate(season: int = 2026, weeks=None, sims: int = 100, seed: int = 0, predictors=None,
             workers: int | None = None, lines=()) -> Evaluation:
    games = [game for game in real_games(season, weeks) if game.actual is not None]
    weeks = sorted({game.context.game.week for game in games})
    card, samples, failures = evaluate_games(games, sims, seed, predictors, workers, lines)
    timeout = (predictors or load_game_predictors("baseline")).timeout
    _score_timeouts(card, season, weeks, timeout, sims, seed)
    return Evaluation(season, weeks, sims, len(games), failures, card, list(lines), samples)
