# START
# The game's event chain.
# - run_game(ctx, predictors, rng) -> GameResult: plays one game from the coin toss to the final whistle.
# - _Game: one game in progress. Methods in chain order:
#   run (opening toss and kickoff, then step until the game is over),
#   step (the next play: the timeouts called before it, the play scenario, and the snap that never came when
#     the clock ran out first),
#   apply (the play's score, stats, history, injuries, and disqualifications),
#   after (what happens before the next play: overtime's end, a coach's challenge, the 10-second runoff, an
#     injury stoppage, the two-minute warning, and time running out),
#   challenge and injury_stoppage (what those two cost),
#   end_period (the next quarter, a kickoff for the second half or overtime, or the end of the game),
#   and the helpers toss, kickoff, play_context, charge_timeout, runoff, stop.
# step returns the next play's Situation, or None when the game is over. The clock's rules are in clock.py,
# overtime's in overtime.py, and injuries in roster.py.
# END
import dataclasses
from collections import defaultdict

from scenarios.coin_toss import TossContext, run_coin_toss
from scenarios.game import clock
from scenarios.game.overtime import Overtime
from scenarios.game.record import GameResult, Stoppage
from scenarios.game.roster import Availability
from scenarios.play import IllegalChoice, PlayContext, Situation, play_summary, run_play, summarize
from shared.rulebook import rules_for

MAX_PLAYS = 1000  # a game that gets here isn't going to end


def run_game(ctx, predictors, rng) -> GameResult:
    return _Game(ctx, predictors, rng).run()


class _Game:
    def __init__(self, ctx, predictors, rng):
        self.ctx, self.p, self.rng = ctx, predictors, rng
        self.game = ctx.game
        self.home, self.away = ctx.game.home, ctx.game.away
        self.rules = rules_for(ctx.game.season)
        self.roster = Availability(ctx.players)
        self.record, self.history, self.warned = [], [], frozenset()
        self.score = {self.home: 0, self.away: 0}
        self.stats = defaultdict(lambda: defaultdict(float))
        self.team_stats = {self.home: defaultdict(float), self.away: defaultdict(float)}
        self.overtime = self.tossed = None   # overtime's possessions, and its latest coin toss
        self.challenges = {self.home: [], self.away: []}  # each team's challenges so far: True for one it won
        self.kick_only = False               # the next down only extends the period for a fair-catch kick
        self.plays, self.quarter = 0, 1

    def run(self) -> GameResult:
        self.opening = self.toss(overtime=False)
        s = self.kickoff(self.opening.kicking, 1, clock.QUARTER, clock.TIMEOUTS)
        while s is not None:
            if self.plays >= MAX_PLAYS:
                raise RuntimeError(f"no end to the game after {MAX_PLAYS} plays")
            s = self.step(s)
        home, away = self.score[self.home], self.score[self.away]
        winner = None if home == away else self.home if home > away else self.away
        return GameResult(self.ctx, tuple(self.record), dict(self.score), winner, self.quarter,
                          {pid: dict(line) for pid, line in self.stats.items()},
                          {team: dict(line) for team, line in self.team_stats.items()},
                          tuple(self.roster.absences))

    # --- helpers ---

    def toss(self, overtime):
        toss = run_coin_toss(TossContext(self.game, self.roster.active(), overtime), self.p.toss, self.rng)
        self.record.append(toss)
        return toss

    def kickoff(self, team, quarter, seconds, timeouts) -> Situation:
        receiving = self.away if team == self.home else self.home
        return Situation("kickoff", team, receiving, float(self.rules.kickoff_line), None, None, dict(self.score),
                         quarter, float(seconds), False, self.rules.admin_play_clock,
                         {self.home: timeouts, self.away: timeouts})

    def play_context(self, s) -> PlayContext:
        return PlayContext(self.game, s, self.roster.active(), tuple(self.history), self.warned)

    def stop(self, kind, s, team=None):
        self.record.append(Stoppage(kind, s.quarter, s.clock, team))

    def charge_timeout(self, s, team, kind="timeout") -> Situation:
        self.stop(kind, s, team)
        return dataclasses.replace(s, timeouts={**s.timeouts, team: s.timeouts[team] - 1}, clock_running=False,
                                   play_clock=self.rules.admin_play_clock)

    def runoff(self, s) -> Situation:
        s = dataclasses.replace(s, clock=max(0.0, s.clock - clock.RUNOFF), clock_running=True)
        self.stop("runoff", s)
        return s

    # --- the chain ---

    def step(self, s):
        kick_only, self.kick_only = self.kick_only, False
        ctx, called = self.play_context(s), None
        for _ in range(2):  # each team may call one timeout in a dead ball
            timeout = self.p.timeout(ctx, called, self.rng)
            if timeout is None:
                break
            if s.timeouts.get(timeout.team, 0) < 1 or timeout.seconds < 0 or timeout.team == called:
                raise IllegalChoice(f"{timeout} with timeouts {s.timeouts}, after one by {called}")
            s = dataclasses.replace(s, clock=clock.at_timeout(self.game, s, timeout.seconds))
            s = self.charge_timeout(s, timeout.team)
            ctx, called = self.play_context(s), timeout.team
        result = run_play(ctx, self.p.play, self.rng)
        if kick_only and result.record[0].offense.unit != "fair_catch_kick":
            return self.end_period(s)  # the team let the period end instead: the play is discarded
        cut = clock.cut_before_snap(self.game, s, result)  # the play is discarded: it was never snapped
        if cut == "two_minute_warning":
            s = dataclasses.replace(s, clock=float(clock.WARNING), clock_running=False,
                                    play_clock=self.rules.admin_play_clock)
            self.stop("two_minute_warning", s)
            return s
        if cut == "period_end":
            return self.end_period(dataclasses.replace(s, clock=0.0))
        self.apply(result)
        return self.after(s, result)

    def apply(self, result):
        self.record.append(result)
        self.history.append(play_summary(result))
        self.score = dict(result.next.score)
        self.quarter = result.context.situation.quarter
        for pid, line in result.stats.items():
            for stat, value in line.items():
                self.stats[pid][stat] += value
        for team, line in result.team_stats.items():
            for stat, value in line.items():
                self.team_stats[team][stat] += value
        self.warned = result.warned
        self.roster.played(result.injuries, result.disqualified, self.plays)
        self.plays += 1

    def after(self, s, result):
        if self.overtime and self.overtime.over(result):
            return None
        nxt = dataclasses.replace(result.next, clock_running=result.clock_after != "snap")
        nxt = self.challenge(s, result, nxt)
        if result.runoff_option and clock.takes_runoff(s):  # the offense spends a timeout instead, if it has one
            nxt = self.charge_timeout(nxt, s.offense) if nxt.timeouts[s.offense] > 0 else self.runoff(nxt)
        if nxt.clock > 0:
            nxt = self.injury_stoppage(s, result, nxt)
        if clock.has_warning(self.game, s.quarter) and s.clock > clock.WARNING >= nxt.clock > 0:
            nxt = dataclasses.replace(nxt, clock_running=False, play_clock=self.rules.admin_play_clock)
            self.stop("two_minute_warning", nxt)
        if nxt.clock > 0:
            return nxt
        if result.untimed_down or (nxt.kind == "try" and clock.try_matters(self.game, nxt)):
            return dataclasses.replace(nxt, clock_running=False)  # the period is extended by one down
        if nxt.fair_catch_kick:  # ... or by a fair-catch kick, if the team that made the catch wants one
            self.kick_only = True
            return dataclasses.replace(nxt, clock_running=False)
        return self.end_period(nxt)

    def challenge(self, s, result, nxt):
        """A coach's challenge of the play. The play stands as it was simulated (it is the ruling after the
        review), so a challenge only costs what the rules charge for it: one of the team's challenges, and a
        timeout if it was lost."""
        allowed = clock.challengers(self.game, self.rules, s, nxt.timeouts, self.challenges)
        ruling = self.p.challenge(result.context, summarize(result), allowed, self.rng) if allowed else None
        if ruling is None:
            return nxt
        if ruling.team not in allowed:
            raise IllegalChoice(f"{ruling}, when only {allowed} may challenge")
        self.challenges[ruling.team].append(ruling.won)
        if not ruling.won:
            return self.charge_timeout(nxt, ruling.team, "challenge_lost")
        self.stop("challenge_won", nxt, ruling.team)
        return dataclasses.replace(nxt, play_clock=self.rules.admin_play_clock)

    def injury_stoppage(self, s, result, nxt):
        """After the two-minute warning an injury costs the player's team a timeout. A team without one gets
        an excess timeout, and its offense a 10-second runoff if the clock was running."""
        for team in clock.injury_timeouts(self.game, s, result):
            if nxt.timeouts[team] > 0:
                nxt = self.charge_timeout(nxt, team, "injury_timeout")
            else:
                self.stop("excess_timeout", nxt, team)
                if team == nxt.offense and nxt.clock_running and clock.takes_runoff(s):
                    nxt = self.runoff(nxt)
        return nxt

    def end_period(self, s):
        self.stop("period_end", s)
        quarter, tied = s.quarter, self.score[self.home] == self.score[self.away]
        if (quarter == 4 and not tied) or (quarter > 4 and not self.game.playoff):
            return None
        if quarter == 2:
            return self.kickoff(self.opening.second_half_kicking, 3, clock.QUARTER, clock.TIMEOUTS)
        form, seconds, timeouts = clock.overtime_setup(self.game, self.rules)
        if quarter % 2:  # play goes on from the same situation: after the first and third quarters, and every
            return dataclasses.replace(s, quarter=quarter + 1, clock_running=False,  # other overtime period
                                       clock=float(seconds if quarter > 4 else clock.QUARTER),
                                       play_clock=self.rules.admin_play_clock)
        if quarter % 4:  # two overtime periods are a half: the third starts like a second half
            return self.kickoff(self.tossed.second_half_kicking, quarter + 1, seconds, timeouts)
        self.tossed = self.toss(overtime=True)  # before overtime, and again before every fourth period of it
        self.overtime = self.overtime or Overtime(form, (self.tossed.receiving, self.tossed.kicking))
        return self.kickoff(self.tossed.kicking, quarter + 1, seconds, timeouts)
