# trained snap predictor (gbm)

Run or pass from a trained model: gradient-boosted trees fitted to every real run and dropback of the seasons before the game's. Everything else about the snap (the ball carrier, bad snaps, kneels, spikes, two-point plays, kicking units) is the [baseline](../baseline/README.md)'s.

API (`from events.snap.predictors.gbm import predict`, or `play.load_predictors()`: it is the snap event's default):

- `predict(ctx, lineups, formation, defense, allowed_actions, rng) -> Snap`
- `pass_rate(ctx, lineups, formation, defense) -> float`: the model's probability that the offense drops back on this scrimmage down.

What the model reads (`inputs.py`), all of it known before the snap:

- the situation: down, distance, yards to the goal line, quarter and clock, the score, both teams' timeouts, whether the clock is running, home or away, and the season;
- the game so far: the offense's dropbacks and runs, the length of its current drive, and what its last play was and gained;
- how the two teams lined up on this play: the offense's personnel group (`lineups.offense.personnel`: its backs, tight ends, and extra linemen), whether it is in the shotgun (`formation.under_center`), and the defenders in the box (`defense.box`);
- who is playing: the offense's pass rating (how much more it has dropped back than its situations called for, per play: `events.strength.rating`), and the same for the offenses that have faced this defense.

The first two groups are `events/situation.py`'s, shared with the trained offensive formation predictor, which is what makes the third usable: the formation the model is told has to fit the rest of what it knows about the play (`MAINTAINER.md`). It doesn't read the betting lines, though they are in the game's inputs.

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it, so no game is predicted by a model that has seen its season. A later season uses the latest model; a season before the first model (2021) gets the baseline's pass rate.

Training (`python -m events.snap.predictors.gbm.train`): retrains the models of the six most recent seasons (`2026` for one, `2021-2026` for a range). The personnel group is only in the data from 2016 on and the box from 2022 on; before that they are unknown to the model (nan). The first run turns every real play since 2011 into a row of the features above (cached in `.cache/training/`); a model then takes about 5 seconds. `python -m events.training` retrains every trained predictor at once. Retrain once a year, when a season is complete.

Scoring: `python -m evaluators.play` and `python -m evaluators.game`, against the same runs with `--swap snap=baseline`.
