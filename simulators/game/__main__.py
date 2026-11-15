# START
# CLI: python -m simulators.game GAME_ID [--sims 1000] [--seed 0] [--workers N] [--swap carry=tuned ...]
# Forecasts a real game (an nflverse game id such as 2026_10_NE_DET, played or not): simulates it from the
# inputs known at kickoff and prints the distributions. --swap uses another implementation of an event.
# END
import argparse
import os

from scenarios.game import load_game_predictors, validate_game_context
from shared.nflverse import real_games
from simulators.game import forecast, simulate_game


def main():
    parser = argparse.ArgumentParser(description="Forecast a real game by simulating it.")
    parser.add_argument("game_id")
    parser.add_argument("--sims", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    parser.add_argument("--swap", nargs="*", default=[], metavar="EVENT=NAME")
    args = parser.parse_args()
    season, week = int(args.game_id[:4]), int(args.game_id[5:7])
    game = next((g for g in real_games(season, [week]) if g.context.game.game_id == args.game_id), None)
    if game is None:
        parser.error(f"no game {args.game_id} in the {season} schedule")
    problems = validate_game_context(game.context)
    if problems:
        parser.error(f"the inputs for {args.game_id} aren't usable: {problems}")
    predictors = load_game_predictors(**dict(swap.split("=") for swap in args.swap))
    sim = simulate_game(game.context, predictors, args.sims, args.seed, args.workers)
    print(forecast(sim))
    for run, message, _ in sim.failures[:5]:
        print(f"failed run {run}: {message}")
    if game.actual:
        print(f"\nactual: {game.actual['points']}")


if __name__ == "__main__":
    main()
