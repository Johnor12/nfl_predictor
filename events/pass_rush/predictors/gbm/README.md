# trained pass rush predictor (gbm)

Throw, sack, or scramble from a trained model: gradient-boosted trees fitted to every real dropback of the seasons before the game's. Everything else about the dropback (throwaways, the rushers, who gets the sack and how many yards it loses, strip sacks, quarterback hits, the timing) is the [baseline](../baseline/README.md)'s.

API (`from events.pass_rush.predictors.gbm import predict`, or `play.load_predictors()`: it is the pass rush event's default):

- `predict(ctx, lineups, formation, defense, rng) -> PassRush`
- `dropback(ctx, formation, league) -> {"throw": p, "sack": p, "scramble": p}`: the model's probabilities for this dropback.

What the model reads (`inputs.py`):

- the situation and the game so far (`events/situation.py`), and whether the offense is in the shotgun;
- the quarterback (`formation.qb`): how often he has been sacked and has scrambled per dropback, this season before the game (`Player.stats`) and over earlier seasons (`Player.career`), his dropbacks this season, and his years in the league.

The quarterback's inputs are read coarsely (`shared/models/README.md`).

Models: `model_<season>.txt` is the model for that season's games, trained on the seasons from 2011 up to the one before it. A later season uses the latest model; a season before the first model (2021) and a try get the baseline's rates.

Training: `python -m events.pass_rush.predictors.gbm.train` (`2026` for one season, `2021-2026` for a range), or `python -m events.training` for every trained predictor at once. Retrain once a year, when a season is complete.

Scoring: `python -m evaluators.play` (`pass_rush: result`) and `python -m evaluators.game` (`team: sacked`, the first quarterback's rushing yards), against the same runs with `--swap pass_rush=baseline`.
