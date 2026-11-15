# lines

Betting lines: what the market expected, gathered as benchmarks for the evaluators.

API (`from shared.lines import ...`):

- `game_lines(season) -> DataFrame`: one row per game with closing lines and American odds: `game_id`, `week`, `home`, `away`, `spread` (points the home team is favored by; negative when the away team is), `home_spread_odds`, `away_spread_odds`, `total`, `over_odds`, `under_odds`, `home_moneyline`, `away_moneyline`. From the nflverse schedule.
- `player_lines(season, weeks=None, games=None) -> DataFrame` (`weeks` and `games`, a list of game ids, each narrow it down): one row per game, player, and stat: `game_id`, `week`, `player_id` (gsis), `player`, `stat`, `line`, `open`. DraftKings' player props as published by ESPN's public API. `line` is the latest value, which is the closing line once the game has been played.

Stats (the play scenario's stat names): `pass_yds`, `pass_cmp`, `pass_att`, `pass_td`, `int_thrown`, `rush_yds`, `rush_att`, `rec_yds`, `receptions`, `fg_made`, `xp_made`.

A game's props are downloaded on first use and cached under `.cache/lines/` (gitignored) once the game has been played. An upcoming game's are fetched every time, because they still move. ESPN publishes the lines but not their prices.

Game lines go back as far as the schedule does. ESPN only has props for 2026's games: none of the 2021 to 2025 games tried had any. Such a game simply has no props (remembered in the cache, so it's asked once), and a sample across seasons scores props on its 2026 games alone.
