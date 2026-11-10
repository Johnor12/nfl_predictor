# START
# The scorecard: scores many forecasts, grouped by output name, and summarizes them.
# - Scorecard.add(name, samples, actual): score one case (samples that are None are dropped; a case left with
#   fewer than 2 is counted as unscored). The output's kind comes from the type of `actual`.
# - Scorecard.merge(other): fold another scorecard in (for evaluations split across processes).
# - Scorecard.rows() -> list[dict], one per output: name, kind, n, unscored, sims (mean ensemble size),
#   score (mean fair score), reference (climatology), skill (1 - score / reference), se (standard error of
#   the mean score over cases), sim_se (the part of the error that comes from simulating a finite number of
#   times), sims_needed (see below).
# - Scorecard.pit(name) -> [share per bin] for a numeric output; Scorecard.reliability(name) ->
#   [(mean probability, observed rate, n)] for a binary or categorical one (each class the output ever took
#   is one probability per case).
# Sim noise: each case is also scored on the two halves of its ensemble (the same predictor, two seeds). The
#   spread between the halves gives sim_se, and sims_needed: the sims per case that make a `change` (1%) move
#   in the score stand 2 standard errors clear of sim noise when two runs are compared, capped at SIMS_CEILING.
# Internals: _Output (one output's per-case scores, half differences, outcomes, PIT values, and forecasts:
#   each case's {class: share of samples} with what happened).
# END
import math
import random
from collections import Counter
from dataclasses import dataclass, field

from evaluators.scoring.scores import climatology, histogram, kind_of, pit, reliability, score

SIMS_CEILING = 10_000


@dataclass
class _Output:
    kind: str
    scores: list = field(default_factory=list)
    halves: list = field(default_factory=list)    # score of one half of the ensemble minus the other's
    members: int = 0
    unscored: int = 0
    actuals: Counter = field(default_factory=Counter)
    pits: list = field(default_factory=list)
    forecasts: list = field(default_factory=list)  # ({class: share of the samples}, actual)


class Scorecard:
    def __init__(self):
        self.outputs = {}
        self.rng = random.Random(0)  # breaks PIT ties

    def add(self, name, samples, actual):
        out = self.outputs.setdefault(name, _Output(kind_of(actual)))
        samples = [x for x in samples if x is not None]
        m = len(samples)
        if m < 2:
            out.unscored += 1
            return
        out.scores.append(score(out.kind, samples, actual))
        out.members += m
        out.actuals[actual] += 1
        if m >= 4:
            out.halves.append(score(out.kind, samples[0::2], actual) - score(out.kind, samples[1::2], actual))
        if out.kind == "numeric":
            out.pits.append(pit(samples, actual, self.rng.random()))
        else:
            out.forecasts.append(({c: k / m for c, k in Counter(samples).items()}, actual))

    def merge(self, other):
        for name, theirs in other.outputs.items():
            out = self.outputs.setdefault(name, _Output(theirs.kind))
            for key in ("scores", "halves", "pits", "forecasts"):
                getattr(out, key).extend(getattr(theirs, key))
            out.members += theirs.members
            out.unscored += theirs.unscored
            out.actuals.update(theirs.actuals)
        return self

    def rows(self, change: float = 0.01) -> list[dict]:
        rows = []
        for name, out in self.outputs.items():
            n = len(out.scores)
            row = dict(name=name, kind=out.kind, n=n, unscored=out.unscored, sims=None, score=None, reference=None,
                       skill=None, se=None, sim_se=None, sims_needed=None)
            if n:
                mean = sum(out.scores) / n
                reference = climatology(out.kind, out.actuals)
                row.update(sims=out.members / n, score=mean, reference=reference,
                           skill=1 - mean / reference if reference else None)
                if n > 1:
                    row["se"] = math.sqrt(sum((s - mean) ** 2 for s in out.scores) / (n - 1) / n)
                if out.halves:  # a half difference has 4 times the full ensemble's sim variance
                    row["sim_se"] = math.sqrt(sum(d * d for d in out.halves) / len(out.halves) / n) / 2
                    if mean:
                        needed = row["sims"] * (2 * math.sqrt(2) * row["sim_se"] / (change * abs(mean))) ** 2
                        row["sims_needed"] = min(SIMS_CEILING, math.ceil(needed))
            rows.append(row)
        return rows

    def pit(self, name, bins: int = 10) -> list[float]:
        return histogram(self.outputs[name].pits, bins)

    def reliability(self, name, bins: int = 10) -> list[tuple[float, float, int]]:
        out = self.outputs[name]
        classes = {True} if out.kind == "binary" else set(out.actuals).union(*(shares for shares, _ in out.forecasts))
        return reliability([(shares.get(c, 0.0), actual == c) for shares, actual in out.forecasts for c in classes], bins)
