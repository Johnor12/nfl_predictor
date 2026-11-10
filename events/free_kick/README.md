# free kick event

A kickoff or safety kick leaving the tee: who kicks it, how far it travels, and whether it goes out of bounds. The kind of kick is decided by the lineup (the onside unit kicks onside), and the alignment by the season's rules.

Predictor: `predict(ctx, lineups, onside, rng) -> FreeKick`

Inputs (besides the [common ones](../README.md)):

- `onside`: whether the kicking team sent out its onside unit.

Output (`from events.free_kick import ...`):

- `FreeKick(kicker, distance, out_of_bounds, seconds)`: yards from the kick spot to where the ball lands; hang time (which doesn't run the game clock).

The play scenario raises `IllegalChoice` unless the kicker is on the field for the kicking team. The scenario makes an onside kick travel the minimum distance and stops any kick at the end line.

Implementations are in [predictors/](predictors/README.md).
