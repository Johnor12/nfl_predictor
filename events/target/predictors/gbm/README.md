# trained target predictor (gbm)

How far downfield a pass is thrown, from a trained model: gradient-boosted trees fitted to every real targeted pass of the seasons before the game's. Who is thrown to and the direction are the [baseline](../baseline/README.md)'s.

API (`from events.target.predictors.gbm import predict`, or `play.load_predictors()`: it is the target event's default):

- `predict(ctx, lineups, formation, eligible, rng) -> Target`
- `air_yards(ctx, formation, receiver, rng) -> float`: one draw of the pass's air yards.

What the model reads (`inputs.py`):

- the situation and the game so far (`events/situation.py`), and whether the offense is in the shotgun;
- the receiver: his position, how deep he has been thrown to (air yards per target), this season before the game (`Player.stats`) and over earlier seasons (`Player.career`), and his targets this season.

A distribution, not a number: the model gives the probability that the pass reaches each of its cuts (`CUTS`: every yard from 6 behind the line to 20 past it, wider after that). A draw picks the two cuts the pass falls between; where they are more than a yard apart, the baseline's histogram picks the yard. The model is told how far each cut is from the goal line, since passes pile up there and in the end zone behind it.

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it. A later season uses the latest model; a season before the first model (2021) and a try get the baseline's histogram.

Training: `python -m events.target.predictors.gbm.train` (`2026` for one season, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once. Retrain once a year, when a season is complete.

Scoring: `python -m evaluators.play` (`target: air yards`) and `python -m evaluators.game` (the receivers' yards), against the same runs with `--swap target=baseline`.
