# START
# CLI: python -m evaluators.audit [--season 2026] [--weeks 1-3 | --weeks 1,4] [--sims 1] [--seed 0] [--out path]
# Runs the audit, writes the markdown report, and prints the summary and any flagged metrics.
# END
import argparse

from evaluators import parse_weeks
from evaluators.audit import metrics, run_audit, write_report


def main():
    parser = argparse.ArgumentParser(description="Audit the play simulator against real plays.")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--weeks", default=None)
    parser.add_argument("--sims", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    audit = run_audit(args.season, parse_weeks(args.weeks), args.sims, args.seed)
    path = write_report(audit, args.out)
    print(path)
    print("\n".join(path.read_text(encoding="utf-8").splitlines()[2:8]))
    for row in metrics(audit):
        if row["flag"]:
            print(f"check: {row['section']} / {row['label']}: real {row['real']:.3f} vs simulated {row['sim']:.3f}")


if __name__ == "__main__":
    main()
