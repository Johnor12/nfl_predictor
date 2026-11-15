# trained snap predictor (gbm)

Run or pass from a trained model: gradient-boosted trees fitted to every real run and dropback of the seasons before the game's. Everything else about the snap (the ball carrier, bad snaps, kneels, spikes, two-point plays, kicking units) is the [baseline](../baseline/README.md)'s.

API (`from events.snap.predictors.gbm import predict`, or `play.load_predictors()`: it is the snap event's default):

- `predict(ctx, lineups, formation, defense, allowed_actions, rng) -> Snap`
- `pass_rate(ctx, lineups, formation, defense) -> float`: the model's probability that the offense drops back on this scrimmage down.

What the model reads (`inputs.py`), all of it known before the snap:

- the situation: down, distance, yards to the goal line, quarter and clock, the score, both teams' timeouts, whether the clock is running, home or away, and the season;
- the game so far: the offense's dropbacks and runs, the length of its current drive, and what its last play was and gained.

It doesn't read the formation, the personnel group, or the box yet, so like the baseline it ignores `lineups`, `formation`, and `defense`. It doesn't read the betting lines either, though they are in the game's inputs. `MAINTAINER.md` says why, and what each was worth.

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it, so no game is predicted by a model that has seen its season. A later season uses the latest model; a season before the first model (2021) gets the baseline's pass rate.

Training (`python -m events.snap.predictors.gbm.train`): retrains the models of the six most recent seasons (`2026` for one, `2021-2026` for a range). The first run turns every real play since 2011 into a row of the features above (about 10 minutes on 4 cores, cached in `.cache/training/`); a model then takes about 5 seconds. Retrain once a year, when a season is complete: `python -m events.snap.predictors.gbm.train <next season>`.

Scoring: `python -m evaluators.play` and `python -m evaluators.game`, against the same runs with `--swap snap=baseline`.
