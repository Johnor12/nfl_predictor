# nflverse

Real NFL data from [nflverse](https://github.com/nflverse/nflverse-data), cached locally and converted into play and game scenario inputs.

API (`from shared.nflverse import ...`):

- `SEASONS`: the seasons the system covers: 2011 (the first the rulebook has) through the current one.
- `load(name, season) -> DataFrame`: a cached file, or None where nflverse has none for the season: `pbp`, `ftn` (charting, 2022 on), `participation` (who was on the field for each play, with personnel groups; 2016 on, published after the season), `snap_counts` (each player's snaps per game, 2013 on), `rosters` (weekly), `depth_charts`, `injuries`, `player_stats` (every player's stat line per game), `games` (schedule with weather, coaches, referees, betting lines). Downloads into `.cache/nflverse/` (gitignored) on first use.
- `real_plays(season, weeks=None, games=None) -> list[RealPlay]`: every real snap or free kick, in game order (`weeks` and `games`, a list of game ids, each narrow it down). `RealPlay.context` is a valid `PlayContext`, `RealPlay.actual` a dict of what happened (action, yards, points by team, touchdown, turnover, penalty, kick results, the real game seconds to the next snap and since the previous one (`seconds_to_next`, `seconds_since_snap`), and `timeout`: the team that called one before the play), and `RealPlay.row` the pbp row index.
- `real_samples(season, weeks=None, games=None)`: iterates the same plays as `shared.priors.Sample`s: the context and `actual`, plus the play's nflverse rows (`row`, the pbp row; `charting`, the FTN row or None; `participation`, who was on the field, or None), each a plain object with the file's columns as attributes (`row.yards_gained`). For code that reads what an event's output was: the priors builders and `evaluators/play`.
- `real_games(season, weeks=None, games=None) -> list[RealGame]`: every game in the schedule, played or not. `RealGame.context` is a `GameContext` with the same game info and active players as the game's real plays. `RealGame.actual` is what happened, or None if the game hasn't been played: `points` by team, `margin` (home minus away), `total`, `winner`, `overtime`, `plays`, `teams` (`{team: {stat: value}}`), and `players` (`{player id: {stat: value}}`), with the play scenario's stat names. The same keys as `simulators.game.summarize`.
- `STAT_COLUMNS`: the play scenario's stat names -> nflverse's player stats columns.

Inputs filled from data: game info (roof, surface, weather, coaches, referee, neutral site); active players (weekly roster status minus injury-report Outs, plus anyone who appears in the game's play-by-play) with position, jersey, depth chart slots from the last snapshot before kickoff, experience, draft pick, season-to-date stats from earlier weeks (the play scenario's stat names, plus how he has been used: `offense_snaps`, `carries` (designed runs), `dropbacks`, `scrambles`, `times_sacked`), and recent snaps; the situation (kind, possession, spot, down and distance, score, quarter and clock, timeouts); the game's earlier plays as `history`; and `warned`, the players already flagged for unsportsmanlike conduct in the game.

On-field personnel, from the best source each season has: a player's `snaps` are his snaps in his team's games over the four weeks before this one, by unit. A season with a participation file (2016 to 2025) counts them play by play in the play scenario's units (`offense`, `defense`, `punt`, `punt_return`, `field_goal`, `field_goal_block`, `kickoff`, `kick_return`). A season without one (2013 to 2015, and 2026 until nflverse publishes it) uses the per-game snap counts, which only say `offense`, `defense`, or `special_teams`. 2011 and 2012 have neither, and nobody has snaps.

A context is the state after any timeout before the play: the timeout is already charged and the clock stopped. `shared.priors.timeout_case` rebuilds the state before it.

A game that hasn't been played uses each team's latest weekly roster, without the game-day inactives, so its inputs are rougher (and sometimes unusable: no kicker activated yet).

Inferred, not recorded: whether the clock was running at the snap and the play clock (from the previous play), and safety kicks (the free kick after a safety).

Every season comes out in the same shape, whatever nflverse's files looked like that year:

- Teams have their current codes everywhere (the 2015 St. Louis Rams are `LA`, as in the play-by-play); a game id keeps the code of its day (`2015_01_SEA_STL`).
- Positions are the play scenario's (`OL`, `DL`, `LB`, `DB`); the rosters before 2016 list tackles, ends, and corners.
- Depth chart slots have the names nflverse uses from 2025 on (`PK`, `KR`, `LCB`). Before 2025 the charts are weekly and in the teams' own words; the common slots are renamed, the rest are kept as they are. They also run a week or two behind what teams actually did.
- From 2016 to 2018 the weekly rosters don't mark game-day inactives, so a team's active players are everyone on the roster who isn't ruled out on the injury report (about 53 instead of 46 to 48).
