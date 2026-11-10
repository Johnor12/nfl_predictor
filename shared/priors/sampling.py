# START
# Sampling from priors (raw counts and histograms).
# - choice(weights, rng): a key of a {key: weight} dict, sampled by weight.
# - hist(histogram, rng) -> float: a value from a {"value": count} histogram.
# - rate(counts, key) -> float: the key's share of the counts (0 if there are none).
# - blend(counts, fallback, k=10): counts backed off to a coarser distribution, worth k samples.
# END


def choice(weights, rng):
    keys = [k for k, v in weights.items() if v > 0]
    return rng.choices(keys, [weights[k] for k in keys])[0]


def hist(histogram, rng) -> float:
    return float(choice(histogram, rng))


def rate(counts, key) -> float:
    total = sum(counts.values())
    return counts.get(key, 0) / total if total else 0.0


def blend(counts, fallback, k=10.0) -> dict:
    total = sum(fallback.values()) or 1
    keys = sorted(set(counts) | set(fallback))  # sorted: sampling must not depend on set order
    return {key: counts.get(key, 0) + k * fallback.get(key, 0) / total for key in keys}
