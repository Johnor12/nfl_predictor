# pass result event

Whether the pass is complete, incomplete, or intercepted, and who defended it. A completion becomes the receiver's carry from the catch spot; an interception becomes the defender's return, and possession flips.

Predictor: `predict(ctx, lineups, target, rng) -> PassResult`

Inputs (besides the [common ones](../README.md)):

- `target`: the `Target` (with air yards clamped to the field).

Output (`from events.pass_result import ...`):

- `PassResult(result, defender, seconds, coverage, drop, bad_throw)`: `result` is one of `RESULTS` (`complete`, `incomplete`, `intercepted`); `defender` defended or intercepted the pass; `seconds` is the game time from the throw until the pass is caught, intercepted, or dead. The last three are what a charter adds, and a predictor may leave them out: the defender in `coverage` on the receiver, and whether an incompletion was a `drop` or a `bad_throw`.

The play scenario raises `IllegalChoice` unless the result is one of `RESULTS`; an interception has a defender; the defender and the one in coverage are on the field for the defense; only an incompletion is a drop or a bad throw; `seconds` isn't negative.

Implementations are in [predictors/](predictors/README.md).
