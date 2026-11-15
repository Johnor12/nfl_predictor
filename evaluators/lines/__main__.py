# START
# CLI: python -m evaluators.lines [--seasons 2021-2026 | --seasons 2026] [--games 160] [--weeks 1-3 | --weeks 1,4]
#   [--out path]
# Scores the betting lines of a fixed sample of the seasons' played games (--games 0 for every game) against
# the results, downloading the lines it doesn't have yet; writes the report and prints it.
# END
import argparse

from evaluators import parse_weeks
from evaluators.lines import write_report
from evaluators.sample import EVALUATED, sample_games


def main():
    parser = argparse.ArgumentParser(description="Score the betting lines against what happened.")
    parser.add_argument("--seasons", default=None)
    parser.add_argument("--games", type=int, default=160)
    parser.add_argument("--weeks", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    games = sample_games(parse_weeks(args.seasons) or EVALUATED, parse_weeks(args.weeks), args.games or None)
    path = write_report(games, path=args.out)
    print(path)
    print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
