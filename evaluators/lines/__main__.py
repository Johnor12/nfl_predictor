# START
# CLI: python -m evaluators.lines [--season 2026] [--weeks 1-3 | --weeks 1,4] [--out path]
# Downloads the lines it doesn't have yet, scores them against the results, writes the report, and prints it.
# END
import argparse

from evaluators import parse_weeks
from evaluators.lines import write_report


def main():
    parser = argparse.ArgumentParser(description="Score the betting lines against what happened.")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--weeks", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    path = write_report(args.season, parse_weeks(args.weeks), path=args.out)
    print(path)
    print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
