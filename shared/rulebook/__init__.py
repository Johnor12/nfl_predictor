# START
# rulebook: NFL rules, looked up by season.
# - rules_for(season) -> Rules: every season-dependent constant the scenarios need.
# - Rules: frozen dataclass of those constants (see rules.py).
# END
from shared.rulebook.rules import Rules, rules_for

__all__ = ["Rules", "rules_for"]
