# defensive formation event

The defense's front and look, chosen after seeing the offensive formation.

Predictor: `predict(ctx, lineups, formation, rng) -> DefensiveFormation`

Inputs (besides the [common ones](../README.md)):

- `formation`: the offense's `Formation`.

Output (`from events.defensive_formation import ...`):

- `DefensiveFormation(box, deep_safeties)`: defenders in the box and deep safeties.

The play scenario doesn't restrict the output.

Implementations are in [predictors/](predictors/README.md).
