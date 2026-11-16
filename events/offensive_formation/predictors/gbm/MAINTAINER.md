# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `shotgun_rate`) and `shotgun_rate` (the season's model when the offense is out on a scrimmage down; the baseline's otherwise, or when the season has no model).
- inputs.py: `NAMES`, `WHO`, and `features(ctx, group)`, the one place the model's inputs are read, for training and for predicting: `events.situation`'s, the personnel group, and the team's shotgun rate (`events.strength`).
- train.py: `example` (a real play as a training row), `train(season)`, `TABLES`, and the CLI.
- model_<season>.txt: the model for that season's games (LightGBM's text format, about 0.5 MB), trained on 2011 up to the season before.
- test_gbm.py: the model reads the situation, the personnel, and the team; synthetic plays stay valid; the fallbacks (before the first model, other units).

Measured (2026-11-15, the evaluators' default 160 games of 2021 to 2026 at 100 sims, against the baseline case by case; it became the event's default on that day, together with the snap model's formation inputs):
- Play evaluator: `offensive_formation: shotgun` 0.1572 -> 0.1455 (-7.4%, 19 standard errors; skill +26.4% -> +31.8%).
- What it is for is the snap: see `events/snap/predictors/gbm/MAINTAINER.md` for what the pair did to run or pass, end to end.

Measured again with the team's shotgun rate (2026-11-15, the same 160 games at 100 sims, case by case, against the model without it; `events/MAINTAINER.md` has the whole system's game scores):
- Play evaluator: `offensive_formation: shotgun` 0.1500 -> 0.1401 (-6.6%, 12 standard errors; skill +29.9% -> +34.5%). It is the largest gain any input about who is playing gave any event.
- Where it was chosen, on 2019 and 2020 with models trained on 2011 to 2018: -12% per play, and the team's shotgun snaps over a game 60% closer (the model's summed probabilities against what happened, squared). The head coach's rate instead was worth the same, and both together no more: within a season they are the same numbers.
- It is read exactly, not coarsely like most inputs about who is playing (`shared/models/README.md`): coarse was worse here (-10.8% per play, -54% per game). The rate is so persistent that its exact value is worth more than the model loses by recognising a team's season.

Notes:
- What each input is worth, on the 192,588 real runs and dropbacks of 2021 to 2026, each season scored by its own model (two-class Brier, twice the evaluators' `shotgun` row): the situation and the game so far 0.3282, with the personnel group 0.3004 (-8.5%). The same on 2019 and 2020 with models trained on 2011 to 2018, where the inputs were chosen: -11.6%.
- The personnel group is not optional. Without it the model scored worse than the baseline in the play evaluator (+2.9% on 48 games at 30 sims), because the baseline does read the group (by down and distance).
- Tried and left out: the defense's package (its defensive backs, which the offense sees before it lines up). Worth another 0.8% on real plays (2.0% on 2019 and 2020), but in a simulated play the package comes from a count by personnel group alone (`lineups`' `_package`), which knows nothing of the situation. It belongs back in once the package is predicted from the situation: a column in `inputs.py`, `lineups.defense.personnel` in `shotgun_rate`, and `shared.priors.package(sample)` in `example`.
- The personnel group is only recorded from 2016 on (nan before, and in 2026 so far). In a simulated play it is always there, from the lineups baseline.
- The team is read through its past (`Game.form`): how often it was in the shotgun this season before the game and over the earlier seasons, and its plays this season. Not which team it is: a model fitted to earlier seasons has nothing to say about a name.
- The settings are `shared.models`' defaults, as for the snap model; nothing else was tried.
- After changing `inputs.py` or `example`, delete `.cache/training/offensive_formation_gbm_*.parquet` and retrain every model, and the snap's too if `events/situation.py` changed (both read it).
- Retraining gives the same file from the same table. A season in progress isn't trained on.
