# START
# Scores for forecasts: an ensemble of simulated values (or a stated probability) against what really happened.
# Lower is better for every score. "Fair" scores are unbiased for any ensemble size (2 or more).
# - kind_of(actual) -> str: numeric, binary, or categorical, from the value's type (number, bool, str).
# - fair_crps(samples, actual): fair CRPS for numbers. On True/False samples it is the fair Brier score.
# - fair_brier(samples, actual): fair multiclass Brier for categories: fair_crps of each class's indicator,
#   summed over the classes (0 is perfect, 2 the worst).
# - score(kind, samples, actual): the fair score for the kind.
# - climatology(kind, actuals): the mean fair score of forecasting each case with every other case's outcome
#   (actuals is a Counter of the outcomes): the reference a forecast has to beat.
# - probability(samples) -> float: smoothed share of True samples, (k + 0.5) / (m + 1); never 0 or 1.
# - brier(p, happened) / log_loss(p, happened): scores for a stated probability (a betting line's, or a smoothed one).
# - pit(samples, actual, u) -> float: where the outcome falls in the ensemble, 0-1, ties broken by u in [0, 1).
# - histogram(values, bins=10) -> [share]: shares of 0-1 values per bin (a PIT histogram; flat is calibrated).
# - reliability(pairs, bins=10) -> [(mean probability, observed rate, n)]: (probability, happened) pairs by
#   probability bin, empty bins left out (a reliability diagram; calibrated when the first two match).
# END
import math


def kind_of(actual) -> str:
    if isinstance(actual, bool):
        return "binary"
    if isinstance(actual, str):
        return "categorical"
    if isinstance(actual, (int, float)):
        return "numeric"
    raise TypeError(f"can't score a {type(actual).__name__}: outcomes are a plain bool, str, or number")


def fair_crps(samples, actual) -> float:
    m = len(samples)
    ordered = sorted(samples)
    error = sum(abs(x - actual) for x in ordered) / m
    spread = sum(x * (2 * i - m + 1) for i, x in enumerate(ordered)) / (m * (m - 1))  # half the mean |x - x'|
    return error - spread


def fair_brier(samples, actual) -> float:
    return sum(fair_crps([x == c for x in samples], actual == c) for c in set(samples) | {actual})


def score(kind, samples, actual) -> float:
    return fair_brier(samples, actual) if kind == "categorical" else fair_crps(samples, actual)


def climatology(kind, actuals) -> float | None:
    n = sum(actuals.values())
    if n < 2:
        return None
    if kind == "categorical":
        return sum(k * (n - k) for k in actuals.values()) / (n * (n - 1))
    pairs, seen, total = 0.0, 0, 0.0  # sum of |x - y| over every pair of outcomes
    for value, count in sorted(actuals.items()):
        pairs += count * (value * seen - total)
        seen += count
        total += count * value
    return pairs / (n * (n - 1))


def probability(samples) -> float:
    return (sum(samples) + 0.5) / (len(samples) + 1)


def brier(p, happened) -> float:
    return (p - happened) ** 2


def log_loss(p, happened) -> float:
    return -math.log(p if happened else 1 - p)


def pit(samples, actual, u) -> float:
    below = sum(x < actual for x in samples)
    ties = sum(x == actual for x in samples)
    return (below + u * (ties + 1)) / (len(samples) + 1)


def histogram(values, bins: int = 10) -> list[float]:
    counts = [0] * bins
    for v in values:
        counts[min(bins - 1, int(v * bins))] += 1
    return [c / len(values) for c in counts] if values else []


def reliability(pairs, bins: int = 10) -> list[tuple[float, float, int]]:
    groups = [[] for _ in range(bins)]
    for p, happened in pairs:
        groups[min(bins - 1, int(p * bins))].append((p, happened))
    return [(sum(p for p, _ in g) / len(g), sum(h for _, h in g) / len(g), len(g)) for g in groups if g]
