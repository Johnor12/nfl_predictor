# START
# Simulating the game scenario many times.
# - simulate_game(ctx, predictors, sims=1000, seed=0, workers=1) -> GameSimulation: plays the game `sims`
#   times (each run has its own seed, from `seed`, the game id, and the run number, so any game can be
#   replayed), validates every game, and summarizes it. workers > 1 splits the runs across processes.
# - summarize(result) -> dict: one game's outcome: points by team, margin (home minus away), total, winner
#   (None for a tie), overtime, plays, teams ({team: {stat: value}}), players ({player id: {stat: value}}).
#   The same keys and meaning as a real game's outcome (shared/nflverse/games.py).
# - GameSimulation: context, outcomes (one summary per game that ran), failures (run number, message,
#   traceback or box score) for games that raised or broke an invariant, and example (the first game's
#   GameResult). values(key), team(team, stat), and player(player_id, stat) give one value per outcome.
# - replay(ctx, predictors, seed, run) -> GameResult: one run again, in full.
# END
import random
import traceback
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

from scenarios.game import describe_game, run_game, validate_game


@dataclass
class GameSimulation:
    context: object
    outcomes: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    example: object = None

    def values(self, key) -> list:
        return [outcome[key] for outcome in self.outcomes]

    def team(self, team, stat) -> list[float]:
        return [outcome["teams"][team].get(stat, 0.0) for outcome in self.outcomes]

    def player(self, player_id, stat) -> list[float]:
        return [outcome["players"].get(player_id, {}).get(stat, 0.0) for outcome in self.outcomes]


def summarize(result) -> dict:
    game = result.context.game
    home, away = result.score[game.home], result.score[game.away]
    return {"points": dict(result.score), "margin": home - away, "total": home + away, "winner": result.winner,
            "overtime": result.quarters > 4, "plays": len(result.plays), "teams": result.team_stats,
            "players": result.stats}


def replay(ctx, predictors, seed: int, run: int):
    return run_game(ctx, predictors, random.Random(f"{seed}|{ctx.game.game_id}|{run}"))


def _runs(ctx, predictors, seed, runs):
    outcomes, failures, example = [], [], None
    for run in runs:
        try:
            result = replay(ctx, predictors, seed, run)
        except Exception as e:
            failures.append((run, f"{type(e).__name__}: {e}", traceback.format_exc()))
            continue
        errors = validate_game(result)
        if errors:
            failures.append((run, "; ".join(errors), describe_game(result)))
        outcomes.append(summarize(result))
        example = example or result
    return outcomes, failures, example


def simulate_game(ctx, predictors, sims: int = 1000, seed: int = 0, workers: int = 1) -> GameSimulation:
    workers = max(1, min(workers, sims))
    chunks = [range(start, sims, workers) for start in range(workers)]
    if workers == 1:
        parts = [_runs(ctx, predictors, seed, chunks[0])]
    else:
        with ProcessPoolExecutor(workers) as pool:
            parts = list(pool.map(_runs, [ctx] * workers, [predictors] * workers, [seed] * workers, chunks))
    sim = GameSimulation(ctx, example=parts[0][2])
    for outcomes, failures, _ in parts:
        sim.outcomes += outcomes
        sim.failures += failures
    return sim
