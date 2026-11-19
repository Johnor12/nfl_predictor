# trained pass result predictor (gbm)

Complete, incomplete, or intercepted from a trained model: gradient-boosted trees fitted to every real targeted pass of the seasons before the game's. Who defends or intercepts the pass, and how long it is in the air, are the [baseline](../baseline/README.md)'s.

API (`from events.pass_result.predictors.gbm import predict`, or `play.load_predictors()`: it is the pass result event's default):

- `predict(ctx, lineups, target, rng) -> PassResult`
- `results(ctx, lineups, target) -> {"complete": p, "incomplete": p, "intercepted": p}`: the model's probabilities for this pass.

What the model reads (`inputs.py`):

- the situation and the game so far (`events/situation.py`), how far downfield the pass is thrown (`target.air_yards`), how far short of the goal line it arrives (negative in the end zone), and the receiver's position;
- the quarterback on the field: his completion rating (his completions over what his throws were expected to complete, per attempt: `events.strength.rating`), and his interceptions per attempt this season before the game (`Player.stats`) and over earlier seasons (`Player.career`);
- the defense: the same rating and rates of the passes thrown against it (`Game.form`).

The ratings are read exactly; the interception rates coarsely, and the home input counts for more than its gain per pass (`shared/models/README.md`).

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it. A later season uses the latest model; a season before the first model (2021) and a try get the baseline's rates.

Training: `python -m events.pass_result.predictors.gbm.train` (`2026` for one season, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once. Retrain once a year, when a season is complete.

Scoring: `python -m evaluators.play` (`pass_result: result`) and `python -m evaluators.game` (the first quarterback's completions, yards, and interceptions), against the same runs with `--swap pass_result=baseline`.
