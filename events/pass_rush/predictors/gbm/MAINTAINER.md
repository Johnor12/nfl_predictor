# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `dropback`) and `dropback` (the season's model on a scrimmage down; the baseline's on a try, or when the season has no model).
- inputs.py: `NAMES`, `WHO`, `RESULTS`, and `features(ctx, qb, shotgun)`, the one place the model's inputs are read, for training and for predicting.
- train.py: `example` (a real dropback as a training row), `train(season)`, `TABLES`, and the CLI.
- model_<season>.txt: the model for that season's games (LightGBM's text format, about 0.4 MB), trained on 2011 up to the season before.
- test_gbm.py: the model reads the situation and the quarterback; synthetic plays stay valid; the fallback before the first model.

Measured (2026-11-15, the evaluators' default 160 games of 2021 to 2026 at 100 sims, case by case, against the system before the trained predictors of that day, and against this model's blind twin: the same model trained with the inputs about who is playing blanked out; `events/MAINTAINER.md` has the whole system's game scores):
- Play evaluator: `pass_rush: result` 0.2609 -> 0.2586 against the baseline (-0.9%, 1.1 standard errors), and 0.2606 -> 0.2586 against the blind twin (-0.8%, 4.4 standard errors). So the model without the quarterback is about what the baseline was, hand-set shrinking included, and the gain is the quarterback's own history.
- Game evaluator: the first quarterback's rushing yards 9.13 -> 8.81 against the baseline (-3.5%, 1.9 standard errors) and 10.53 -> 8.81 against the blind twin (-16%, 6.5 standard errors); `team: sacked` +1.4% against the baseline (0.8 standard errors) and -2.6% against the twin (1.6).

Notes:
- Out of sample: a season's model has seen nothing of that season, and the inputs and settings were chosen on 2019 and 2020 with models trained on 2011 to 2018.
- What each input was worth there, per dropback (three-class Brier) and per team and game (the summed probabilities against what happened, squared): the quarterback's sack and scramble rates and his dropbacks, read coarsely, -0.9% and -18%; his team's rates instead, -0.5% and -12%; his years in the league alone, -0.3% and -7%. The defense's sack and scramble rates made it worse (+0.2%, +1%), and so did every one of them read exactly.
- His draft pick looked worth -0.35% and -9.5% read exactly and nothing read coarsely: an exact pick number names the quarterback, and the model was learning the quarterbacks it had seen. His own rates say the same thing honestly.
- The model replaces the baseline's hand-set shrinking of a quarterback's season toward the league (`DROPBACKS`): it gets his season and his earlier seasons as two rates and the dropbacks behind this season's, and weighs them itself.
- 40 rounds, not the 150 of `shared.models`' defaults: on 2019 and 2020 the score rose with every round after about 40 (0.1862 at 25 and 40, 0.1870 at 150).
- A throwaway is a throw to the model, since the data only tells them apart from 2022. The baseline draws it afterwards from the charted rate.
- Not read: the pass rushers, the line, or the box. `defense.box` is there to be tried.
- After changing `inputs.py` or `example`, delete `.cache/training/pass_rush_gbm_*.parquet` and retrain every model.
