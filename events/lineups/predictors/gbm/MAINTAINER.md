# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `units`) and `units` (the season's model on a fourth down; the baseline's on any other down, or when the season has no model).
- inputs.py: `NAMES`, `WHO`, `UNITS`, and `features(ctx)`, the one place the model's inputs are read, for training and for predicting.
- train.py: `example` (a real fourth down as a training row), `train(season)`, `TABLES`, and the CLI.
- model_<season>.txt: the model for that season's games (LightGBM's text format, about 1 MB), trained on 2011 up to the season before.
- test_gbm.py: the model reads the situation and the team; other downs are the baseline's; synthetic plays stay valid; the fallback before the first model.

Measured (2026-11-15, the evaluators' default 160 games of 2021 to 2026 at 100 sims, case by case, against the system before the trained predictors of that day, and against this model's blind twin: the same model trained with the inputs about who is playing blanked out; `events/MAINTAINER.md` has the whole system's game scores):
- Play evaluator: `lineups: unit (4th down)` 0.2513 -> 0.1444 against the baseline (-43%, 13 standard errors; skill +58% -> +76%), and 0.1483 -> 0.1444 against the blind twin (-2.6%, 2.5 standard errors).
- Game evaluator: `team: punts` -0.8% against the baseline (0.6 standard errors) and -2.2% against the twin (1.8); `team: fg_att` -0.6% and 0.0%. A team makes about four of these decisions a game, so even a much better decision moves a game's totals little.

Notes:
- Out of sample: a season's model has seen nothing of that season, and the inputs and settings were chosen on 2019 and 2020 with models trained on 2011 to 2018.
- Most of the gain is the situation, not the team: the baseline counts by down, distance, and field position, and the decision also turns on the score and the clock, which the model reads.
- What the team was worth there, per fourth down (three-class Brier) and per team and game: how often it has gone for it, read coarsely, -1.1% and -2%; its head coach's rate instead -0.4% and -2%; both together no better than the team's alone. Read exactly, each made it worse (+2 to +4%). The offense's points per game, its quarterback, and the weather added nothing.
- The coach is in the game's inputs (`game.form(game.home_coach)`), and his form follows him to a new team, which the team's doesn't. It wasn't worth a place here: within a season the two are the same numbers, and there are few first seasons to learn the difference from.
- 100 rounds: on 2019 and 2020 the score was best there (0.1220 against 0.1232 at 150). A fourth down is rare (4,000 a season), so this is the smallest table of the trained predictors.
- The baseline's hand-set rules run first and aren't the model's: the kneel, and the field goal at the end of a half.
- Teams go for it more every season. The season is an input, but a model can't know the season after its last: 2026's model was trained through 2025.
- A fake punt or field goal is the kicking unit's (`shared.priors.sent_out`): the coach sent that unit out, and the snap event decides to fake. Before 2026-11-16 the about 20 fakes a season were labeled as going for it; relabeled and retrained, `lineups: unit (4th down)` went 0.1490 -> 0.1382 on the evaluators' default games (the real unit of a fake changed with it, so this is the label, not a better model). The team's go rate (`fourth_down_goes`, `shared/nflverse/form.py`) still counts a fake as going for it.
- After changing `inputs.py` or `example`, delete `.cache/training/lineups_gbm_*.parquet` and retrain every model.
