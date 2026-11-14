# START
# Who is available to play: the active players minus the ones sidelined by an injury or disqualified.
# - Availability(players): active() -> the players available for the next play (the same tuple until someone
#   leaves or returns); played(injuries, disqualified, index) -> one play (number `index`) has gone by:
#   sidelined players move a play closer to returning, then the play's injuries and disqualifications take
#   effect; absences -> (player, index of the first play missed, plays missed) for each one applied.
# - REQUIRED: positions the play scenario can't field a legal team without. A team's last available players
#   there play through an injury or a disqualification (emergency replacements aren't modeled).
# END
REQUIRED = {"QB": 1, "OL": 5, "K": 1, "P": 1}
REST_OF_GAME = 999


class Availability:
    def __init__(self, players):
        self.players = players
        self.by_id = {p.id: p for p in players}
        self.out = {}              # player id -> plays left to miss
        self.absences = []
        self._active = players

    def active(self) -> tuple:
        return self._active

    def _spare(self, player) -> bool:
        needed = REQUIRED.get(player.position)
        if needed is None:
            return True
        healthy = sum(p.team == player.team and p.position == player.position for p in self._active)
        return healthy > needed

    def played(self, injuries, disqualified, index):
        returning = [pid for pid, left in self.out.items() if left <= 1]
        for pid in returning:
            del self.out[pid]
        for pid, left in self.out.items():
            if left < REST_OF_GAME:
                self.out[pid] = left - 1
        if returning:
            self._active = tuple(p for p in self.players if p.id not in self.out)
        leaving = [(injury.player, injury.plays_out) for injury in injuries]
        for player, plays_out in leaving + [(player, REST_OF_GAME) for player in disqualified]:
            if player in self.out or not self._spare(self.by_id[player]):
                continue
            self.out[player] = plays_out
            self.absences.append((player, index + 1, plays_out))
            self._active = tuple(p for p in self._active if p.id != player)
