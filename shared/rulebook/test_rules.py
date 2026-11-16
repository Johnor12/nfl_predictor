# START
# Tests for rules_for: spot checks of rule changes by season (kickoffs, tries, overtime, challenges), and
# same_rules on the kickoff and try fields.
# END
from shared.rulebook import KICKOFF, TRY, rules_for, same_rules


def test_kickoff_eras():
    assert rules_for(2015).kickoff_touchback_line == 20
    assert rules_for(2016).kickoff_touchback_line == 25
    assert rules_for(2024).kickoff_touchback_line == 30
    assert rules_for(2026).kickoff_touchback_line == 35
    assert not rules_for(2023).dynamic_kickoff and rules_for(2024).dynamic_kickoff
    assert [rules_for(season).kickoff_fair_catch_line for season in (2022, 2023, 2024)] == [0, 25, 0]


def test_try_changes():
    assert rules_for(2014).pat_line == 2 and rules_for(2015).pat_line == 15
    assert not rules_for(2014).defensive_try_points


def test_overtime_eras():
    assert rules_for(2011).overtime_format == "sudden_death" and rules_for(2011).playoff_overtime_format == "modified"
    assert rules_for(2016).overtime_format == "modified" and rules_for(2016).overtime_seconds == 900
    assert rules_for(2024).overtime_seconds == 600 and rules_for(2024).playoff_overtime_format == "both_possess"
    assert rules_for(2026).overtime_format == "both_possess"


def test_challenges():
    assert rules_for(2023).third_challenge_wins == 2 and rules_for(2024).third_challenge_wins == 1


def test_same_rules():
    assert same_rules(2016, 2023, KICKOFF) and not same_rules(2023, 2024, KICKOFF) and not same_rules(2024, 2025, KICKOFF)
    assert same_rules(2015, 2026, TRY) and not same_rules(2014, 2015, TRY)
    assert same_rules(2011, 2026, ())
