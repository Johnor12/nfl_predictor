# START
# CLI: python -m evaluators.game [--season 2026] [--weeks 1-3 | --weeks 1,4] [--sims 100] [--seed 0]
#   [--swap carry=tuned ...] [--workers N] [--no-lines] [--out path]
# Simulates every played game, scores it against what happened and against the betting lines (downloading
# the lines it doesn't have yet; --no-lines skips them), writes the report, and prints the score tables.
# --swap evaluates another implementation of an event (events/<event>/predictors/<name>/).
# END
import argparse

from evaluators import parse_weeks
from evaluators.game import evaluate, write_report
from evaluators.lines import lines
from scenarios.game import load_game_predictors


def main():
    parser = argparse.ArgumentParser(description="Score the game scenario against real games and betting lines.")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--weeks", default=None)
    parser.add_argument("--sims", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--swap", nargs="*", default=[], metavar="EVENT=NAME")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--no-lines", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    weeks = parse_weeks(args.weeks)
    predictors = load_game_predictors("baseline", **dict(swap.split("=") for swap in args.swap))
    betting = () if args.no_lines else lines(args.season, weeks)
    evaluation = evaluate(args.season, weeks, args.sims, args.seed, predictors, args.workers, betting)
    path = write_report(evaluation, args.out)
    report = path.read_text(encoding="utf-8")
    print(path)
    print(report[:report.index("## PIT histograms")])


if __name__ == "__main__":
    main()
