# trained carry predictor (gbm)

The yards of a designed run and the yards after a catch, each from a trained model: gradient-boosted trees fitted to the real runs and completions of the seasons before the game's. Every other kind of carry (scrambles, returns, recoveries, kneels), how a carry ends, laterals, and the tacklers are the [baseline](../baseline/README.md)'s.

API (`from events.carry.predictors.gbm import predict`, or `play.load_predictors()`: it is the carry event's default):

- `predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd`
- `yards(ctx, kind, carrier, yard_line, rng) -> float`: one draw of the carry's yards.

What the models read (`inputs.py`):

- a run: the situation and the game so far (`events/situation.py`), the carrier's position, his yards per rush this season before the game (`Player.stats`) and over earlier seasons (`Player.career`), and his team's yards per designed run (`Game.form`);
- a catch: the situation and the game so far, how far downfield the ball was caught and how far that is from the goal line, the receiver's position, and his yards after the catch per reception, this season and over earlier ones.

The carrier's and the team's inputs are read coarsely (`shared/models/README.md`).

Distributions, not numbers: each model gives the probability that the carry reaches each of its cuts (`RUN_CUTS`, `CATCH_CUTS`: every yard up to 15, wider after that). A draw picks the two cuts the carry falls between; where they are more than a yard apart, the baseline's histogram picks the yard. The models are told how far each cut is from the goal line, where every longer gain ends, so there are no separate goal-to-go histograms.

Models: `run_<season>.txt` and `catch_<season>.txt` are the models for that season's games, trained on the seasons from 2011 up to the one before it. A later season uses the latest ones; a season before the first (2021) and a try get the baseline's histograms.

Training: `python -m events.carry.predictors.gbm.train` (`2026` for one season, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once. Retrain once a year, when a season is complete.

Scoring: `python -m evaluators.play` (`carry: yards (run)`, `carry: yards (catch)`, `play: yards (scrimmage)`) and `python -m evaluators.game`, against the same runs with `--swap carry=baseline`.
