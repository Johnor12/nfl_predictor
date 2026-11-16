# trained offensive formation predictor (gbm)

Shotgun or under center from a trained model: gradient-boosted trees fitted to every real run and dropback of the seasons before the game's. The alignment (who is on the line, who is in the backfield, the punt and field goal units) is the [baseline](../baseline/README.md)'s.

API (`from events.offensive_formation.predictors.gbm import predict`, or `play.load_predictors()`: it is the offensive formation event's default):

- `predict(ctx, lineups, rng) -> Formation`
- `shotgun_rate(ctx, lineups) -> float`: the model's probability that the offense lines up in the shotgun on this scrimmage down.

What the model reads (`inputs.py`), all of it known as the offense lines up:

- the situation and the game so far, as the run-or-pass model reads them (`events/situation.py`): down, distance, yards to the goal line, quarter and clock, the score, both teams' timeouts, whether the clock is running, home or away, the season, the offense's dropbacks and runs, the length of its current drive, and what its last play was and gained;
- the personnel group the lineups event sent out (`lineups.offense.personnel`): its backs, tight ends, and extra linemen;
- the team: how often it has been in the shotgun, this season before the game and over earlier seasons, and the plays this season's rate rests on (`Game.form`, through `events/strength.py`).

Why it exists: the run-or-pass model (`events/snap/predictors/gbm/`) reads the formation, and a formation drawn from down and distance alone doesn't fit the rest of what that model knows about the play. This one reads what that one reads, so the two agree.

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it. A later season uses the latest model; a season before the first model (2021), a kicking or victory unit, and a try get the baseline's rate.

Training (`python -m events.offensive_formation.predictors.gbm.train`): retrains the models of the six most recent seasons (`2026` for one, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once. The first run turns every real play since 2011 into a row of the features above (cached in `.cache/training/`); a model then takes about 5 seconds. Retrain once a year, when a season is complete, together with the snap model.

Scoring: `python -m evaluators.play` (`offensive_formation: shotgun`, and `play: action (scrimmage)` for what it does to the snap), against the same run with `--swap offensive_formation=baseline`.
