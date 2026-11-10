# play scenario

Simulates a single NFL play: takes the state of the game before the play and returns everything that happens on it.

API (`from scenarios.play import ...`):

- `run_play(ctx, predictors, rng) -> PlayResult`: runs one play from a `PlayContext` with a `random.Random`. Raises `IllegalChoice` if a predictor returns something the rules don't allow.
- `validate_play(result) -> list[str]`: the broken [invariants](RULES.md#invariants) (empty if the play is valid).
- `validate_context(ctx) -> list[str]`: problems with an input.
- `describe_play(result)` / `describe_situation(situation)`: human-readable narration.
- Inputs: `PlayContext(game, situation, players, history)` with `Game`, `Situation`, `Player`, `PlaySummary`. Spots are yard lines from the offense's own goal line (the kicking team's on free kicks); a try's `x` is the two-point spot, and a kicked try is snapped 13 yards farther back.
- Predictors: `Predictors` bundles one function per event. `load_predictors("baseline")` builds it from each event's implementation of that name (`events/<event>/predictors/<name>/`), and `load_predictors("baseline", carry="other")` swaps one event's. Each event's signature and output type are in `events/<event>/README.md`.
- `PlayResult`: the record (facts), live and final dead-ball results, accepted/declined fouls, scores, `next` situation, player and team stats, elapsed time, what the clock does next, untimed-down and 10-second-runoff flags, injuries.
- The record's facts: `Sack`, `Pass`, `Carry`, `LooseBall`, `Kick`, plus the event outputs kept as they were predicted; `facts(record, type)` reads them.
- Helpers for predictors: `rel` / `to_x` (team yard lines), `eligible_receivers`, `field_goal_distance`, `allowed_units`, `FREE_KICKS`, `CATALOG` (the fouls).
- Test support (`from scenarios.play.testing import ...`): `synthetic_context`, `synthetic_roster`, `chaos_predictors` (random legal predictors for fuzzing), `scripted` (fixed outputs for rule tests).

The hardcoded NFL rules, the invariants, and what isn't built yet are in [RULES.md](RULES.md).

## inputs

Provided by the game scenario:

- **game**: teams playing, game location, weather, time of day, stadium turf type, coaching staffs, referee crew, and season (which selects the rulebook).
- **players**: rosters (including injuries, depth charts, and disqualifications) and each player's information (position, jersey number, aggregate statistics for the season so far, and draft capital for rookies).
- **situation**: kind of play (scrimmage down, try after a touchdown, or kickoff/safety kick), possession, field location, down and distance, score, quarter, game clock time, whether the game clock is running, play clock time, and team timeouts remaining.
- **history**: all previous plays in the game (or a condensation of the relevant information, or just their outcomes).

Each event's predictor is handed only the slice of these inputs (plus earlier events' outputs) that it plausibly needs.

## outputs

- **the play record**: the ordered list of events and their outcomes (the play's timeline). The single source of truth for everything below.
- the type of play, how long it took, and the players involved.
- player outcomes, offensive and defensive: rushing yards, receiving yards, passes, receptions, first downs, touchdowns, kick yards, return yards, field goal makes and misses, fumbles, interceptions, sacks, tackles, and pressures. Team totals are the sum of player outcomes.
- penalties: type, players involved, yardage outcome, accepted or declined, and initiating referee if available.
- injuries and disqualifications, including how much of the game they cost the player, up to the rest of it.
- the new situation: possession, field location, down and distance, score, and the kind of the next play (a try after a touchdown, a kickoff after a try or field goal, a safety kick after a safety, otherwise a scrimmage down).
- clock: game time used (pre-snap runoff plus the play itself), what the clock does afterward (keeps running, stopped until the snap, or restarts on the ready-for-play signal), and flags the game scenario needs (10-second runoff, untimed down owed).

## split of responsibilities

Predictors predict what the players do: who comes on the field, how they line up, who gets the ball, where the pass goes, where the ball carrier is brought down, who recovers a fumble. The play scenario decides what that means under the rules: whether it was a touchdown, first down, safety, or touchback, where the ball is spotted, who has possession, how penalties are enforced, what the clock does, and what every player's stat line is. A predictor never predicts something the rules determine.

## consistency guarantees

Every play the scenario produces is legal and internally consistent.

- **one source of truth**: the play record stores only facts (who had the ball, where each carry started and ended, where each pass was caught, who recovered each loose ball, which fouls were called). Field position, possession, score, and every stat line are computed from those facts by deterministic code; no predictor outputs a stat. Passing yards equal receiving yards because both come from the same "caught at X, tackled at Y" facts.
- **rules as a failsafe**: predictors should output valid state, but the scenario also masks illegal choices before sampling (an ineligible receiver can't be targeted) and clamps continuous outputs to the field (a carry can't end past the end line). It never silently accepts an illegal state.
- **invariants**: checked on every play in tests (see [RULES.md](RULES.md#invariants)).

## the event chain

```
scrimmage down or try:
  lineups -> offensive formation -> defensive formation -> pre-snap -> snap -> action

  action:
    run             -> carry
    pitch           -> carry (or loose ball if incomplete)
    pass            -> pass rush -> sack
                                 -> scramble -> carry
                                 -> throwaway
                                 -> strip sack -> loose ball
                                 -> throw -> target -> pass result -> complete    -> carry (after the catch)
                                                                   -> incomplete
                                                                   -> intercepted -> carry (return)
    punt            -> punt kick -> punt result -> carry (return)
    field goal/PAT  -> kick attempt
    kneel, spike    -> (done)

free kick (kickoff or safety kick):
  lineups -> kickoff alignment -> free kick -> kick result -> carry (return)

shared building blocks, reachable from anywhere the ball is live:
  carry      -> tackled | out of bounds | into an end zone | lateral -> carry | fumble -> loose ball
  loose ball -> recovered (-> carry, if the recovering player may advance) | out of bounds

after the ball is dead:
  live-ball fouls -> accept/decline -> enforcement -> injuries -> stat crediting -> new situation
```

Bad snaps, strip sacks, blocked kicks, muffed punts, and incomplete backward passes all become a loose ball, and every run, scramble, catch, and return becomes a carry. These shared building blocks keep the number of distinct events small.

Each event in the chain is a package under `events/`, with its inputs, output, and predictors: `lineups`, `offensive_formation`, `defensive_formation`, `pre_snap`, `snap`, `pass_rush`, `target`, `pass_result`, `punt_kick`, `punt_result`, `kick_attempt`, `free_kick`, `kick_result`, the shared building blocks `carry` and `loose_ball`, and `fouls` and `injuries` after the ball is dead. The kickoff alignment is fixed by the season's rules, so it isn't predicted.

The rest of what happens after the ball is dead is this scenario's own code, with no predictors:

- **accept/decline**: the non-offending team's choice. A hardcoded rule (take whichever result is better in yards, downs, possession, and clock); it can become an event later if coaches turn out to deviate from it meaningfully.
- **enforcement**: fully hardcoded (see [RULES.md](RULES.md#penalty-enforcement)).
- **stat crediting** and the **new situation**: computed from the record (see [RULES.md](RULES.md#invariants)).
