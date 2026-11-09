nfl_predictor

the goal of this project is to build a system for predicting what happens during an NFL season.

definitions:
event: a discrete unit of something happening. generally has inputs (the relevant state of the world before the event) and outputs (the relevant state of the world changed by the event).
predictor: a mechanism for predicting the outcomes of an event, given its inputs. can be as simplistic as a 50/50 random number generator or as complex as a machine learning (ML) model.
scenario: chains events together, often with domain-specific logic. encodes a real-world sequence of events, connected by logic, where the outputs of previous events are often fed into future events. stores the relevant state of the world as events operate on it. has a set of inputs describing the world before the scenario, and generates relevant outputs.
simulator: simulates many instances of a scenario, aggregating relevant outputs across those simulations.
timeline: a particular instance of a scenario

general approach: simulate many instances of the same scenario, then present a distribution of outcomes. a scenario can be composed of many events, each of which is predicted by an appropriately complex predictor (a game scenario includes a coin toss scenario, composed of a toss event and a decision event; the toss predictor is a trivial 50/50 random generator; the model for predicting what the winning team will do with the toss is significantly more complex). the scenario logically composes event predictors, keeps track of relevant outcomes, then the simulator aggregates those outcomes across 1000’s of simulations. each predictor should be as simple and concise as possible, both in its technical implementation and its scope (for example, the defensive formation predictor should be told the offense's personnel and formation (information the defense has before the snap), rather than implicitly predicting them from team rosters).

complex events should generally be predicted by machine learning (ML) models trained on historical incidents of that event.

scenarios can be composed together; for example an NFL play scenario contains lineup, formation, snap, and outcome events. a game scenario contains many play scenarios. a season scenario contains many game scenarios. parent scenarios should call child scenarios directly rather than trying to recreate or handle them differently.

ML models will probably need to be trained at scale in the cloud (AWS).

scenarios should generally be defined as units that need to be reusable in our system; for example, a play is a very common component of a game, and can be broken down into discrete steps, but there's no point in having a separate "snap scenario" and "play scenario", because the two are always tied together.

in general a simulator’s “simulation” step should happen at the highest level possible; a game simulator should play through a game timeline composed of concrete play timelines, then repeat many times, rather than simulating many play timelines at each step and attempting to average them together or something.

we will need to handle complex logic like changes in NFL rules over the years (the kickoff rule in 2024, for example). all rules live in one rulebook, looked up by season.

the play scenario

the play is the core unit of the system: a game is a sequence of plays, and nearly every stat we care about is produced by a play. a play is a chain of small, discrete events (lineups -> offensive formation -> defensive formation -> pre-snap -> snap -> run/pass/punt/kick/kneel -> more specialized events, like pass -> reception/interception or run -> tackle/fumble), each predicted by its own small predictor, connected by hardcoded NFL rules. the full event chain and rules are in scenarios/play/README.md.

the most important idea is the split of responsibilities. predictors predict what the players do: who comes on the field, how they line up, who gets the ball, where the pass goes, where the ball carrier is brought down, who recovers a fumble. the play scenario decides what that means under the rules: whether it was a touchdown, first down, safety, or touchback, where the ball is spotted, who has possession, how penalties are enforced, what the clock does, and what every player's stat line is. a predictor never predicts something the rules determine.

inputs (provided by the game scenario): teams playing, game location, weather, time of day, stadium turf type, coaching staff, referee team, season (which selects the rulebook), player rosters (including injuries, depth charts, and disqualifications), individual players’ information (position, jersey number, aggregate statistics for the season so far, and draft capital for rookies), kind of play (scrimmage down, try after a touchdown, or kickoff/safety kick), possession, field location, down and distance, game score, quarter, game clock time, whether the game clock is running, play clock time, team timeouts remaining, and all previous plays for the game (or a condensation of relevant information from those plays, or just the outcomes of previous plays). each event's predictor is handed only the slice of these inputs (plus earlier events' outputs) that it plausibly needs.

outputs:
the play record: the ordered list of events and their outcomes (the play's timeline). the single source of truth for everything below.
the type of play, how long the play takes, and the players involved in the play.
relevant outcomes for those players, both offensive and defensive: rushing yards, receiving yards, passes, receptions, first downs, touchdowns, kick yards, return yards, field goal makes and misses, fumbles, interceptions, sacks, tackles, and pressures. team totals are the sum of player outcomes.
penalties: type, players involved, yardage outcome, accepted or declined, and initiating referee if available.
injuries and disqualifications, including how much time they cause the player to miss during the game, up to the rest of the game.
the new situation: possession, field location, down and distance, score, and the kind of the next play (a try after a touchdown, a kickoff after a try or field goal, a safety kick after a safety, otherwise a scrimmage down).
clock: game time used (pre-snap runoff plus the play itself), what the clock does afterward (keeps running, stopped until the snap, or restarts on the ready-for-play signal), and flags the game scenario needs (10-second runoff, untimed down owed).

consistency guarantees: every play the scenario produces is legal and internally consistent.
one source of truth: the play record stores only facts (who had the ball, where each carry started and ended, where each pass was caught, who recovered each loose ball, which fouls were called). field position, possession, score, and every stat line are computed from those facts by deterministic code; no predictor outputs a stat. passing yards equal receiving yards because both come from the same "caught at X, tackled at Y" facts.
rules as a failsafe: predictors should output valid state, but the scenario also masks illegal choices before sampling (an ineligible receiver can't be targeted) and clamps continuous outputs to the field (a carry can't end past the end line). it never silently accepts an illegal state.
invariants: a validation function checks every play in tests (passing yards equal receiving yards, team stats equal the sum of player stats, the change in field position reconciles with the play's yardage, every change of possession is explained by an event, and so on; the full list is in scenarios/play/README.md). simulating millions of plays with cheap random predictors and checking every invariant is the core of the automated testing.

design notes:
predictors sample, they don't average: each predictor returns a sample from its distribution, drawn with a seeded random number generator it's handed, so any play can be reproduced exactly.
one interface per event: any predictor behind an event (base rate, hand-tuned, ML model, or a script in a test) is interchangeable, so predictors can be upgraded one at a time.
cut events along what historical data records: each predictor needs a training set, so events should line up with what play-by-play and participation data actually label (nflverse, for example, records personnel, formation, box count, pass rushers, air yards, yards after the catch, tacklers, and fumble recoveries).

phases

Phase 0 is the play simulator: the play scenario, simulated many times from a fixed set of inputs, with the outcomes aggregated into distributions. its events will be predicted by ML models, but build it rules-first: implement the full event chain, rulebook, play record, stat crediting, and invariants with trivial predictors (historical base rates), prove consistency across millions of simulated plays, then replace the predictors with ML models one event at a time.

Phase 1 is the game simulator. The game scenario broadly takes in all information available at the start of an NFL game, then composes: coin toss scenario -> a sequence of play scenarios (starting with the opening kickoff; each play tells the game what kind of play comes next), potentially with timeouts and coach’s challenge flags between them, keeps track of all game statistics (the sum of each play's stat lines) and the game clock (quarters, the two-minute warning, timeouts, untimed downs), and continues until the game concludes (including overtime if applicable, under the season's overtime rules). The simulator simulates the game scenario 1000’s of times, then presents aggregated statistical distributions across those simulations.

Phase 2 is a season simulator. the season scenario contains all game scenarios across an NFL season and layers between-game events on top of them (practice injuries, trades, depth chart changes, free agent transactions, coaching personnel changes, and IR moves). aggregates statistics across all games. this is further out and therefore less developed.

Phase 3 is a multi-season simulator. the multi-season scenario chains multiple season scenarios together with between-season events (many of the same events from the season scenario, but including drafted players and the NFL schedule). even further out.
