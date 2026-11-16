# START
# Who is available to play: the active players minus the ones sidelined by an injury or disqualified, with
# an emergency replacement where a team has run out of players at a position it can't play without.
# - Availability(players): active() -> the players available for the next play (the same tuple until someone
#   leaves or returns); played(injuries, disqualified, index) -> one play (number `index`) has gone by:
#   sidelined players move a play closer to returning, then the play's injuries and disqualifications take
#   effect; absences -> (player, index of the first play missed, plays missed) for each one applied.
# - REQUIRED: positions the play scenario can't field a legal team without, and how many it needs there.
# - STAND_INS: who fills in at each of them, by position, in the order they are asked. A stand-in is the
#   same player with the position he now plays (an offensive lineman with a receiver's number has reported
#   as ineligible), until the player he replaced is back.
# END
import dataclasses
from collections import Counter

REQUIRED = {"QB": 1, "OL": 5, "K": 1, "P": 1}
STAND_INS = {"QB": ("RB", "WR", "TE"), "OL": ("DL", "TE", "LB"), "K": ("P", "DB", "WR"), "P": ("K", "QB", "DB", "WR")}
REST_OF_GAME = 999


def _positions(players) -> dict:
    """{team: how many players it has at each position}."""
    counts = {}
    for p in players:
        counts.setdefault(p.team, Counter())[p.position] += 1
    return counts


class Availability:
    def __init__(self, players):
        self.players = players
        self.out = {}              # player id -> plays left to miss
        self.absences = []
        self.dressed = _positions(players)  # a team that came without a punter isn't given one
        self._active = players

    def active(self) -> tuple:
        return self._active

    def _fielded(self) -> tuple:
        """Everyone who isn't out, with a stand-in wherever a team is short at a required position. A
        stand-in is never taken from a required position that would be left short itself."""
        active = [p for p in self.players if p.id not in self.out]
        for team, count in _positions(active).items():
            for position, needed in REQUIRED.items():
                order = STAND_INS[position]
                while count[position] < min(needed, self.dressed[team][position]):
                    spare = [p for p in active if p.team == team and count[p.position] > REQUIRED.get(p.position, 0)]
                    if not spare:
                        break
                    stand_in = min(spare, key=lambda p: order.index(p.position) if p.position in order else len(order))
                    active[active.index(stand_in)] = dataclasses.replace(stand_in, position=position)
                    count[stand_in.position] -= 1
                    count[position] += 1
        return tuple(active)

    def played(self, injuries, disqualified, index):
        returning = [pid for pid, left in self.out.items() if left <= 1]
        for pid in returning:
            del self.out[pid]
        for pid, left in self.out.items():
            if left < REST_OF_GAME:
                self.out[pid] = left - 1
        leaving = [(injury.player, injury.plays_out) for injury in injuries]
        leaving += [(player, REST_OF_GAME) for player in disqualified]
        for player, plays_out in leaving:
            if player not in self.out:
                self.out[player] = plays_out
                self.absences.append((player, index + 1, plays_out))
        if returning or leaving:
            self._active = self._fielded()
