# trained punt kick predictor (gbm)

How far a punt goes, from a trained model: gradient-boosted trees fitted to every real punt of the seasons before the game's. Blocked punts and the hang time are the [baseline](../baseline/README.md)'s.

API (`from events.punt_kick.predictors.gbm import predict`, or `play.load_predictors(punt_kick="gbm")`; the event's default is the baseline, see `MAINTAINER.md`):

- `predict(ctx, lineups, punter, rng) -> PuntKick`
- `distance(ctx, punter, rng) -> float`: one draw of the punt's distance.

What the model reads (`inputs.py`):

- the situation and the game so far (`events/situation.py`): above all where the punt is from;
- the weather: temperature, wind, and whether the game is outdoors (`Game.temperature`, `wind`, `roof`);
- the punter: his yards per punt this season before the game (`Player.stats`) and over earlier seasons (`Player.career`).

The weather and the punter's inputs are read coarsely (`shared/models/README.md`).

A distribution, not a number: the model gives the probability that the punt reaches each of its cuts (`CUTS`: every 2 yards from 24 to 64). A draw picks the two cuts the punt falls between, and the baseline's histogram the yard. The model is told how far each cut is from the goal line, where a punt into the end zone is recorded.

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it. A later season uses the latest model; a season before the first model (2021) gets the baseline's histogram.

Training: `python -m events.punt_kick.predictors.gbm.train` (`2026` for one season, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once. Retrain once a year, when a season is complete.

Scoring: `python -m evaluators.play` (`punt_kick: distance`), against the same run with `--swap punt_kick=baseline`.
