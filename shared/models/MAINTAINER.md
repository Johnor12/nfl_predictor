# MAINTAINER

- __init__.py: the public API (re-exports).
- files.py: `models_of` (the model for a season: the latest one trained for that season or an earlier one), `save_model`, `draw`, `choose`, and `_probability` (a model file read once, as a function of one row, or of several, that remembers its recent answers).
- training.py: `fit`, `fit_number`, and their default settings (`PARAMS`, `ROUNDS`, `COARSE`).
- test_models.py: a fitted model predicts what it was shown; `models_of` picks the model for a season; a model of classes; a model of a number and drawing from it; a number's limit; a coarse feature.

Notes:
- Imports nothing from the rest of the project (LightGBM and numpy only), like `shared/priors`.
- A model file is LightGBM's text format: it loads without the training code, and a retrain's diff is at least readable as "it changed".
- Training is deterministic (`seed`, `deterministic`, `force_row_wise`), so the same table gives the same file. A simulated play stays reproducible from its seed: a prediction draws nothing.
- One prediction costs about 60 microseconds for a 150-tree model, once per simulated play. `probability` remembers its last 4,096 rows, because the play evaluator asks about the same real play once per sim. Measured with the snap model on 24 games at 30 sims: the play evaluation takes 4% longer than with the baseline (22% without the memory), the game evaluation 13% (its situations never repeat). `num_threads=1` matters: the evaluators already use every core, and threads inside a prediction made it slower.
- A model isn't updated during a season the way the priors are. What a team has done this season reaches it through its features.
- A number's model is one yes/no model over (the play's features, a cut), not a model per cut or a class per yard: the file stays the size of a yes/no model's (0.5 MB), any number of cuts costs one prediction of that many rows (about 0.1 ms for 35), and the cuts share what they learn. The cut may only lower the answer (`monotone_constraints`), and `_probability` makes the answers fall where rounding doesn't.
- Why `limit`: without it the yards models put too little on the goal line. Whether a run from the 3 reaches a cut depends on the cut being 3 or 4, and to a tree that is two features (the cut, the yards to go) whose difference matters; it can only cut each one at a few values, so the touchdown, which sits exactly where they are equal, got smeared over its neighbours. Simulated games had the right yards and 80% of the real rushing touchdowns. With the difference as a feature of its own (`ROOM`) it is one split. The same goes for anything that piles up at a boundary: give the model the distance to it.
- A drawn number between two wide cuts is filled in by the predictor from a histogram (`shared.priors.hist`). If the limit lies between them, everything past it belongs there too: the carry predictor draws from the histogram's whole tail and lets the play scenario stop the carry at the goal line.
- A choice among players (who is thrown to) is a yes/no model asked once per candidate, not a model with a class per player: the candidates change from play to play. One call scores them all (`several=True`: about the cost of one row), and `choose` draws in proportion to the answers, so they needn't add up to 1. `events/target/predictors/gbm_receiver/` is the pattern; its training table has a row per candidate (`events.training`: an example may return several rows).
- `coarse` exists because of what was found adding inputs about who is playing (`events/MAINTAINER.md`). 8 steps was the only number tried besides exact.

