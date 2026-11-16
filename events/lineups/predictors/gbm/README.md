# trained lineups predictor (gbm)

The fourth-down decision (go for it, punt, or kick a field goal) from a trained model: gradient-boosted trees fitted to every real fourth down of the seasons before the game's. Everything else about the lineups (the kneel and end-of-half rules, two-point tries, onside kicks, the personnel group and the defense's package, and the players) is the [baseline](../baseline/README.md)'s.

API (`from events.lineups.predictors.gbm import predict`, or `play.load_predictors()`: it is the lineups event's default):

- `predict(ctx, rng) -> Lineups`
- `units(ctx) -> {"offense": p, "punt": p, "field_goal": p}`: the model's probabilities on a fourth down. A real fake punt or field goal was the kicking unit's (`shared.priors.sent_out`); the snap event decides to fake.

What the model reads (`inputs.py`):

- the situation and the game so far (`events/situation.py`): distance, field position, the score, the quarter and clock, timeouts;
- the team: how often it has gone for it on fourth down, this season before the game and over earlier seasons (`Game.form`), read coarsely (`shared/models/README.md`).

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it. A later season uses the latest model; a season before the first model (2021) and every other down get the baseline's counts.

Training: `python -m events.lineups.predictors.gbm.train` (`2026` for one season, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once. Retrain once a year, when a season is complete.

Scoring: `python -m evaluators.play` (`lineups: unit (4th down)`) and `python -m evaluators.game` (`team: punts`, `team: fg_att`), against the same runs with `--swap lineups=baseline`.
