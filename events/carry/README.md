# carry event

One player running with the ball: designed runs, scrambles, kneels, yards after the catch, and every kind of return. Predicts where the carry ends, how it ends, who made the tackle, and how long it took. A shared building block, reachable from anywhere the ball is live.

Predictor: `predict(ctx, lineups, kind, carrier, yard_line, rng) -> CarryEnd`

Inputs (besides the [common ones](../README.md)):

- `kind`: `run`, `scramble`, `kneel`, `catch`, `interception`, `punt_return`, `kick_return`, or `recovery`.
- `carrier`: the ball carrier's id.
- `yard_line`: where the carry starts, as the carrier's own yard line (yards from his team's goal line; the one input that isn't in play coordinates).

Output (`from events.carry import ...`):

- `CarryEnd(yards, how, tacklers, forced_by, seconds)`: `yards` is signed, in the carrier's direction of travel; `how` is one of `ENDS` (`tackled`, `out_of_bounds`, `fumble`, `down` for a slide, kneel, or no contact).

The play scenario raises `IllegalChoice` unless `how` is one of `ENDS`; `seconds` isn't negative; tacklers and `forced_by` are on the field for the other team; `forced_by` needs a fumble. The scenario clamps the end of the carry to the field and applies the goal lines (touchdown, safety, touchback, momentum).

Implementations are in [predictors/](predictors/README.md).
