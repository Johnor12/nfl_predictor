# play scenario

Simulates a single NFL play: takes the state of the game before the play and returns everything that happens on it.

There's no code yet; this is the design.

API (planned): a single entry point that runs one play from the play context (the inputs) with a seeded random number generator, and returns the play result (the outputs).

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
- **invariants**: checked on every play in tests (see [invariants](#invariants)).

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

### pre-snap events

- **lineups**: which 11 players each team puts on the field. The offense goes first, choosing a personnel group (11, 12, 21...) or a special teams unit (punt, field goal/PAT, victory formation). This is where coaching decisions live: sending the punt unit out on 4th down *is* the decision to punt, and sending the kicking unit out after a touchdown *is* the decision not to go for two. The defense picks its personnel second, conditioned on the offense's (in real life, the defense is allowed to match offensive substitutions). Likely implementation: predict the package, then fill it from the depth chart.
- **offensive formation**: how the offense lines up: who is on the line, who is in the backfield, receiver splits, quarterback alignment (under center, shotgun, pistol), motion and shifts. The formation fixes who the eligible receivers are for the rest of the play. It guarantees that formations are legal and that players are lined up in appropriate positions, by construction (for example, the predictor picks from a catalog of legal formation templates); illegal formations only happen as pre-snap fouls.
- **defensive formation**: the defense's front and look (box count, rushers shown, deep safeties, man/zone shell), conditioned on the offensive formation.
- **pre-snap**: how much of the play clock is used before the snap (tempo, which runs off the game clock if it's running) and any pre-snap foul: false start, encroachment, neutral zone infraction, delay of game, illegal formation, illegal shift or motion, too many men on the field. Using more time than the play clock allows is delay of game. Dead-ball fouls end the play here, without a snap. Defensive offside is a live-ball foul: the snap happens, and the play is a "free play" for the offense.
- **snap**: the snap itself (clean, or fumbled -> loose ball) and what the offense does with it: handoff (to whom), pitch, quarterback run, dropback pass, punt, field goal/PAT kick, kneel, spike, or a fake out of a special teams formation. The action must be possible from the formation (a handoff goes to a player in the backfield; a field goal needs a holder and a kicker on the field).

### action events

- **pass rush**: how many rushers came, whether the quarterback was pressured or hit (and by whom), how long until something happened, and the result: throw, sack (by whom, and where), scramble, throwaway, or strip sack.
- **target**: who the pass goes to and where it goes (air yards; left, middle, or right). Only eligible receivers can be targeted.
- **pass result**: complete, incomplete, or intercepted, plus who defended it. A completion becomes the receiver's carry, starting at the catch spot; an interception becomes the defender's return carry, and possession flips.
- **punt kick**: blocked (-> loose ball) or not, and where it lands or goes out of bounds.
- **punt result**: fair catch, return (-> carry), downed by the kicking team, out of bounds, touchback, or muff (-> loose ball).
- **kick attempt** (field goal or PAT): good, no good (and how), or blocked (-> loose ball).
- **kickoff alignment**: mostly dictated by the season's rules (fully fixed since 2024).
- **free kick**: kick type (deep, squib, onside when allowed), and where it lands or goes out of bounds.
- **kick result**: touchback, return (-> carry), out of bounds, fair catch (when allowed), or muff (-> loose ball).

### shared building blocks

- **carry**: one player running with the ball, covering designed runs, scrambles, yards after the catch, and every kind of return. Predicts where the carry ends (signed yards), how it ends (tackled, out of bounds, slide, lateral, fumble), who made the tackle(s), and how long it took. Different contexts (designed run, after the catch, kick return, interception return) probably want different predictors behind the same interface.
- **loose ball**: fumbles, muffs, bad snaps, blocked kicks, and incomplete backward passes. Predicts who recovers it (team and player) and where, or that it goes out of bounds. The rules decide whether the recovering player may advance it (-> carry) and who gets the ball.

### after the ball is dead

- **live-ball fouls**: fouls during the play (holding, pass interference, illegal contact, roughing the passer, illegal block in the back, facemask, intentional grounding, ineligible man downfield, kick catch interference...) and dead-ball fouls after it (unsportsmanlike conduct, unnecessary roughness after the whistle), each with the offending player and the spot. Predicted once, conditioned on the whole play (a 60-yard touchdown run is more likely to come back on a hold than a 2-yard run). A foul has to be possible on the play: no pass interference on a run, no roughing the passer without a passer, no intentional grounding without a throwaway or pressured throw.
- **accept/decline**: the non-offending team's choice. Start with a hardcoded rule (take whichever result is better in yards, downs, possession, and clock); it can become a predictor later if coaches turn out to deviate from it meaningfully.
- **enforcement**: fully hardcoded (see below).
- **injuries**: which players were injured and for how long, weighted toward the players involved in the play.
- **stat crediting** and **new situation**: deterministic code, no predictors (see invariants below).

## hardcoded NFL rules

The play scenario encodes the rulebook. This is a sketch of what it must cover, not the full list. The values below are from memory and should be checked against the official NFL rulebook for each season when implemented.

### downs and distance
- 4 downs to gain 10 yards. Reaching the line to gain is a first down; when the line to gain would be in the end zone, it's goal to go.
- Failing on 4th down is a turnover on downs at the dead-ball spot.
- Every change of possession gives the new offense 1st and 10 (or goal to go).

### scoring
- Touchdown 6, extra point kick 1, two-point conversion 2, field goal 3, safety 2 (for the defense), defensive return during a try 2 (2015+).
- After a touchdown, the scoring team gets a try (the game scenario may skip a try that can't affect the result). After a try or field goal, the scoring team kicks off. After a safety, the team scored upon free kicks from its own 20, by punt or place kick.
- A try is a single down, from the 2 (two-point attempt) or the 15 (kick; 2015+, the 2 before). It ends when the down ends.

### end zones and boundaries
- Possession of the ball on or across the opponent's goal line is a touchdown.
- A ball that dies in a team's own end zone is a safety if that team put it there (impetus), and a touchback if the opponent did.
- Touchbacks after punts, interceptions, and fumbles are spotted at the 20; kickoff touchbacks follow the season's kickoff rules.
- A pass caught beyond the end line or out of bounds is incomplete.

### passing
- One forward pass per play, from behind the line of scrimmage. A second forward pass, or one thrown from beyond the line, is an illegal forward pass (5 yards and loss of down).
- Only eligible receivers may catch a forward pass first. Ineligible linemen may not be more than 1 yard downfield when a pass crosses the line.
- Backward passes (laterals and pitches) may be thrown by anyone, from anywhere, any number of times. An incomplete backward pass is a loose ball.
- Intentional grounding: loss of down plus 10 yards or the spot of the foul, whichever is worse; a safety if the passer is in his own end zone. It isn't grounding if the passer is outside the tackle box and the pass reaches the line of scrimmage.
- Spiking the ball to stop the clock is an incomplete pass, not grounding.

### fumbles and loose balls
- On 4th down, on a try, or after the two-minute warning of either half, an offensive fumble can only be advanced by the player who fumbled. If a teammate recovers it, the ball is spotted at the spot of the fumble (or of the recovery, if that's behind it).
- A fumble out of bounds belongs to the team that last had it, at the out-of-bounds spot, unless it went forward, in which case it returns to the spot of the fumble. A fumble out of bounds through the opponent's end zone is a touchback for the opponent.

### scrimmage kicks (punts and field goals)
- Once a kick crosses the line of scrimmage and is touched first by the receiving team, it's a live ball for both teams; the kicking team may recover it but not advance it.
- A fair catch kills the ball at the spot of the catch. Kick catch interference is 15 yards from the spot of the foul.
- A punt into the end zone is a touchback.
- A missed field goal gives the defense the ball at the spot of the kick, or at its own 20 if the spot of the kick was inside the 20. Blocked field goals, and ones that fall short in the field of play, are live.
- Field goal distance = yards from the line of scrimmage to the goal line + 17 (10 yards of end zone and a 7-yard hold).

### free kicks (rule-versioned)
- Kickoffs are from the kicking team's 35 (2011+; the 30 before). Safety kicks are from the 20.
- Kickoff touchbacks are spotted at the 20 (before 2016), the 25 (2016–2023), the 30 (2024), and the 35 (2025+). In 2023 only, a fair catch inside the 25 was spotted at the 25.
- Dynamic kickoff (2024+): fixed alignment (kicking team at the receiving team's 40, at least 9 receiving players in a setup zone between their own 30 and 35, at most two returners in the landing zone); a kick that lands in the landing zone (receiving team's 20 to the goal line) is live and must be played; a kick short of the landing zone or out of bounds gives the receiving team the ball at its 40; a kick that lands in the landing zone and rolls into the end zone is a touchback at the 20; no fair catches.
- Onside kicks must be declared from 2024: in 2024 only when trailing in the 4th quarter, from 2025 any time the kicking team is trailing.
- The kicking team may recover a free kick (but not advance it) once it has gone 10 yards or been touched by the receiving team.

### personnel and formation
- Exactly 11 players per side at the snap (12 or more is too many men on the field).
- Offense: at least 7 players on the line of scrimmage, no more than 4 in the backfield, at least 5 players numbered 50–79 on the line. Eligible receivers are the two players on the ends of the line and the backs, plus anyone who reported as eligible. At most one player in motion at the snap, and not moving toward the line; after a shift, everyone is set for a full second.
- Defense: no one in the neutral zone at the snap.
- A player injured on a play must sit out at least the next play.
- Two unsportsmanlike conduct fouls (2016+) or a flagrant foul disqualify a player for the rest of the game.

### penalty enforcement
- Each foul has a yardage (5, 10, 15, or a spot foul), an enforcement spot (previous spot, spot of the foul, end of the run, or succeeding spot), and possibly an automatic first down (defensive holding, illegal contact, defensive pass interference, roughing the passer, defensive personal fouls) or a loss of down (intentional grounding, illegal forward pass).
- Running plays use the "3-and-1" principle to choose between the spot of the foul and the end of the run.
- Half the distance to the goal when the yardage would exceed it.
- Defensive pass interference is a spot foul (1st down at the spot, or at the 1 if it happened in the end zone); offensive pass interference is 10 yards from the previous spot.
- Offsetting fouls replay the down. An offensive foul in its own end zone is a safety.
- Accepted fouls during the play usually wipe it out ("no play", no player stats); fouls after the play are enforced from where it ended, and the play's stats stand.
- Fouls on a scoring play may be enforced on the try or the ensuing kickoff.
- A half can't end on a play with an accepted defensive foul (untimed down). In the last minute of a half, an offensive foul that stops the clock carries a 10-second runoff option, avoidable with a timeout.

### clock (play level)
- The play reports how much game time it used and what the clock does afterward. Quarter ends, the two-minute warning, and timeouts belong to the game scenario.
- The clock stops on incomplete passes, scores, changes of possession, penalties, spikes, and runners going out of bounds. After an out-of-bounds play it restarts on the ready-for-play signal, except in the last 2 minutes of the first half and the last 5 minutes of the second half, when it waits for the snap.
- An injury stoppage inside the last 2 minutes of a half costs a timeout, or a 10-second runoff if the team has none.
- 40-second play clock after most plays; 25 seconds after administrative stoppages (timeouts, penalties, injuries, changes of possession...).

### rule versioning
- All rules live in one rulebook, looked up by season. The play scenario never hardcodes a season-dependent value outside it.
- This matters for training as much as for simulation: historical plays have to be interpreted under the rules of their own season, and predictors for events whose rules changed (kickoffs, after 2024) need the rule era as an input, or the data from before the change dropped.
- Examples: kickoff spot (2011), PAT moved to the 15 and defensive returns on tries (2015), kickoff touchback at the 25 and ejection after two unsportsmanlike fouls (2016), kickoff fair catch (2023), dynamic kickoff (2024), touchback at the 35 and onside declaration (2025). Overtime rules are versioned the same way, but belong to the game scenario.

## invariants

Checked by one validation function after every simulated play in tests:

- For each completion, the passer's passing yards equal the receiver's receiving yards (line of scrimmage to where the receiver's carry ended). Completions equal receptions; interceptions thrown equal interceptions made.
- Sack yards come off team passing yards, not the passer's; sacks are not rushes; scrambles and kneels are rushes; spikes are incomplete passes.
- Rushing and receiving yards are credited to the spot of a fumble; yards after a recovery are fumble return yards.
- Two-point tries add no passing, rushing, or receiving yards.
- Team stats equal the sum of player stats, plus team-only items (sack yards, penalty yards).
- The change in field position reconciles with the play's offensive, return, and penalty yardage, across any changes of possession.
- The score changes only through a scoring event, by exactly that event's value.
- Every player with a stat on the play was on the field for it; ball carriers belong to the team in possession at that moment, tacklers to the other team.
- Every change of possession is explained by an event (interception, lost fumble, punt, kick, turnover on downs, score, safety).
- A "no play" produces no player stats besides the foul itself.
- Lost fumbles equal opponent recoveries; forced fumbles never exceed fumbles.
- 11 players per side (unless too many men was called), down between 1 and 4, distance positive and never past the goal line, ball inside the field, elapsed time never negative.

Simulating millions of plays with cheap random predictors and checking every invariant is the core of the automated testing. Rule-specific behavior (a 4th-down fumble recovered by a teammate, a dynamic kickoff landing short of the landing zone) gets hand-built tests that script the predictors' outputs.

## implementation notes

- Suggested module boundaries: the rulebook (season constants and pure rule functions), the play record and stat crediting (pure, no predictors), the events (an interface plus predictors for each), and the play scenario (the chain that connects them). None of them need to know about games or seasons.
- Left to the implementer: whether some fouls are better predicted inside the event they belong to (pass interference in pass result, for example); whether lineups pick packages or specific players; how much of the passer's position to model (it separates forward passes from laterals, and decides grounding); and many more micro-decisions like these.
