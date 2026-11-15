# MAINTAINER

- __init__.py: exports `evaluate`, `Evaluation`, `write_report`.
- evaluate.py: `evaluate` (the sampled games, eight to a process, scorecards merged), `play_outputs` (the scenario's scored outputs), and the per-play loop: simulate with traced predictors, score the scenario, score each event case.
- cases.py: `event_cases` (a real play -> each event's real inputs and output), `stand_ins` (the cases once per run, each run leading once), `read` (the same outputs from a predictor's sample), `Run` (a traced simulated run), the stand-in lookup, and the real lineups where the season has them.
- report.py: `write_report`.
- __main__.py: the CLI.
- test_play.py: the scenario scored against itself is calibrated; tracing; a hand-built real play's cases; a real week; a sample across old and new seasons. The last two are skipped if the nflverse cache is missing.

Notes:
- To score a new output of the play scenario, add it to `play_outputs`. It reads a real outcome (`RealPlay.actual`) and a simulated one (`summarize`) the same way, so the key has to mean the same thing in both.
- To score a new event (or a new output of one), add a builder to `BUILDERS` and a reader to `READERS` in cases.py. The builder says which real plays have the event, with its real inputs and output; the reader returns the same output names from a predictor's sample. Name an output once: `Case.actual` and the reader's dict share keys.
- Outputs are typed by their values: `bool`, `str`, or a number (see `evaluators/scoring`). Convert what comes off a pandas row (`bool(...)`, `float(...)`).
- The predictors are traced by wrapping each one to record its arguments and output, so a stand-in's inputs (allowed fouls, allowed kick results, the record) are exactly what the chain computed. Nothing from `scenarios/play` internals is imported.
- A predictor whose only input is the context (lineups) isn't sampled again: the simulated runs' outputs are its samples.
- `event_cases(sample, runs)` takes its stand-ins from the first run that fits. `_score_events` builds the cases once per run (`stand_ins`), with that run moved to the front, and draws sample `i` with the `i`-th set of arguments. The cases are rebuilt `sims` times per play, so a builder must stay cheap: what doesn't depend on the runs (the real lineups) is built once and handed to every builder. With one stand-in for all samples, a predictor that reads the lineups (who carries, who is targeted) was scored on a single random lineup instead of on the spread of them.
- Real carries stop at the goal line, so a sampled carry's yards are capped there and its end counts as a touchdown.
- Not scored, because the data doesn't say: the lineups' players and personnel in seasons without participation data, formations beyond shotgun, pre-snap time, hang times, tacklers, who recovers a fumble, onside kicks, kickoffs fielded in the end zone (their return yards are counted from the goal line).
- A reader gets the whole `Case`: its `args`, and `real`, whatever else of the real play it needs (the lineups reader compares a sampled lineup with the players really on the field; the pass rush reader is told whether the play was charted, and counts a sampled throwaway as a throw where it wasn't, as the real one would have been).
- Real lineups replace the stand-in's only for events whose other inputs are real (offensive formation, carry, loose ball, kicks). The snap, pass rush, target, and pass result take a formation too, which only a simulated run has, so they keep that run's lineups.
- An output that looks badly calibrated may be a definition mismatch between real and simulated outcomes. The reliability table is where it shows: first downs were off until `summarize` counted touchdowns as nflverse does.
- Each play's seed comes from `seed`, its game, and its position in the game, so a game scores the same alone or with other games.
