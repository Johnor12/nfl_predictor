# START
# Scoring the game scenario against real games, and its timeout and challenge predictors against the real ones.
# - evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None,
#   lines=()) -> Evaluation: every played game of the seasons (`games` of them, sampled by
#   evaluators.sample_games) is simulated `sims` times from its inputs at kickoff and scored against what
#   happened; games run in parallel processes. `lines` are evaluators.lines Lines: the simulated values
#   behind each one are kept so the simulator can be scored on them.
# - Evaluation: seasons, sims, games, failures (simulated games that raised or broke an invariant),
#   card (a scoring.Scorecard with outputs named "game: margin", "team: pass_yds", "player: rec_yds (WR1)",
#   "timeout: caller (...)", "challenge: who and ruling": outputs.py has the game's), lines, and samples
#   ({line key: simulated values}, for lines.score_lines).
# - evaluate_games(games, sims, seed, predictors, workers, lines) -> (card, samples, failures): the same for
#   a list of shared.nflverse RealGames (or anything with .context and .actual).
# Internals: _evaluate_game (one game's scorecard and line samples), _line_values (a line's simulated
#   values), _score_games (the games as jobs of a pool, their scorecards merged), _played (a season's sampled
#   games), _score_events (the game's own predictors, a season at a time: the timeout predictor sampled on
#   every real play's situation, the challenge predictor on every real play a coach could challenge).
#   evaluate runs all three in one pool of processes: reading a season and scoring its timeouts and
#   challenges are jobs like a game is, so nothing waits on the parent process.
# END
import random
from dataclasses import dataclass

from evaluators import executor
from evaluators.game.outputs import game_outputs
from evaluators.sample import EVALUATED, sample_games
from evaluators.scoring import Scorecard
from scenarios.game import clock, load_game_predictors
from shared.lines import value
from shared.nflverse import real_games, real_plays
from shared.priors import timeout_case
from shared.rulebook import rules_for
from simulators.game import simulate_game


@dataclass
class Evaluation:
    seasons: list
    sims: int
    games: int
    failures: int
    card: Scorecard
    lines: list
    samples: dict


def _line_values(sim, key) -> list:
    if key[0] in ("margin", "total"):
        return [float(value) for value in sim.values(key[0])]
    stat, _, player_id = key
    return [value(stat, outcome["players"].get(player_id, {})) for outcome in sim.outcomes]


def _evaluate_game(game, sims, seed, predictors, keys):
    sim = simulate_game(game.context, predictors or load_game_predictors(), sims, seed)
    card = Scorecard()
    simulated = [game_outputs(game.context, outcome) for outcome in sim.outcomes]
    for (name, subject), actual in game_outputs(game.context, game.actual).items():
        card.add(name, [outputs[name, subject] for outputs in simulated], actual)
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


def _score_events(season, games, predictors, sims, seed) -> Scorecard:
    card, rng, rules = Scorecard(), random.Random(f"{seed} timeouts {season}"), rules_for(season)
    challenges = random.Random(f"{seed} challenges {season}")
    for play in real_plays(season, games=games):
        ctx, caller = timeout_case(play)
        s = ctx.situation
        side = lambda team: "offense" if team == s.offense else "defense"
        left = s.clock + (900 if s.quarter in (1, 3) else 0)
        label = "last 2:00 of a half" if left <= 120 else "rest of the game"
        called = [predictors.timeout(ctx, None, rng) for _ in range(sims)]
        card.add(f"timeout: caller ({label})", [side(t.team) if t else "none" for t in called], caller)
        allowed = clock.challengers(ctx.game, rules, s, s.timeouts, {s.offense: (), s.defense: ()})
        if allowed:  # the data doesn't say how many challenges a team had left
            ruling = lambda made: f"{side(made[0])} {'won' if made[1] else 'lost'}" if made else "none"
            made = [predictors.challenge(play.context, play.actual, allowed, challenges) for _ in range(sims)]
            sampled = [ruling(challenge and (challenge.team, challenge.won)) for challenge in made]
            card.add("challenge: who and ruling", sampled, ruling(play.actual["challenge"]))
    return card


def evaluate(seasons=EVALUATED, weeks=None, games=None, sims: int = 100, seed: int = 0, predictors=None,
             workers: int | None = None, lines=()) -> Evaluation:
    sample = sample_games(seasons, weeks, games)
    own = predictors or load_game_predictors()
    with executor(workers) as pool:  # each season's games are read and its timeouts scored while games are simulated
        loading = [pool.submit(_played, season, ids) for season, ids in sample.items()]
        timeouts = [pool.submit(_score_events, season, ids, own, sims, seed) for season, ids in sample.items()]
        played = [game for games in loading for game in games.result()]
        card, samples, failures = _score_games(pool, played, sims, seed, predictors, lines)
        for part in timeouts:
            card.merge(part.result())
    return Evaluation(sorted(sample), sims, len(played), failures, card, list(lines), samples)
