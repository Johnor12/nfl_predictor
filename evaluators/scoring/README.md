# scoring

The evaluators' shared toolkit: scores a forecast against what really happened. It knows nothing about football, so every evaluator (plays and events now, games and seasons later) uses the same scores.

A forecast is an ensemble: the values a simulator produced for one case (a play's yards over 100 simulated plays). The kind of output decides the score, and comes from the type of the values:

| values | kind | score |
|---|---|---|
| numbers | numeric | fair CRPS, in the output's units |
| True / False | binary | fair Brier (fair CRPS on 0/1) |
| strings | categorical | fair multiclass Brier: the fair Brier of each class, summed (0 to 2) |

Lower is better. "Fair" means the score doesn't depend on how many times the case was simulated (2 or more).

API (`from evaluators.scoring import ...`):

- `Scorecard`: scores many cases, grouped by output name.
  - `add(name, samples, actual)`: one case. `None` samples are dropped; a case left with fewer than 2 is counted as unscored.
  - `rows() -> list[dict]`, one per output: `name`, `kind`, `n`, `unscored`, `sims` (mean ensemble size), `score` (mean), `reference`, `skill`, `se`, `sim_se`, `sims_needed`.
  - `pit(name)`: a numeric output's PIT histogram (10 shares; flat is calibrated).
  - `reliability(name)`: a binary or categorical output's `(mean forecast probability, observed rate, n)` by probability bin.
  - `merge(other)`: fold in a scorecard built in another process.
- `fair_crps(samples, actual)`, `fair_brier(samples, actual)`, `score(kind, samples, actual)`, `kind_of(actual)`.
- `climatology(kind, actuals)`: the reference score (see below).
- For a stated probability (a betting line's): `brier(p, happened)`, `log_loss(p, happened)`, and `probability(samples)`, a smoothed share of True samples that is never 0 or 1, so a simulator's probability can take a log loss.
- `pit(samples, actual, u)`, `histogram(values)`, `reliability(pairs)`: the diagnostics on their own.
- Reports: `OUT` (`evaluation_output/`, gitignored), `GUIDE` (how to read a score table), `score_table(rows)`, `pit_table(card, names)`, `reliability_table(card, names)`: markdown lines.

Reading a row:

- **reference**: the score of forecasting every case with the overall distribution of real outcomes (each case forecast from all the others). A forecast that knows nothing about the case scores this.
- **skill**: `1 - score / reference`. 0 is no better than the reference, 1 is perfect, negative is worse than knowing nothing.
- **se**: the standard error of the mean score over the cases. Two evaluations of the same cases share most of this error, so a difference between them can be real well inside it.
- **sim_se**: the part of the error that comes from simulating a finite number of times. Each case is also scored on the two halves of its ensemble (the same predictor with two seeds); the spread between the halves gives it.
- **sims_needed**: the sims per case at which a 1% change in the score stands 2 standard errors clear of sim noise when two runs are compared (capped at 10,000).
