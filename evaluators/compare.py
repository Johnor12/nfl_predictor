# START
# Two evaluations of the same games, compared case by case: what a change did to each scored output.
# - save(evaluation, path) / load(path): an evaluation kept as a file (the CLIs' --save).
# - compare(before, after, names=()) -> list[dict], one per output both evaluations scored on the same cases:
#   name, n, before and after (the mean scores), change (after over before, less 1), z (the mean difference
#   of the cases' scores over its standard error: beyond 2 or so is more than chance), mean (the real
#   average), sim_before and sim_after (the simulated ones). `names` keeps the outputs whose name contains
#   one of them. An output scored on different cases (other games, other players) is left out.
# - table(rows) -> list[str]: the rows as a markdown table.
# - CLI: `python -m evaluators.compare before.pkl after.pkl [name ...]`.
# Both evaluations must cover the same games with the same seed's sample (evaluators/README.md): the cases
# are matched by their order. A file holds this project's own objects: only load one you saved.
# END
import math
import pickle
import sys
from pathlib import Path


def save(evaluation, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps(evaluation))
    return path


def load(path):
    return pickle.loads(Path(path).read_bytes())


def compare(before, after, names=()) -> list[dict]:
    summaries = [{row["name"]: row for row in evaluation.card.rows()} for evaluation in (before, after)]
    rows = []
    for name, old in before.card.outputs.items():
        new = after.card.outputs.get(name)
        wanted = not names or any(part in name for part in names)
        if new is None or len(old.scores) != len(new.scores) or not old.scores or not wanted:
            continue
        n = len(old.scores)
        differences = [b - a for a, b in zip(old.scores, new.scores)]
        mean, was = sum(differences) / n, sum(old.scores) / n
        error = math.sqrt(sum((d - mean) ** 2 for d in differences) / max(1, n - 1) / n)
        rows.append(dict(name=name, n=n, before=was, after=was + mean, change=mean / was if was else None,
                         z=mean / error if error else 0.0, mean=summaries[0][name]["mean"],
                         sim_before=summaries[0][name]["sim_mean"], sim_after=summaries[1][name]["sim_mean"]))
    return rows


def table(rows) -> list[str]:
    number = lambda value, digits: "-" if value is None else f"{value:.{digits}f}"  # noqa: E731
    lines = ["| output | n | before | after | change | z | mean | sim before | sim after |", "|---" * 9 + "|"]
    for r in rows:
        change = "-" if r["change"] is None else f"{100 * r['change']:+.1f}%"
        lines.append(f"| {r['name']} | {r['n']} | {number(r['before'], 4)} | {number(r['after'], 4)} | {change} "
                     f"| {r['z']:+.1f} | {number(r['mean'], 3)} | {number(r['sim_before'], 3)} "
                     f"| {number(r['sim_after'], 3)} |")
    return lines


if __name__ == "__main__":
    print("\n".join(table(compare(load(sys.argv[1]), load(sys.argv[2]), sys.argv[3:]))))
