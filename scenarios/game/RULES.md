# game scenario rules

The NFL rules the game scenario hardcodes, the invariants every game satisfies, and what isn't built yet. The API and the event chain are in [README.md](README.md). Values are from memory and should be checked against the official rulebook.

## hardcoded NFL rules

### periods
- Four 15-minute quarters. The first and third end without changing anything but the clock: play resumes from the same situation.
- The first half ends when the second quarter does, whatever the situation. The second half starts with a kickoff by the team the coin toss gave it to, with three timeouts each again.
- A period can't end on a play with an accepted defensive foul (an untimed down follows), and a touchdown as time expires is still followed by its try. The try is skipped when the game is ending and it can't change who wins.
- Otherwise the period ends when the clock reaches zero. If a running clock runs out before the ball is snapped, the play never happens.

### the clock between plays
- After a play the clock keeps running, restarts on the ready-for-play signal, or waits for the snap, as the play scenario reports. The first two both run before the next snap.
- Two-minute warning in the second and fourth quarters, and in overtime (postseason: in the even overtime periods). The clock stops at 2:00, or after the play that crosses it. If a running clock reaches 2:00 before the snap, the play is snapped at 2:00 with the clock stopped.
- 10-second runoff: when a play reports the option, the defense takes it if it's the first half or it isn't behind. The offense spends a timeout instead if it has one. After a runoff the clock starts on the ready-for-play signal; declined or bought off with a timeout, it waits for the snap.
- Play clock: 25 seconds after a timeout, the two-minute warning, and the start of a period.

### timeouts
- Three per team per half. Calling one stops the clock until the snap. A running clock runs until the timeout is called, and a team that calls one gets it in before the two-minute warning or the end of the period.
- One timeout at most before each play.

### overtime (rule-versioned)
- A tied game gets a new coin toss (no deferring) and a kickoff.
- Regular season: one period (10 minutes; 15 before 2017), two timeouts each, and a tie if nobody leads when it ends. Postseason: 15-minute periods, three timeouts each, until there is a winner.
- Both teams possess (regular season 2025+, postseason 2022+): the game ends when the score isn't tied and the trailing team has had its possession. Then the next score wins.
- Modified sudden death (regular season 2012-2024, postseason before 2022): the same, except that a touchdown or safety on the first possession ends the game.
- Sudden death (regular season before 2012): any score wins.
- A team has had its possession once it has had the ball and lost it, scored and finished its try, muffed a kick, or seen the kicking team recover its kickoff. A touchdown that ends the game has no try.

### injuries and disqualifications
- A player injured on a play misses the number of plays the injury says, up to the rest of the game.
- A player the play scenario disqualifies (a flagrant foul, or a second unsportsmanlike conduct foul in the game) misses the rest of it.

## invariants

Checked by `validate_game`, on every simulated game in tests and in the simulator:

- Every play passes the play scenario's validator.
- Each play starts from the score, possession, spot, down, and distance the last play left, except the kickoffs that start a half or overtime, which are kicked by the team the coin toss gave them to.
- Within a period the clock never goes up; periods come in order; no play is snapped inside two minutes of a period that has a warning before the warning was given.
- Timeouts only change by a recorded timeout, never go below zero, and reset at the half and in overtime.
- The first half never ends with a try still owed.
- Nobody is on the field while sidelined by an injury or after being disqualified.
- The final score is the sum of the scoring plays; player and team stats are the sum of the plays' stat lines.
- The winner has more points. A tie only happens after a regular season overtime.
- The game ends when time runs out in the fourth quarter or a regular season overtime, or in overtime with a winner.

## not built yet

- **coach's challenges and replay review**: a simulated play's outcome is the final ruling. A lost challenge only shows up as a timeout (the timeout priors count it as one).
- **timeouts**: one per dead ball, not one per team. Icing the kicker and timeouts to avoid a delay of game aren't distinguished from any other.
- **injuries and disqualifications**: stoppages aren't charged in the last two minutes. A team's last available quarterback, kicker, punter, and five offensive linemen play through an injury or a disqualification, because emergency replacements aren't modeled.
- **10-second runoff**: the defense's choice and the offense's timeout are hardcoded, and the play scenario only reports the option in the last minute of a half.
- **postseason overtime**: every period after the first continues from the same situation. The kickoff that starts a third overtime period, and timeouts resetting there, aren't modeled.
- **end of a half**: a fair-catch kick.
- **weather and field direction**: the toss winner's choice of goal isn't modeled.
