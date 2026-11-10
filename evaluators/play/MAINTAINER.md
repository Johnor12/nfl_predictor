# MAINTAINER

- __init__.py: exports `evaluate`, `Evaluation`, `write_report`.
- evaluate.py: `evaluate` (one process per week, scorecards merged), `play_outputs` (the scenario's scored outputs), and the per-play loop: simulate with traced predictors, score the scenario, score each event case.
- cases.py: `event_cases` (a real play -> each event's real inputs and output), `read` (the same outputs from a predictor's sample), `Run` (a traced simulated run), and the stand-in lookup.
- report.py: `write_report`.
- __main__.py: the CLI.
- test_play.py: the scenario scored against itself is calibrated; tracing; a hand-built real play's cases; a real week. The last is skipped if the nflverse cache is missing.

Notes:
- To score a new output of the play scenario, add it to `play_outputs`. It reads a real outcome (`RealPlay.actual`) and a simulated one (`summarize`) the same way, so the key has to mean the same thing in both.
- To score a new event (or a new output of one), add a builder to `BUILDERS` and a reader to `READERS` in cases.py. The builder says which real plays have the event, with its real inputs and output; the reader returns the same output names from a predictor's sample. Name an output once: `Case.actual` and the reader's dict share keys.
- Outputs are typed by their values: `bool`, `str`, or a number (see `evaluators/scoring`). Convert what comes off a pandas row (`bool(...)`, `float(...)`).
- The predictors are traced by wrapping each one to record its arguments and output, so a stand-in's inputs (allowed fouls, allowed kick results, the record) are exactly what the chain computed. Nothing from `scenarios/play` internals is imported.
- A predictor whose only input is the context (lineups) isn't sampled again: the simulated runs' outputs are its samples.
- Real carries stop at the goal line, so a sampled carry's yards are capped there and its end counts as a touchdown.
- Not scored, because the data doesn't say: the lineups' players and personnel, formations beyond shotgun, pre-snap time, hang times, tacklers, who recovers a fumble, onside kicks, kickoffs fielded in the end zone (their return yards are counted from the goal line).
- An output that looks badly calibrated may be a definition mismatch between real and simulated outcomes. The reliability table is where it shows: first downs were off until `summarize` counted touchdowns as nflverse does.
- Each play's seed comes from `seed`, its week, and its position in the week, so a week scores the same alone or with other weeks.
