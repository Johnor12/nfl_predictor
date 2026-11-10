# lineups event

Which 11 players each team puts on the field. The offense goes first, choosing a personnel group (11, 12, 21...) or a special teams unit, and the defense matches it. This is where coaching decisions live: sending the punt unit out on 4th down *is* the decision to punt, sending the kicking unit out after a touchdown *is* the decision not to go for two, and sending the onside unit out *is* the decision to kick onside.

Predictor: `predict(ctx, rng) -> Lineups`

Output (`from events.lineups import ...`):

- `Lineups(offense, defense)`: one `Lineup` per team.
- `Lineup(unit, personnel, players)`: the unit (offense: `offense`, `punt`, `field_goal`, `victory`, `kickoff`, `onside_kickoff`; defense: `defense`, `punt_return`, `field_goal_block`, `kick_return`), a personnel label (`"11"`, `"nickel"`) or None, and 11 player ids.

The play scenario raises `IllegalChoice` unless each side has exactly 11 distinct active players of its own team, and the offense's unit is one of `play.allowed_units(ctx, rules)` (scrimmage: offense, punt, field_goal, victory; try: offense, field_goal; free kick: kickoff, plus onside_kickoff when the season's rules allow declaring one).

Implementations are in [predictors/](predictors/README.md).
