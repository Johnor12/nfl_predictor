# MAINTAINER

- __init__.py: exports `lines`, `Line`, `score_lines`, `no_vig`, `write_report`.
- lines.py: `Line`, `lines` (game lines and props from `shared.lines`, results from the nflverse schedule and player stats), `no_vig`, `score_lines`, `favorites` (moneylines from the favorite's side, for the reliability table), and `ACTUAL` (our stat name -> nflverse player stats column).
- report.py: `write_report`.
- __main__.py: the CLI.
- test_lines.py: `no_vig`; `score_lines` on made-up lines and samples; the cached season. The last is skipped if the caches are missing.

Notes:
- nflverse's `spread_line` is the points the home team is favored by and `result` is home minus away, so the home team covers when `result > spread_line`.
- A push (the number landing exactly on the line) isn't scored.
- A prop whose player has no row in nflverse's player stats is left out. That drops players who didn't play (a void bet), and also the few who played without recording any stat (which would have gone under).
- Props are scored at 50% because ESPN publishes the lines without prices. A juiced line (receptions 1.5 at -160) isn't really a median, so `over` for a market can sit a few points off 50%.
- To add a prop market: add ESPN's name to `shared.lines.STATS` and the nflverse column to `ACTUAL`. Stat names are the play scenario's (`scenarios/play/stats.py`), so a simulated stat line can be looked up by the same name.
