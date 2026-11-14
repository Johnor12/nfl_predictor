# START
# Tests for rules_for: spot checks of rule changes by season.
# END
from shared.rulebook import rules_for


def test_kickoff_eras():
    assert rules_for(2015).kickoff_touchback_line == 20
    assert rules_for(2016).kickoff_touchback_line == 25
    assert rules_for(2024).kickoff_touchback_line == 30
    assert rules_for(2026).kickoff_touchback_line == 35
    assert not rules_for(2023).dynamic_kickoff and rules_for(2024).dynamic_kickoff


def test_try_changes():
    assert rules_for(2014).pat_line == 2 and rules_for(2015).pat_line == 15
    assert not rules_for(2014).defensive_try_points


def test_overtime_eras():
    assert rules_for(2011).overtime_format == "sudden_death" and rules_for(2011).playoff_overtime_format == "modified"
    assert rules_for(2016).overtime_format == "modified" and rules_for(2016).overtime_seconds == 900
    assert rules_for(2024).overtime_seconds == 600 and rules_for(2024).playoff_overtime_format == "both_possess"
    assert rules_for(2026).overtime_format == "both_possess"
