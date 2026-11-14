# START
# Overtime: who has had the chance to possess the ball, and whether the score ends the game.
# - Overtime(form, teams): form is the season's format (shared/rulebook): sudden_death, modified, or
#   both_possess.
# - Overtime.over(result) -> bool: call after every overtime play; True when the game is over.
# A team's opportunity starts when it first has the ball (a kick it muffs, or a kickoff the kicking team
# recovers, counts) and is done once it no longer has it: after a change of possession, or a free kick (a try
# still belongs to the team that scored). The game ends when the score isn't tied and the trailing team's
# opportunity is done. Under "modified" anything but a field goal on the first possession also ends it, and
# under "sudden_death" any score does.
# END
from scenarios.play import FREE_KICKS, Carry, Kick, LooseBall, facts


class Overtime:
    def __init__(self, form, teams):
        self.form = form
        self.had = dict.fromkeys(teams, False)
        self.done = dict.fromkeys(teams, False)

    def over(self, result) -> bool:
        s, nxt = result.context.situation, result.next
        holder = None if nxt.kind in FREE_KICKS else nxt.offense
        possessed = {holder} if s.kind in FREE_KICKS else {holder, s.offense}
        if not result.no_play:
            possessed |= {c.team for c in facts(result.record, Carry)}
            possessed |= {b.last_team for b in facts(result.record, LooseBall) if b.cause == "muff"}
            if s.kind in FREE_KICKS and any(k.result == "kicking_recovery" for k in facts(result.record, Kick)):
                possessed.add(s.defense)
        for team in self.had:
            self.had[team] = self.had[team] or team in possessed
            self.done[team] = self.done[team] or (self.had[team] and holder != team)
        if len(set(nxt.score.values())) == 1:
            return False
        trailing = min(nxt.score, key=nxt.score.get)
        if self.form == "sudden_death" or self.done[trailing]:
            return True
        return self.form == "modified" and any(how != "field_goal" for _, _, how in result.scores)
