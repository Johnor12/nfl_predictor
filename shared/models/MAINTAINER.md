# MAINTAINER

- __init__.py: the public API (re-exports).
- files.py: `models_of` (the model for a season: the latest one trained for that season or an earlier one), `save_model`, and `_probability` (a model file read once, as a function of one row that remembers its recent answers).
- training.py: `fit` and its default settings (`PARAMS`, `ROUNDS`).
- test_models.py: a fitted model predicts what it was shown; `models_of` picks the model for a season.

Notes:
- Imports nothing from the rest of the project (LightGBM and numpy only), like `shared/priors`.
- A model file is LightGBM's text format: it loads without the training code, and a retrain's diff is at least readable as "it changed".
- Training is deterministic (`seed`, `deterministic`, `force_row_wise`), so the same table gives the same file. A simulated play stays reproducible from its seed: a prediction draws nothing.
- One prediction costs about 60 microseconds for a 150-tree model, once per simulated play. `probability` remembers its last 4,096 rows, because the play evaluator asks about the same real play once per sim. Measured with the snap model on 24 games at 30 sims: the play evaluation takes 4% longer than with the baseline (22% without the memory), the game evaluation 13% (its situations never repeat). `num_threads=1` matters: the evaluators already use every core, and threads inside a prediction made it slower.
- A model isn't updated during a season the way the priors are. What a team has done this season reaches it through its features.
