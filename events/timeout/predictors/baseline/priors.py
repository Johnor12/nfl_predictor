# START
# Builds the baseline timeout priors from real plays.
# - observe(tally, sample): counts one real play (see shared/priors/building.py).
#   timeout[situation key]: offense, defense, or none, by who called a timeout before the play. The key is
#   read from the situation before the timeout (shared.priors.timeout_case).
#   snap_gap[how late|offense or defense]: histograms of the game seconds since the previous snap, for the
#   timeouts called before a scrimmage down with the clock running (the last play, then the wait for the call).
# END
from events.timeout.predictors.baseline import late, situation_key
from shared.priors import present, timeout_case


def observe(t, sample):
    ctx, caller = timeout_case(sample)
    s, gap = ctx.situation, sample.actual["seconds_since_snap"]
    t.c[f"timeout|{situation_key(s)}"][caller] += 1
    if caller != "none" and s.kind == "scrimmage" and s.clock_running and present(gap):
        t.hist[f"snap_gap|{late(s)}|{caller}"].append(gap)
