nfl_predictor

the goal of this project is to build a system for predicting what happens during an NFL season.

definitions:
event: a discrete unit of something happening. generally has inputs (the relevant state of the world before the event) and outputs (the relevant state of the world changed by the event).
predictor: a mechanism for predicting the outcomes of an event, given its inputs. can be as simplistic as a 50/50 random number generator or as complex as a machine learning (ML) model.
scenario: chains events together, often with domain-specific logic. encodes a real-world sequence of events, connected by logic, where the outputs of previous events are often fed into future events. stores the relevant state of the world as events operate on it. has a set of inputs describing the world before the scenario, and generates relevant outputs.
simulator: simulates many instances of a scenario, aggregating relevant outputs across those simulations.
timeline: a particular instance of a scenario
evaluator: scores a simulator's output distributions against external benchmarks (betting lines, player projections), so predictor changes can be measured.

general approach: simulate many instances of the same scenario, then present a distribution of outcomes. a scenario can be composed of many events, each of which is predicted by an appropriately complex predictor (a game scenario includes a coin toss scenario, composed of a toss event and a decision event; the toss predictor is a trivial 50/50 random generator; the model for predicting what the winning team will do with the toss is significantly more complex). the scenario logically composes event predictors, keeps track of relevant outcomes, then the simulator aggregates those outcomes across 1000’s of simulations. each predictor should be as simple and concise as possible, both in its technical implementation and its scope (for example, the defensive formation predictor should be told the offense's personnel and formation (information the defense has before the snap), rather than implicitly predicting them from team rosters).

I have a fairly strong conviction that coaching staff, referees, and betting lines will be significant predictors.

I am absolutely willing to include pre-game betting lines as inputs to our predictors. I realize this means that comparing to betting lines becomes more complex, but I believe betting lines abolsutely impact the outcomes of games (corruption). at the very least we should test including them. a theory is that referees are unduly influenced by betting lines, which would imply that fouls are the main way they express themselves in games. I'm not particularly interested in implicitly reusing the betting lines predictive values (that's the whole point of this project), but I think they could be useful as a primary indicator via the path I described above. - we attempted this generally and saw no improvement. the next step would be to split by referee crew and foul type. this is not high priority.

complex events should generally be predicted by machine learning (ML) models trained on historical incidents of that event.

scenarios can be composed together; for example an NFL play scenario contains lineup, formation, snap, and outcome events. a game scenario contains many play scenarios. a season scenario contains many game scenarios. parent scenarios should call child scenarios directly rather than trying to recreate or handle them differently.

ML models will probably need to be trained at scale in the cloud (AWS).

scenarios should generally be defined as units that need to be reusable in our system; for example, a play is a very common component of a game, and can be broken down into discrete steps, but there's no point in having a separate "snap scenario" and "play scenario", because the two are always tied together.

in general a simulator’s “simulation” step should happen at the highest level possible; a game simulator should play through a game timeline composed of concrete play timelines, then repeat many times, rather than simulating many play timelines at each step and attempting to average them together or something.

we will need to handle complex logic like changes in NFL rules over the years (the kickoff rule in 2024, for example). all rules live in one rulebook, looked up by season.

the play scenario

the play is the core unit of the system: a game is a sequence of plays, and nearly every stat we care about is produced by a play. a play is a chain of small, discrete events (lineups -> formations -> snap -> run/pass/kick -> carries, catches, and loose balls -> fouls), each predicted by its own small predictor, connected by hardcoded NFL rules.

the most important idea is the split of responsibilities: predictors predict what the players do (who comes on the field, where the pass goes, where the ball carrier is brought down); the play scenario decides what that means under the rules (touchdowns, first downs, possession, penalty enforcement, the clock, and every player's stat line). stats are computed from the facts in the play record by deterministic code, never predicted, so every play is legal and internally consistent; a validation function checks this on every simulated play in tests.

inputs, outputs, the full event chain, rules, and invariants are in scenarios/play/README.md.

design notes:
predictors sample, they don't average: each predictor returns a sample from its distribution, drawn with a seeded random number generator it's handed, so any play can be reproduced exactly.
one interface per event: any predictor behind an event (base rate, hand-tuned, ML model, or a script in a test) is interchangeable, so predictors can be upgraded one at a time.
cut events along what historical data records: each predictor needs a training set, so events should line up with what play-by-play and participation data actually label (nflverse, for example, records personnel, formation, box count, pass rushers, air yards, yards after the catch, tacklers, and fumble recoveries).

Tell me if we're missing data which you think I could provide rather than working around it.

our general strategy for evaluating accuracy should be: run our simulator, which provides a distribution of outcomes. check the real outcome against that distribution using fair CRPS for numberic stats, multiclass (fair) Brier for categorical outputs, and, for binary outcomes, Brier score (main metric) + smoothed log loss for moneyline comparisons. fair crps on a binary outcome is equivalent to fair brier, so a single implementation should work for both. evaluation should happen at every level of the system; individual event predictors, and every scenario, and should apply to every system output. in addition to comparing to what actually happened, we should evaluate our outputs against other predictors: moneylines (encodes win probability +vig), spreads (median-like), and prop lines (P(X > line)), be computing the same values from our distributions. those predictors can help as establish a baseline accuracy goal.

for CRPS in specific, scoring the same predictor twice with different seeds gives sim noise, which can be used to estimate the number of simulations we need to run to extract real changes when comparing different predictor versions (ceiling of around 10,000)

for diagnostics, we shoud output PIT histograms for numerical values and reliability diagrams for probabilities.

phases

Phase 0 is the game simulator, built rules-first. The game scenario broadly takes in all information available at the start of an NFL game, then composes: coin toss scenario -> a sequence of play scenarios (starting with the opening kickoff; each play tells the game what kind of play comes next), potentially with timeouts and coach’s challenge flags between them, keeps track of all game statistics (the sum of each play's stat lines) and the game clock (quarters, the two-minute warning, timeouts, untimed downs), and continues until the game concludes (including overtime if applicable, under the season's overtime rules). The simulator simulates the game scenario 1000’s of times, then presents aggregated statistical distributions across those simulations. the football logic (event chains, rulebook, play record, stat crediting, invariants) should be comprehensive from the start, since it's limited only by knowledge and effort, not data or cost. the predictors behind the events start out extremely simple: statistical priors from previous seasons.

Phase 1 is the evaluator, then iterative predictor improvement. the evaluator compares the game simulator's distributions against external benchmarks: full-game priors (betting lines: spread, total, moneyline) and individual player stats (fantasy football projections or player prop lines). with that in place, swap out event predictors one at a time (priors -> hand-tuned -> ML models) and measure the effect of each change.

Phase 2 is a season simulator. the season scenario contains all game scenarios across an NFL season and layers between-game events on top of them (practice injuries, trades, depth chart changes, free agent transactions, coaching personnel changes, and IR moves). aggregates statistics across all games. this is further out and therefore less developed.

Phase 3 is a multi-season simulator. the multi-season scenario chains multiple season scenarios together with between-season events (many of the same events from the season scenario, but including drafted players and the NFL schedule). even further out.

architecture: the project should be structured to match our terminology and model; a /events folder with subfolders for each individual event that we are modeling (the inputs and outputs for the event). within each event folder, we should have a folder for predictors. each subfolder in the predictors folder should be an implementation of a predictor for that event, allowing us to store multiple predictors and swap between them easily. a separate folder within the scenario folder for each scenario we model; a game, a play, etc. individual events/predictors can be reused across different scenarios. a separate top level folder for our simulators, which orchestrate our scenarios. a separate top level folder for evaluators, which score the output of simulators. a top level folder /shared, for shared business logic (rulebooks)

finished (11/14):
Game scenario, simulator, and evaluator.
not built: coach's challenges, multiple timeouts per dead ball, injury stoppage time, emergency replacements, postseason third-overtime kickoff, fair-catch kick, fake kicks

current goals:

1. follow up on our game scenario implementation, building out any remaining edge cases.

notes:
Do you want a priced source for player props? Without prices a prop can only be treated as a coin flip at the line, and priced history most likely means a paid odds API.

a trained box predictor is the natural next ML model

it feels like team strength is a proxy/approximation for the sum of all players' strengths + coaching staff strength. investigate a version of our system which tracks no single team strength and uses player + coach identities as the "skill" input. similarly, including "team 4-th down go rate" for example seems like a mistake to me; the "team" as an entity probably has only mild preferences ("team culture"). the coaching staff and available players seem much more relevant. that would also allow us to handle coaching staff changes cleanly without erroneous carry-over from their respective teams.

I suspect the wider coaching staff has a decent impact on performance; at the least offensive and defensive coordinator seem relevant. for playcalling in particular, knowing who is calling plays seems like extremely relevant input to what play is called (not always the OC/DC). investigate adding more coaching staff depth to the model, and more intelligent play calling information.

we've tested weather (improvements for punts, no where else. might be limited by not using it system-wide). surface, neutral site, draft pick, defensive form; no improvements. some intuitions which I think are worth testing: annecdotally, weather (high wind, rain) is generally thought to adversely affect passing, kicking, and fumble rates (higher). I saw a study once that surface (turf) can increase injury rates; if we ever get to an ML driven injury model, that could be worth testing. draft pick _should_ have some impact on usage, although it may not be homogenous across positions (the normal thought is: freshly drafted high-capital RBs are generally used within their first couple of years, WRs more like 2-3 years, QBs sometimes develop for even longer. I'm not sure the details for other positions, but my point is that the effect might differ between them).