# game scenario

Simulates a single NFL game: takes everything known at kickoff and returns everything that happens in it.

API (`from scenarios.game import ...`):

- `run_game(ctx, predictors, rng) -> GameResult`: plays one game from a `GameContext` with a `random.Random`. Raises the play scenario's `IllegalChoice` if a predictor returns something the rules don't allow.
- `validate_game(result, plays=True) -> list[str]`: the broken [invariants](RULES.md#invariants) (empty if the game is valid). `plays=False` skips re-checking each play with the play scenario's validator.
- `describe_game(result, plays=False) -> str`: a box score; with `plays=True`, the whole timeline as well.
- `validate_game_context(ctx) -> list[str]`: problems with an input.
- Input: `GameContext(game, players)`: the play scenario's `Game` (teams, venue, weather, coaches, referee, season, playoff) and both teams' active `Player`s.
- Predictors: `GamePredictors(play, toss, timeout)`: the play scenario's `Predictors`, the coin toss scenario's `TossPredictors`, and the timeout event's function. `load_game_predictors("baseline", timeout="other", carry="other")` builds it from each event's implementation of that name.
- `GameResult`: `record` (the timeline), `score`, `winner` (None for a tie), `quarters` (4, or more with overtime), `stats` and `team_stats` (the sum of the plays'), `absences` (players sidelined by injuries or disqualified), and `plays` (the `PlayResult`s alone).
- The record's entries, in order: a `Toss` for each coin toss, a `PlayResult` for each play, and a `Stoppage(kind, quarter, clock, team)` for each timeout, 10-second runoff, two-minute warning, and end of a period.
- Test support (`from scenarios.game.testing import ...`): `synthetic_game`, `chaos_game_predictors` (random legal predictors for fuzzing), `with_events` (swap any event's function).

The hardcoded NFL rules, the invariants, and what isn't built yet are in [RULES.md](RULES.md).

## the event chain

```
coin toss scenario -> opening kickoff -> play -> play -> ... -> final whistle

before every play:
  timeout?  -> the clock stops and the team is charged
  play scenario (run_play), from the situation the last play left

after every play:
  score, stats, history, injuries, disqualifications -> 10-second runoff? -> two-minute warning? -> overtime decided?
  -> time left: the next play
  -> time out:  an untimed down or a try, else the end of the period:
                next quarter | halftime -> second half kickoff | coin toss -> overtime kickoff | game over
```

The game calls the child scenarios directly: `scenarios.coin_toss.run_coin_toss` and `scenarios.play.run_play`. Its one event of its own is `timeout` (`events/timeout/`).

## split of responsibilities

Each play tells the game what comes next: the new situation (possession, spot, down and distance, score, kind of play), how much time it used, and what the clock does afterward. The game owns everything between plays: the periods, the two-minute warning, timeouts, halftime, overtime, who is available, and the history each play is handed. Predictors predict what people do (call a timeout, choose to defer); the game decides what that means under the rules.

## what the game keeps

- **the clock**: seconds left in the period. A play's situation carries the clock as the last play left it; if it is running, the play's pre-snap time comes off before the snap.
- **availability**: a player injured on a play is left out of the next plays' inputs for as long as the injury says, and a disqualified player for the rest of the game.
- **conduct**: the players with one unsportsmanlike conduct foul, handed to each play (`PlayContext.warned`) so it can disqualify one for a second.
- **history**: every play so far, as the play scenario's `PlaySummary`.
- **stats**: each player's and team's totals are the sum of the plays' stat lines, so they are consistent by construction.
