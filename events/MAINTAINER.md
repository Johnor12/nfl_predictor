# MAINTAINER

- __init__.py: package marker.
- <event>/: one package per event (see its README.md and MAINTAINER.md).
- baseline_priors.py: `build` / `save` and the CLI. One pass over a season's real plays, handing each one (a `shared.priors.Sample`) to every `<event>/predictors/baseline/priors.py`'s `observe(tally, sample)`.
- test_predictors.py: every baseline predictor together produces valid plays on synthetic contexts; `load_predictors` rejects unknown events.
- test_baseline_priors.py: a week 1 priors build covers all 17 events with the committed files' keys. Skipped if the nflverse cache is missing.

Adding an event: create `events/<event>/` with the output type in `__init__.py`, a `predictors/baseline/` exporting `predict`, and the READMEs; add a field to `scenarios.play.Predictors` and call it from `scenarios/play/chain.py`.

Adding a predictor implementation: create `events/<event>/predictors/<name>/` exporting `predict`, then load it with `load_predictors("baseline", <event>="<name>")` and compare audits.

Notes:
- An event's `__init__.py` must not import `scenarios.play` (the play scenario imports it). Implementations may.
- In an implementation's `__init__.py`, don't give a module-level name the name of a sibling module: importing `priors.py` replaces a `priors` attribute on the package. That's why the loaders are called `load_priors`.
- A baseline's `priors.py` is only imported by `baseline_priors.py`; `predict` reads the built JSON.
- After changing a `priors.py`, rebuild the priors and rerun `python -m evaluators.audit` to see the effect.
