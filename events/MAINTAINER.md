# MAINTAINER

- __init__.py: package marker.
- <event>/: one package per event (see its README.md and MAINTAINER.md).
- baseline_priors.py: `build` / `save` and the CLI. One pass over a season's real plays, handing each one (a `shared.priors.Sample`) to every `<event>/predictors/baseline/priors.py`'s `observe(tally, sample)`.
- test_predictors.py: every baseline predictor together produces valid plays on synthetic contexts; `load_predictors` rejects unknown events; the baseline timeout predictor only names a team that has a timeout.
- test_baseline_priors.py: a week 1 priors build covers every event that has a `priors.py` (18) with the committed files' keys. Skipped if the nflverse cache is missing.

Adding an event: create `events/<event>/` with the output type in `__init__.py`, a `predictors/baseline/` exporting `predict`, and the READMEs; add a field to `scenarios.play.Predictors` and call it from `scenarios/play/chain.py`; add its cases to `evaluators/play/cases.py` so it gets scored.

Adding an event to another scenario works the same way: a field in that scenario's bundle (`scenarios.coin_toss.TossPredictors`, `scenarios.game.GamePredictors`) and a call in its chain. A baseline without data (`coin_toss`, `toss_choice`) has no `priors.py`.

Adding a predictor implementation: create `events/<event>/predictors/<name>/` exporting `predict`, then load it with `load_predictors("baseline", <event>="<name>")`. Score it with `python -m evaluators.play --swap <event>=<name>` and compare the event's rows with the baseline's; the audit shows the effect on overall rates.

Notes:
- An event's `__init__.py` must not import `scenarios.play` (the play scenario imports it). Implementations may.
- In an implementation's `__init__.py`, don't give a module-level name the name of a sibling module: importing `priors.py` replaces a `priors` attribute on the package. That's why the loaders are called `load_priors`.
- A baseline's `priors.py` is only imported by `baseline_priors.py`; `predict` reads the built JSON.
- `python -m events.baseline_priors` rebuilds every event's file from the data as it is now. `timeout`'s was added later than the rest, from a few more games.
- After changing a `priors.py`, rebuild the priors and rerun `python -m evaluators.play` and `python -m evaluators.audit` to see the effect.
