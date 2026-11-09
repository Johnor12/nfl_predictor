# predictors

Implementations of the play scenario's event predictors (the interface is `scenarios/play/events.py`).

- `baseline/`: simple priors from a season of real plays, plus hand-set rules. Start here.

A future predictor (hand-tuned or ML) implements one event's function and replaces it in a `Predictors` bundle:
`dataclasses.replace(baseline_predictors(), carry=my_carry)`.
