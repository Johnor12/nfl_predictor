# START
# CLI: python -m evaluators.play [--season 2026] [--weeks 1-3 | --weeks 1,4] [--sims 100] [--seed 0]
#   [--swap carry=tuned ...] [--workers N] [--out path]
# Scores the play scenario and its event predictors against real plays, writes the report, and prints the
# score tables. --swap evaluates another implementation of an event (events/<event>/predictors/<name>/).
# END
import argparse

from evaluators import parse_weeks
from evaluators.play import evaluate, write_report
from scenarios.play import load_predictors


def main():
    parser = argparse.ArgumentParser(description="Score the play scenario and its event predictors against real plays.")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--weeks", default=None)
    parser.add_argument("--sims", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--swap", nargs="*", default=[], metavar="EVENT=NAME")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    predictors = load_predictors("baseline", **dict(swap.split("=") for swap in args.swap))
    evaluation = evaluate(args.season, parse_weeks(args.weeks), args.sims, args.seed, predictors, args.workers)
    path = write_report(evaluation, args.out)
    report = path.read_text(encoding="utf-8")
    print(path)
    print(report[:report.index("## PIT histograms")])


if __name__ == "__main__":
    main()
