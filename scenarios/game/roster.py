# START
# Who is available to play: the active players minus the ones sidelined by an injury.
# - Availability(players): active() -> the players available for the next play (the same tuple until someone
#   leaves or returns); played(injuries, index) -> one play (number `index`) has gone by: sidelined players
#   move a play closer to returning, then the play's injuries take effect; absences -> (player, index of the
#   first play missed, plays missed) for every injury applied.
# - REQUIRED: positions the play scenario can't field a legal team without. A team's last healthy players
#   there play through an injury (emergency replacements aren't modeled).
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

    def played(self, injuries, index):
        returning = [pid for pid, left in self.out.items() if left <= 1]
        for pid in returning:
            del self.out[pid]
        for pid, left in self.out.items():
            if left < REST_OF_GAME:
                self.out[pid] = left - 1
        if returning:
            self._active = tuple(p for p in self.players if p.id not in self.out)
        for injury in injuries:
            if injury.player in self.out or not self._spare(self.by_id[injury.player]):
                continue
            self.out[injury.player] = injury.plays_out
            self.absences.append((injury.player, index + 1, injury.plays_out))
            self._active = tuple(p for p in self._active if p.id != injury.player)
