# START
# Builds the baseline kick result priors from real plays.
# - observe(tally, sample): kickoff_result[landing_zone|end_zone]: return, touchback, or muff.
# END
from shared.priors import kickoff_result


def observe(t, sample):
    kickoff = kickoff_result(sample)
    if kickoff:
        zone, result = kickoff
        t.c[f"kickoff_result|{zone}"][result] += 1
