# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `shotgun_rate`) and `shotgun_rate` (the season's model when the offense is out on a scrimmage down; the baseline's otherwise, or when the season has no model).
- inputs.py: `NAMES` and `features(ctx, group)`, the one place the model's inputs are read, for training and for predicting: `events.situation`'s, plus the personnel group.
- train.py: `example` (a real play as a training row), `train(season)`, and the CLI.
- model_<season>.txt: the model for that season's games (LightGBM's text format, about 0.5 MB), trained on 2011 up to the season before.
- test_gbm.py: the model reads the situation and the personnel; synthetic plays stay valid; the fallbacks (before the first model, other units).

Measured (2026-11-15, the evaluators' default 160 games of 2021 to 2026 at 100 sims, against the baseline case by case; it became the event's default on that day, together with the snap model's formation inputs):
- Play evaluator: `offensive_formation: shotgun` 0.1572 -> 0.1455 (-7.4%, 19 standard errors; skill +26.4% -> +31.8%).
- What it is for is the snap: see `events/snap/predictors/gbm/MAINTAINER.md` for what the pair did to run or pass, end to end.

Notes:
- What each input is worth, on the 192,588 real runs and dropbacks of 2021 to 2026, each season scored by its own model (two-class Brier, twice the evaluators' `shotgun` row): the situation and the game so far 0.3282, with the personnel group 0.3004 (-8.5%). The same on 2019 and 2020 with models trained on 2011 to 2018, where the inputs were chosen: -11.6%.
- The personnel group is not optional. Without it the model scored worse than the baseline in the play evaluator (+2.9% on 48 games at 30 sims), because the baseline does read the group (by down and distance).
- Tried and left out: the defense's package (its defensive backs, which the offense sees before it lines up). Worth another 0.8% on real plays (2.0% on 2019 and 2020), but in a simulated play the package comes from a count by personnel group alone (`lineups`' `_package`), which knows nothing of the situation. It belongs back in once the package is predicted from the situation: a column in `inputs.py`, `lineups.defense.personnel` in `shotgun_rate`, and `shared.priors.package(sample)` in `example`.
- The personnel group is only recorded from 2016 on (nan before, and in 2026 so far). In a simulated play it is always there, from the lineups baseline.
- Not read: the team. Offenses differ a lot in how often they are in the shotgun, and nothing in the context says which one this is (the root README's goal on team strength). That, not another input about the play, is where the rest of this event's score is.
- The settings are `shared.models`' defaults, as for the snap model; nothing else was tried.
- After changing `inputs.py` or `example`, delete `.cache/training/offensive_formation_gbm_*.parquet` and retrain every model, and the snap's too if `events/situation.py` changed (both read it).
- Retraining gives the same file from the same table. A season in progress isn't trained on.
