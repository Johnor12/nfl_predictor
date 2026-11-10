# MAINTAINER

- __init__.py: exports `game_lines`, `player_lines`.
- lines.py: `game_lines` (a view of the nflverse schedule), `player_lines`, `STATS` (ESPN's prop name -> our stat name), and the ESPN download (`_props`, `_fetch`, `_parse`).
- test_lines.py: parsing ESPN's prop list; the cached lines' shape. The last two are skipped if the caches are missing.

Notes:
- ESPN's endpoint is public but undocumented: `sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/<id>/competitions/<id>/odds/100/propBets` (100 is DraftKings; the event id is the schedule's `espn` column). It returns 404 for a game with no props.
- Each prop is listed twice (over and under) with only the line (`current.target.value`, `open.target.value`), no price. About 1% of the pairs disagree by a point; `_parse` keeps the one updated last.
- The cache holds the parsed rows for every prop type, not just the ones in `STATS`, so adding a stat doesn't need a new download. Delete `.cache/lines/` after changing `_parse`.
- ESPN athlete ids are mapped to gsis ids through the weekly rosters' `espn_id`. A player missing there is dropped.
- Other sources checked: nflverse has no player props; Sleeper's public API has weekly stat projections (means, not lines) if a second benchmark is wanted.
