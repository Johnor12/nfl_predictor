# START
# Tests for what a game's inputs say about who plays: the starting quarterback of a played game, and each
# player's recent snaps (no cache needed).
# - test_the_starter_is_first_at_quarterback: the quarterbacks listed ahead of him move down one; nobody
#   else's depth chart changes, and a starter the chart already has first changes nothing.
# - test_only_a_quarterback_starts: a receiver who threw the first pass doesn't.
# - test_starters_are_the_first_passers: each team's first pass or sack names its starter.
# - test_snaps_cover_the_weeks_a_player_played: the weeks he missed don't count against him.
# END
import pandas as pd

from scenarios.play import Player
from shared.nflverse.contexts import SNAP_WEEKS, _Rosters, _start, _starters


def _team():
    return [Player("a", "A", "KC", "QB", depth=(("QB", 1),)), Player("b", "B", "KC", "QB", depth=(("QB", 2), ("H", 1))),
            Player("c", "C", "KC", "QB", depth=(("QB", 3),)), Player("w", "W", "KC", "WR", depth=(("WR", 1),))]


def test_the_starter_is_first_at_quarterback():
    ranks = {p.id: p.depth for p in _start(_team(), "b")}
    assert ranks == {"a": (("QB", 2),), "b": (("QB", 1), ("H", 1)), "c": (("QB", 3),), "w": (("WR", 1),)}
    players = _team()
    assert _start(players, "a") is players and _start(players, None) is players
    unlisted = _start(_team() + [Player("d", "D", "KC", "QB")], "d")
    assert [p.rank("QB") for p in unlisted] == [2, 3, 4, None, 1]


def test_only_a_quarterback_starts():
    players = _team()
    assert _start(players, "w") is players


def test_starters_are_the_first_passers():
    rows = pd.DataFrame({"posteam": ["KC", "KC", None, "DEN", "KC"], "passer_player_id": [None, "b", "x", "q", "a"],
                         "order_sequence": [1, 2, 3, 4, 5]})
    assert _starters(rows) == {"KC": "b", "DEN": "q"}


def test_snaps_cover_the_weeks_a_player_played():
    index = pd.MultiIndex.from_tuples(
        [("starter", week, "offense") for week in (1, 2, 3, 4, 5)] + [("backup", week, "offense") for week in (6, 7, 8, 9)]
        + [("backup", 9, "kickoff")], names=["player", "week", "unit"])
    weekly = pd.Series([60.0, 60, 60, 60, 60, 50, 50, 50, 50, 5], index=index)
    snaps = _Rosters._recent_snaps(weekly, pd.DataFrame({"week": range(1, 11)}))
    assert SNAP_WEEKS == 4 and snaps[1] == {} and snaps[3] == {"starter": (("offense", 120.0),)}
    assert snaps[10]["starter"] == (("offense", 240.0),)  # back from five weeks out: his last four games
    assert snaps[10]["backup"] == (("kickoff", 5.0), ("offense", 200.0)) and set(snaps) == set(range(1, 12))
