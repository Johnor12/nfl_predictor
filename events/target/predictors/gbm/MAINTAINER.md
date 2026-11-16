# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `air_yards`) and `air_yards` (a draw from the season's model on a scrimmage down; the baseline's on a try, or when the season has no model).
- inputs.py: `NAMES`, `CUTS`, and `features(ctx, receiver, shotgun)`, the one place the model's inputs are read, for training and for predicting.
- train.py: `example` (a real targeted pass as a training row), `train(season)`, `TABLES`, and the CLI.
- model_<season>.txt: the model for that season's games (LightGBM's text format, about 0.5 MB), trained on 2011 up to the season before.
- test_gbm.py: the model reads the receiver; passes stay on the field; synthetic plays stay valid; the fallback before the first model.

Measured (2026-11-15, the evaluators' default 160 games of 2021 to 2026 at 100 sims, case by case, against the system before the trained predictors of that day, and against this model's blind twin: the same model trained with the inputs about who is playing blanked out; `events/MAINTAINER.md` has the whole system's game scores):
- Play evaluator: `target: air yards` 5.255 -> 5.134 against the baseline (-2.3%, 4.9 standard errors), and 5.139 -> 5.134 against the blind twin (-0.1%, 0.7 standard errors). Nearly all of it is the situation (the baseline only knows the receiver's position); a receiver's own depth of target, worth 3.5% of the squared error on 2019 and 2020, is too small a part of the spread of a single pass to show in a score of the whole distribution.
- Game evaluator: the receivers' yards and catches are within noise of the blind twin's (the first receiver's catches -1.1%, 1.3 standard errors).

Notes:
- Out of sample: a season's model has seen nothing of that season, and the inputs and settings were chosen on 2019 and 2020 with models trained on 2011 to 2018.
- What each input was worth there, per pass (squared error of the expected air yards) and per team and game (expected against real air yards, squared), on top of the situation, the shotgun, and the receiver's position: the receiver's air yards per target and his targets -3.5% and -9%; the quarterback's air yards per attempt alone -0.3% and -5%, his team's the same, and neither added anything once the receiver's was in. The defense's and the weather added nothing.
- The receiver's inputs are read exactly, unlike most inputs about who is playing: coarse was a little worse here (-3.2% and -8%). There are hundreds of receivers, and a pass goes to one of them, so his rate doesn't mark a team's season the way a team's rate does.
- The model is one yes/no model of "the pass reaches this cut" for all the cuts (`shared.models.fit_number`). The cuts are a yard apart where passes are common; beyond 20 yards the baseline's histogram for the receiver's position fills in the yard.
- The baseline's goal-to-go histograms are only used that way now: the model is fitted with the yards to the goal line as its limit (`LIMIT`), so it knows how far each cut is from it. Passes aren't stopped there as carries are, but they pile up at the goal line and just behind it. `predict` still draws again when a pass would land past the end line.
- Who is thrown to is still the baseline's (depth chart role and his own targets). A trained receiver choice would be a model over the eligible players, which `shared.models` doesn't have.
- After changing `inputs.py` or `example`, delete `.cache/training/target_gbm_*.parquet` and retrain every model.
