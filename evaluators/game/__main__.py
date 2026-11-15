# START
# CLI: python -m evaluators.game [--seasons 2021-2026 | --seasons 2026] [--games 160] [--weeks 1-3 | --weeks 1,4]
#   [--sims 100] [--seed 0] [--swap carry=tuned ...] [--workers N] [--no-lines] [--out path]
# Simulates a fixed sample of the seasons' played games (--games 0 for every game), scores each against what
# happened and against the betting lines (downloading the lines it doesn't have yet; --no-lines skips
# them), writes the report, and prints the score tables.
# --swap evaluates another implementation of an event (events/<event>/predictors/<name>/).
# END
import argparse

from evaluators import parse_weeks
from evaluators.game import evaluate, write_report
from evaluators.lines import lines
from evaluators.sample import EVALUATED, sample_games
from scenarios.game import load_game_predictors


def main():
    parser = argparse.ArgumentParser(description="Score the game scenario against real games and betting lines.")
    parser.add_argument("--seasons", default=None)
    parser.add_argument("--games", type=int, default=160)
    parser.add_argument("--weeks", default=None)
    parser.add_argument("--sims", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--swap", nargs="*", default=[], metavar="EVENT=NAME")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--no-lines", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    seasons, weeks, games = parse_weeks(args.seasons) or EVALUATED, parse_weeks(args.weeks), args.games or None
    predictors = load_game_predictors("baseline", **dict(swap.split("=") for swap in args.swap))
    betting = () if args.no_lines else lines(sample_games(seasons, weeks, games))
    evaluation = evaluate(seasons, weeks, games, args.sims, args.seed, predictors, args.workers, betting)
    path = write_report(evaluation, args.out)
    report = path.read_text(encoding="utf-8")
    print(path)
    print(report[:report.index("## PIT histograms")])


if __name__ == "__main__":
    main()
