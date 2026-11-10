# pass result event

Whether the pass is complete, incomplete, or intercepted, and who defended it. A completion becomes the receiver's carry from the catch spot; an interception becomes the defender's return, and possession flips.

Predictor: `predict(ctx, lineups, target, rng) -> PassResult`

Inputs (besides the [common ones](../README.md)):

- `target`: the `Target` (with air yards clamped to the field).

Output (`from events.pass_result import ...`):

- `PassResult(result, defender)`: `result` is one of `RESULTS` (`complete`, `incomplete`, `intercepted`); `defender` defended or intercepted the pass.

The play scenario raises `IllegalChoice` unless the result is one of `RESULTS`; an interception has a defender; the defender is on the field for the defense.

Implementations are in [predictors/](predictors/README.md).
