# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `yards`) and `yards` (a draw from the run or the catch model on a scrimmage down; the baseline's for another kind of carry, on a try, or when the season has no model).
- inputs.py: `RUN`, `CATCH`, their `_WHO` and `_CUTS`, and `run(ctx, carrier)` and `catch(ctx, receiver, yard_line)`, the one place the models' inputs are read, for training and for predicting.
- train.py: `run_example` and `catch_example` (a real run or completion as a training row), `train(season)`, `TABLES`, and the CLI.
- run_<season>.txt, catch_<season>.txt: the models for that season's games (LightGBM's text format, about 0.5 MB each), trained on 2011 up to the season before.
- test_gbm.py: the models read the carrier and know the goal line; other carries are the baseline's; synthetic plays stay valid; the fallback before the first model.

Measured (2026-11-15, the evaluators' default 160 games of 2021 to 2026 at 100 sims, case by case, against the system before the trained predictors of that day, and against this model's blind twin: the same model trained with the inputs about who is playing blanked out; `events/MAINTAINER.md` has the whole system's game scores):
- Play evaluator: `carry: yards (run)` 2.626 -> 2.608 against the baseline (-0.7%, 3.1 standard errors), `carry: yards (catch)` 2.817 -> 2.766 (-1.8%, 4.8), `carry: end (run)` -2.0% (3.6: the touchdowns). Against the blind twin nothing moves (run -0.04%, catch +0.07%): the gain is the situation, not the carrier.
- End to end, with the other trained predictors of that day: `play: yards (scrimmage)` -0.5% (3.5 standard errors), `play: touchdown (scrimmage)` -2.3% (3.6), `play: points for minus against (scrimmage)` -3.6% (5.9).
- Game evaluator: the first back's rushing yards -1.3% against the baseline and -1.2% against the blind twin (both 1 standard error); his touchdowns -6.4% against the baseline (3.4 standard errors) and -4.3% against the twin (2.3).

Notes:
- Out of sample: a season's models have seen nothing of that season, and the inputs and settings were chosen on 2019 and 2020 with models trained on 2011 to 2018.
- What each input was worth there, per carry (squared error of the expected yards) and per team and game (expected against real yards, squared), read coarsely. Runs: the carrier's yards per rush -0.1% and -3%, his team's yards per designed run -0.2% and -3%, both with the defense's -0.4% and -4.5%; the defense's alone, the carrier's years in the league, his draft pick, the surface, and the weather nothing or worse. Catches: the receiver's yards after the catch per reception -0.3% and -3%; the offense's, the defense's, the surface, and the weather nothing.
- These are small. Most of what a run gains is the play, not the runner, and a model can't be shown much of the rest: it doesn't see the blocking, the box, or the formation (the carry event isn't handed them).
- Each model is one yes/no model of "the carry reaches this cut" for all the cuts (`shared.models.fit_number`), a yard apart up to 15; beyond that the baseline's histogram fills in the yard.
- A carry that starts a few yards from the goal line can't gain more than that, and real carries stop there: a touchdown from the 3 is a gain of exactly 3. Each model is fitted with the yards to the goal line as its limit (`RUN_LIMIT`, `CATCH_LIMIT`; `shared/models/MAINTAINER.md` has what went wrong without it), and `yards` takes a draw between two wide cuts that hold the goal line from the histogram's whole tail, because that is what the model's probability there covers. The first version did neither: simulated games had the real yards and 80% of the real rushing touchdowns. The baseline's goal-to-go histograms are only used to fill in a wide cut.
- Scrambles and returns are the baseline's: few of them (6,000 scrambles in eight seasons) for a model of a distribution. A lateral's second carry is asked of the same model as the first.
- After changing `inputs.py` or an `example`, delete `.cache/training/carry_*_gbm_*.parquet` and retrain every model.
