# game scenario rules

The NFL rules the game scenario hardcodes, the invariants every game satisfies, and what isn't built yet. The API and the event chain are in [README.md](README.md). Values are from memory and should be checked against the official rulebook.

## hardcoded NFL rules

### periods
- Four 15-minute quarters. The first and third end without changing anything but the clock: play resumes from the same situation.
- The first half ends when the second quarter does, whatever the situation. The second half starts with a kickoff by the team the coin toss gave it to, with three timeouts each again.
- A period can't end on a play with an accepted defensive foul (an untimed down follows), and a touchdown as time expires is still followed by its try. The try is skipped when the game is ending and it can't change who wins.
- A period that ends on a fair catch can be extended by a fair-catch kick: the team that made the catch decides (its lineups predictor sends the kick out or doesn't), and if it doesn't, the period ends with no down played.
- Otherwise the period ends when the clock reaches zero. If a running clock runs out before the ball is snapped, the play never happens.

### the clock between plays
- After a play the clock keeps running, restarts on the ready-for-play signal, or waits for the snap, as the play scenario reports. The first two both run before the next snap.
- Two-minute warning in the second and fourth quarters, and in overtime (postseason: in the even overtime periods). The clock stops at 2:00, or after the play that crosses it. If a running clock reaches 2:00 before the snap, the play is snapped at 2:00 with the clock stopped.
- 10-second runoff: when a play reports the option, the defense takes it if it's the first half or it isn't behind. The offense spends a timeout instead if it has one. After a runoff the clock starts on the ready-for-play signal; declined or bought off with a timeout, it waits for the snap.
- Play clock: 25 seconds after a timeout, the two-minute warning, and the start of a period.

### timeouts
- Three per team per half. Calling one stops the clock until the snap. A running clock runs until the timeout is called, and a team that calls one gets it in before the two-minute warning or the end of the period.
- Each team may call one in a dead ball, never two in a row: after a timeout only the other team can call another before the snap.

### coach's challenges
- A team may challenge the play just run if it has a timeout left and a challenge left: two a game, and a third once it has won one of them (both of them, before 2024).
- Not after the two-minute warning of a half or in overtime, where only the replay official starts a review.
- A challenge that is lost costs a timeout; one that is won costs nothing. Either way it uses up a challenge, and the next play clock is 25 seconds.
- The play stands as it was simulated: a simulated play is the ruling after any review, as a real play is in the data. A challenge that was won means it was first ruled differently on the field.

### overtime (rule-versioned)
- A tied game gets a new coin toss (no deferring) and a kickoff.
- Regular season: one period (10 minutes; 15 before 2017), two timeouts each, and a tie if nobody leads when it ends. Postseason: 15-minute periods until there is a winner.
- Postseason periods come in pairs, like halves: the second goes on from where the first ended. The third starts with a kickoff by the team that won the overtime toss (the loser chooses first there, and takes the ball), with three timeouts each again. A fifth starts with a new coin toss, and so on.
- Both teams possess (regular season 2025+, postseason 2022+): the game ends when the score isn't tied and the trailing team has had its possession. Then the next score wins.
- Modified sudden death (regular season 2012-2024, postseason before 2022): the same, except that a touchdown or safety on the first possession ends the game.
- Sudden death (regular season before 2012): any score wins.
- A team has had its possession once it has had the ball and lost it, scored and finished its try, muffed a kick, or seen the kicking team recover its kickoff. A touchdown that ends the game has no try.

### injuries and disqualifications
- A player injured on a play misses the number of plays the injury says, up to the rest of the game.
- A player the play scenario disqualifies (a flagrant foul, or a second unsportsmanlike conduct foul in the game) misses the rest of it.
- After the two-minute warning of a half (and of an overtime period that has one), an injury on a scrimmage down costs the player's team a timeout, unless the other team fouled on the play, possession changed, or the play was a field goal that was good. A team with no timeout left gets an excess timeout instead; if it is the offense and the clock was running, the defense may take a 10-second runoff (the same hardcoded choice as after a foul).
- Emergency replacements: a team that runs out of quarterbacks, kickers, or punters, or is down to four offensive linemen, plays someone else there until the player is back. Who is hardcoded: a back, receiver, or tight end at quarterback; a defensive lineman, tight end, or linebacker on the line (he reports as ineligible); a defensive back or receiver as the kicker; the kicker, a spare quarterback, or a defensive back as the punter. Nobody is taken from a position that would be left short itself, so the punter doesn't also kick. A team that came to the game without a punter isn't given one.

## invariants

Checked by `validate_game`, on every simulated game in tests and in the simulator:

- Every play passes the play scenario's validator.
- Each play starts from the score, possession, spot, down, and distance the last play left, except the kickoffs that start a half or overtime, which are kicked by the team the coin toss gave them to.
- Within a period the clock never goes up; periods come in order; no play is snapped inside two minutes of a period that has a warning before the warning was given.
- Timeouts only change by a recorded stoppage that costs one (a timeout, a lost challenge, an injury after the two-minute warning), never go below zero, and reset at the half, in overtime, and before every third overtime period of a postseason game.
- A team only challenges when it may: with a timeout and a challenge left, before the two-minute warning, in regulation.
- A half never ends with a try still owed.
- Nobody is on the field while sidelined by an injury or after being disqualified.
- The final score is the sum of the scoring plays; player and team stats are the sum of the plays' stat lines.
- The winner has more points. A tie only happens after a regular season overtime.
- The game ends when time runs out in the fourth quarter or a regular season overtime, or in overtime with a winner.

## not built yet

- **replay review**: the replay official's own reviews (scores, turnovers, everything after the two-minute warning) aren't modeled: they cost nobody anything, and the play is already the ruling after review. The 10-second runoff after a review that leaves a running clock isn't either. A challenge doesn't stop a running clock: the game clock restarts on the ready signal, which the game treats like a running one.
- **timeouts**: icing the kicker and timeouts to avoid a delay of game aren't distinguished from any other (the timeout predictor is asked before the lineups are known).
- **injuries**: the 5-yard penalty for a team's second excess timeout in a half. The injured player's team calling its own timeout, or the opponent calling one, in place of the charge. Outside the last two minutes an injury doesn't stop the clock.
- **emergency replacements**: who stands in is hardcoded by position; it can become an event if it turns out to matter. A stand-in is predicted like any other player at the position, from his own (empty) record there.
- **10-second runoff**: the defense's choice and the offense's timeout are hardcoded, and the play scenario only reports the option in the last minute of a half.
- **fair-catch kick**: a kick that falls short isn't returned (like any missed field goal in the play scenario).
- **weather and field direction**: the toss winner's choice of goal isn't modeled.
