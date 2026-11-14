# START
# Builds the baseline timeout priors from real plays.
# - observe(tally, sample): counts one real play (see shared/priors/building.py).
#   timeout[situation key]: offense, defense, or none, by who called a timeout before the play. The key is
#   read from the situation before the timeout (shared.priors.timeout_case).
# END
from events.timeout.predictors.baseline import situation_key
from shared.priors import timeout_case


def observe(t, sample):
    ctx, caller = timeout_case(sample)
    t.c[f"timeout|{situation_key(ctx.situation)}"][caller] += 1
