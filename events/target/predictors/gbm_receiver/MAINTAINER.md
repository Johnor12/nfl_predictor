# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `receiver` and the gbm predictor's `air_yards`) and `receiver` (one of the eligible players, by the season's model; the baseline's choice on a try, when the season has no model, or when no back, receiver, or tight end is eligible).
- inputs.py: `NAMES`, `RECEIVERS`, and `candidates(ctx, players, shotgun)`, the one place the model's inputs are read, for training and for predicting: a row per player.
- train.py: `example` (a real targeted pass as a row per back, receiver, and tight end on the field), `train(season)`, `TABLES`, and the CLI.
- model_<season>.txt: the model for that season's games (LightGBM's text format, about 0.5 MB), trained on 2016 up to the season before.
- test_gbm_receiver.py: who is thrown to follows his targets; synthetic plays stay valid.

Measured (2026-11-16, the evaluators' default 160 games of 2021 to 2026 at 100 sims, case by case against the default, whose receiver is the baseline's):
- Game evaluator, the rows it is meant to move: no receiver row is better beyond noise. A second receiver's targets are 2.9% worse (3.2 standard errors) and a fullback's receiving yards 5.3% worse (3.0); a first receiver's, a first tight end's, and a third receiver's targets are 0.6% to 1.0% worse (about 1 standard error each), and the backs' are level.
- The game rows lean the other way (`game: margin` -1.7%, 1.8 standard errors; `game: home win` -4.4%, 2.4), which is less than a 160-game run can tell from simulating alone (2.5% and 4.7%: `evaluators/game/README.md`). A `--games 480` comparison would say whether that is real; until it does, a receiver choice that doesn't help the receivers isn't the default.

Notes:
- Not the default: `events/target/predictors/__init__.py` names `gbm`, whose receiver is the baseline's (his depth chart role's rate, moved toward his own targets per snap).
- A choice among players can't be a model with a class per player (the candidates change from play to play), so this is a yes/no model of "this player is the one thrown to", asked about every eligible player in one call (`shared.models.models_of(..., several=True)`), and the pass is drawn in proportion to its answers (`shared.models.choose`). What makes the rows of one play hang together is in the inputs: each player's rate as a share of the eligible players' rates, and who else is eligible. `share` carries most of the model (five times the gain of the next input).
- It is trained on the players really on the field (the participation files, 2016 to 2025) and asked about the formation's eligible players, which are the same backs, receivers, and tight ends. The training table has a row per candidate (`events.training`: an example may return several rows), about 90,000 a season.
- A player's rates are the same in every row of his game, so the model's leaves are kept large (`LEAF`, 1,000 rows) to keep it from learning one player's game. Nothing else about it was tuned: the inputs and settings are a first attempt, not chosen on earlier seasons.
- What it would take to beat the baseline is probably not a bigger model of the same inputs: the baseline already reads the one input that matters (his own targets per snap, next to his role's). What neither reads: who the quarterback is and whom he favours, the routes a player runs (a snap on which he blocks counts against him), and the coverage.
- After changing `inputs.py` or `example`, delete `.cache/training/target_gbm_receiver_*.parquet` and retrain every model.
