# START
# rulebook: NFL rules, looked up by season.
# - rules_for(season) -> Rules: every season-dependent constant the scenarios need.
# - Rules: frozen dataclass of those constants (see rules.py).
# - same_rules(season, other, fields) -> bool: two seasons agree on those Rules fields; KICKOFF and TRY are
#   the fields that change how kickoffs and tries are played.
# END
from shared.rulebook.rules import KICKOFF, TRY, Rules, rules_for, same_rules

__all__ = ["Rules", "rules_for", "same_rules", "KICKOFF", "TRY"]
