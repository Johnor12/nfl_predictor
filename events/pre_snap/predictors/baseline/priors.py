# START
# Builds the baseline pre-snap priors from real plays.
# - observe(tally, sample): snaps[n]: scrimmage downs and tries; fouls[type|side]: pre-snap fouls;
#   fouler[type][position group]: who the flag was on;
#   snap_gap[game script]: histograms of the game seconds since the previous snap, on scrimmage downs
#   snapped with the clock running on a full play clock (the last play, then the wait for this snap).
# END
from shared.priors import PRESNAP, flag, flagged, present, script
from shared.rulebook import rules_for


def observe(t, sample):
    s, gap = sample.context.situation, sample.actual["seconds_since_snap"]
    if s.kind in ("scrimmage", "try"):
        t.c["snaps"]["n"] += 1
    if (s.kind == "scrimmage" and s.clock_running and present(gap)
            and s.play_clock == rules_for(sample.context.game.season).play_clock):
        t.hist[f"snap_gap|{script(s)}"].append(gap)
    foul = flag(sample)
    if foul and foul[0] in PRESNAP:
        t.c["fouls"]["|".join(foul)] += 1
        if flagged(sample):
            t.c[f"fouler|{foul[0]}"][flagged(sample)] += 1
