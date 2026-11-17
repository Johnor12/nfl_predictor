# START
# Tests for the coaching staffs. Skipped unless the schedule and the play-caller file are already in
# .cache/nflverse (no downloads in tests).
# - test_every_team_has_a_staff_in_every_game: a head coach and both play callers for every team and game
#   from 2011 on, and a coordinator wherever staff.csv names one.
# - test_stints_are_well_formed: staff.csv's roles and weeks; a team's coordinator stints don't overlap.
# - test_known_staffs: a head coach who calls the offense, an interim head coach the schedule misses, a
#   coordinator replaced during the season, and a team without a coordinator of that title.
# END
import pandas as pd
import pytest

from shared.nflverse.download import CACHE, SEASONS
from shared.nflverse.staff import ROLES, STINTS, staff

pytestmark = pytest.mark.skipif(not ((CACHE / "games.csv").exists() and (CACHE / "all_playcallers.csv").exists()),
                                reason="nflverse cache missing")


def test_every_team_has_a_staff_in_every_game():
    stints = pd.read_csv(STINTS)
    vacant = {(s.season, s.team, s.role) for s in stints[stints.name.isna()].itertuples()}
    for season in SEASONS:
        staffs = staff(season)
        assert len(staffs) >= 2 * 256
        for (game, team), coaches in staffs.items():
            assert coaches.head_coach and coaches.offensive_play_caller and coaches.defensive_play_caller, (game, team)
            for role in ("offensive_coordinator", "defensive_coordinator"):
                assert getattr(coaches, role) or (season, team, role) in vacant, (game, team, role)


def test_stints_are_well_formed():
    stints = pd.read_csv(STINTS)
    assert set(stints.role) <= set(ROLES) and (stints.first_week <= stints.last_week).all()
    assert stints.season.between(SEASONS[0], SEASONS[-1]).all() and stints.source.notna().all()
    for _, held in stints.groupby(["season", "team", "role"]):
        weeks = held.sort_values("first_week")
        assert all(first > last for first, last in zip(weeks.first_week.tolist()[1:], weeks.last_week.tolist())), held


def test_known_staffs():
    chiefs = staff(2023)["2023_01_DET_KC", "KC"]
    assert chiefs.head_coach == chiefs.offensive_play_caller == "Andy Reid"
    assert (chiefs.offensive_coordinator, chiefs.defensive_play_caller) == ("Matt Nagy", "Steve Spagnuolo")
    assert staff(2015)["2015_04_NYJ_MIA", "MIA"].head_coach == "Joe Philbin"
    assert staff(2015)["2015_06_MIA_TEN", "MIA"].head_coach == "Dan Campbell"    # the schedule keeps Philbin
    assert staff(2024)["2024_06_BUF_NYJ", "NYJ"].head_coach == "Jeff Ulbrich"    # ... and Saleh
    bills = [staff(2023)[game, "BUF"].offensive_coordinator for game in ("2023_10_DEN_BUF", "2023_11_NYJ_BUF")]
    assert bills == ["Ken Dorsey", "Joe Brady"]
    assert staff(2019)["2019_01_SF_TB", "SF"].offensive_coordinator is None      # Kyle Shanahan had none
