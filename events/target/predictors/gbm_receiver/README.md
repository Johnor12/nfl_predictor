# trained receiver choice (gbm_receiver)

Who a pass is thrown to, from a trained model: gradient-boosted trees fitted to the real targeted passes of the seasons before the game's. How far downfield is the [gbm](../gbm/README.md) predictor's model; the direction is the [baseline](../baseline/README.md)'s.

API (`from events.target.predictors.gbm_receiver import predict`, or `play.load_predictors(target="gbm_receiver")`; the event's default is `gbm`, see `MAINTAINER.md`):

- `predict(ctx, lineups, formation, eligible, rng) -> Target`
- `receiver(ctx, formation, eligible, rng) -> str`: who is thrown to.

A choice among players: the model is a yes/no model of one player ("he is the one thrown to"), asked about each eligible back, receiver, and tight end in one call; the pass goes to one of them in proportion to its answers. A quarterback or a lineman who is eligible is only thrown to when nobody else is (the baseline's choice, as on a try and in a season before the first model).

What the model reads about each player (`inputs.py`):

- the situation and the game so far (`events/situation.py`), and whether the offense is in the shotgun;
- the player: his position and depth chart rank, his targets per snap on offense this season before the game (`Player.stats`) and over earlier seasons (`Player.career`), each also as his share of the eligible players' rates added up, his targets this season, how deep he is thrown to, and his years in the league;
- who is eligible with him: how many players, and how many of them receivers, tight ends, and backs.

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2016 (the first that records who was on the field) up to the one before it. A later season uses the latest model.

Training: `python -m events.target.predictors.gbm_receiver.train` (`2026` for one season, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once.

Scoring: `python -m evaluators.game --swap target=gbm_receiver` (every receiver's targets, catches, and yards) and `python -m evaluators.play --swap target=gbm_receiver` (`target: receiver`), against the same runs without the swap.
