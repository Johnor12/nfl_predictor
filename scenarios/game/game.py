# START
# The game's event chain.
# - run_game(ctx, predictors, rng) -> GameResult: plays one game from the coin toss to the final whistle.
# - _Game: one game in progress. Methods in chain order:
#   run (opening toss and kickoff, then step until the game is over),
#   step (the next play: a timeout if one is called, the play scenario, and the snap that never came when
#     the clock ran out first),
#   apply (the play's score, stats, history, injuries, and disqualifications),
#   after (what the clock does next: the 10-second runoff, the two-minute warning, overtime's end, and time
#     running out),
#   end_period (the next quarter, the second half kickoff, overtime, or the end of the game),
#   and the helpers toss, kickoff, play_context, charge_timeout, stop.
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
from scenarios.play import IllegalChoice, PlayContext, Situation, play_summary, run_play
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
        self.overtime = None
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

    def charge_timeout(self, s, team) -> Situation:
        self.stop("timeout", s, team)
        return dataclasses.replace(s, timeouts={**s.timeouts, team: s.timeouts[team] - 1}, clock_running=False,
                                   play_clock=self.rules.admin_play_clock)

    # --- the chain ---

    def step(self, s):
        ctx = self.play_context(s)
        caller = self.p.timeout(ctx, self.rng)
        if caller is not None:
            if s.timeouts.get(caller, 0) < 1:
                raise IllegalChoice(f"{caller} has no timeout to call")
            s = self.charge_timeout(s, caller)
            ctx = self.play_context(s)
        result = run_play(ctx, self.p.play, self.rng)
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
        nxt = dataclasses.replace(result.next, clock_running=result.clock_after != "snap")
        if result.runoff_option and clock.takes_runoff(s):
            if nxt.timeouts[s.offense] > 0:  # the offense spends a timeout instead
                nxt = self.charge_timeout(nxt, s.offense)
            else:
                nxt = dataclasses.replace(nxt, clock=max(0.0, nxt.clock - clock.RUNOFF), clock_running=True)
                self.stop("runoff", nxt)
        if clock.has_warning(self.game, s.quarter) and s.clock > clock.WARNING >= nxt.clock > 0:
            nxt = dataclasses.replace(nxt, clock_running=False, play_clock=self.rules.admin_play_clock)
            self.stop("two_minute_warning", nxt)
        if self.overtime and self.overtime.over(result):
            return None
        if nxt.clock > 0:
            return nxt
        if result.untimed_down or (nxt.kind == "try" and clock.try_matters(self.game, nxt)):
            return dataclasses.replace(nxt, clock_running=False)  # the period is extended by one down
        return self.end_period(nxt)

    def end_period(self, s):
        self.stop("period_end", s)
        admin = self.rules.admin_play_clock
        if s.quarter in (1, 3):
            return dataclasses.replace(s, quarter=s.quarter + 1, clock=float(clock.QUARTER), clock_running=False,
                                       play_clock=admin)
        if s.quarter == 2:
            return self.kickoff(self.opening.second_half_kicking, 3, clock.QUARTER, clock.TIMEOUTS)
        form, seconds, timeouts = clock.overtime_setup(self.game, self.rules)
        if s.quarter == 4:
            if self.score[self.home] != self.score[self.away]:
                return None
            toss = self.toss(overtime=True)
            self.overtime = Overtime(form, (toss.receiving, toss.kicking))
            return self.kickoff(toss.kicking, 5, seconds, timeouts)
        if not self.game.playoff:
            return None
        return dataclasses.replace(s, quarter=s.quarter + 1, clock=float(seconds), clock_running=False,
                                   play_clock=admin)
