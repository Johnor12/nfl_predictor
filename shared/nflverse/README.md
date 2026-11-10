# nflverse

Real NFL data from [nflverse](https://github.com/nflverse/nflverse-data), cached locally and converted into play scenario inputs.

API (`from shared.nflverse import ...`):

- `load(name, season) -> DataFrame`: a cached file: `pbp`, `ftn` (charting), `rosters` (weekly), `depth_charts`, `injuries`, `player_stats` (every player's stat line per game), `games` (schedule with weather, coaches, referees, betting lines). Downloads into `.cache/nflverse/` (gitignored) on first use.
- `real_plays(season, weeks=None) -> list[RealPlay]`: every real snap or free kick, in game order. `RealPlay.context` is a valid `PlayContext`, `RealPlay.actual` a dict of what happened (action, yards, points by team, touchdown, turnover, penalty, kick results, real snap-to-snap seconds), and `RealPlay.row` the pbp row index.
- `real_samples(season, weeks=None)`: iterates the same plays as `shared.priors.Sample`s: the context and `actual`, plus the play's nflverse rows (`row`, the pbp row, and `charting`, the FTN row or None). For code that reads what an event's output was: the priors builders and `evaluators/play`.

Inputs filled from data: game info (roof, surface, weather, coaches, referee, neutral site); active players (weekly roster status minus injury-report Outs, plus anyone who appears in the game's play-by-play) with position, jersey, depth chart slots from the last snapshot before kickoff, experience, draft pick, and season-to-date stats from earlier weeks; the situation (kind, possession, spot, down and distance, score, quarter and clock, timeouts); and the game's earlier plays as `history`.

Inferred, not recorded: whether the clock was running at the snap and the play clock (from the previous play), and safety kicks (the free kick after a safety).
