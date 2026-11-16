# MAINTAINER

- __init__.py: exports `lines`, `Line`, `score_lines`, `no_vig`, `write_report`.
- lines.py: `Line`, `lines` (game lines and props from `shared.lines`, results from the nflverse schedule and player stats), `no_vig`, `score_lines`, `favorites` (moneylines from the favorite's side, for the reliability table), and `PROPS` (the prop markets: `shared.lines.STATS`' stat names). A prop's real value is `shared.lines.value` of the player's row in `shared.nflverse.stat_lines`.
- report.py: `write_report` and `lines_table`.
- __main__.py: the CLI.
- test_lines.py: `no_vig`; `score_lines` on made-up lines and samples; the cached season. The last is skipped if the caches are missing.

Notes:
- nflverse's `spread_line` is the points the home team is favored by and `result` is home minus away, so the home team covers when `result > spread_line`.
- A push (the number landing exactly on the line) isn't scored.
- A prop whose player has no stat line for the game is left out. That drops players who didn't play (a void bet), and also the few who played without recording any stat (which would have gone under).
- A prop with both prices is scored at their no-vig probability (2022 to 2025); one without (all of 2026) at 50%. A juiced line (receptions 1.5 at -160) isn't really a median, so `over` for an unpriced market can sit a few points off 50%, and the markets on rare events sit far off it (a sack line of 0.5 goes over 30% of the time, an interception line 8%).
- To add a prop market: add ESPN's name to `shared.lines.STATS` (and, for a prop on a sum of stats, its weights to `shared.lines.COMBINED`), and the stat's nflverse columns to `shared.nflverse.STAT_COLUMNS` if they aren't there. Stat names are the play scenario's (`scenarios/play/stats.py`), so a simulated stat line can be looked up by the same name.
