# lines

Betting lines: what the market expected, gathered as benchmarks for the evaluators.

API (`from shared.lines import ...`):

- `game_lines(season) -> DataFrame`: one row per game with closing lines and American odds: `game_id`, `week`, `home`, `away`, `spread` (points the home team is favored by; negative when the away team is), `home_spread_odds`, `away_spread_odds`, `total`, `over_odds`, `under_odds`, `home_moneyline`, `away_moneyline`. From the nflverse schedule.
- `player_lines(season, weeks=None, games=None) -> DataFrame` (`weeks` and `games`, a list of game ids, each narrow it down): one row per game, player, and stat: `game_id`, `week`, `player_id` (gsis), `player`, `stat`, `line`, `open`, `over_odds`, `under_odds` (American; nan where the book's prices aren't published), `book`. Sportsbooks' player props as published by ESPN's public API. `line` is the latest value, which is the closing line once the game has been played.
- `STATS`: the props kept, ESPN's name -> our stat name. `COMBINED`: the props on a sum of stats, name -> `{stat: weight}`.
- `value(stat, line) -> float`: a stat's value in a stat line (`{stat: value}`, real or simulated), or a combined stat's weighted sum.

Stats (the play scenario's stat names), for every kind of player a book offers a prop on:

- passers: `pass_yds`, `pass_cmp`, `pass_att`, `pass_td`, `int_thrown`, `pass_yds+rush_yds`
- runners and receivers: `rush_yds`, `rush_att`, `rec_yds`, `receptions`, `rush_yds+rec_yds`
- defenders: `tackles` (solo), `assists`, `tackles+assists`, `sacks`, `interceptions`
- kickers: `fg_made`, `xp_made`, `kick_pts` (3 a field goal, 1 an extra point)

What ESPN has, by season (every played game, 2026-11-16):

| season | games with props | lines | books | prices | markets |
|---|---|---|---|---|---|
| 2011 to 2021 | 0 | 0 | | | |
| 2022 | 155 of 284 | 243 | DraftKings, MGM | all | interceptions thrown, tackles |
| 2023 | 231 of 285 | 591 | DraftKings, MGM, ESPN BET, Caesars | all | tackles, interceptions thrown, assists |
| 2024 | 281 of 285 | 17,634 | ESPN BET | all | every stat above but `tackles` and `assists` |
| 2025 | 197 of 285 (weeks 1 to 13, and five playoff games) | 14,588 | ESPN BET, DraftKings | 90% | every stat above but `assists` |
| 2026 | all 136 | 11,766 | DraftKings | none | every stat above but `interceptions` |

A game's props are downloaded on first use and cached under `.cache/lines/` (gitignored) once the game has been played. An upcoming game's are fetched every time, because they still move. A game without props has none (remembered in the cache, so it's asked once).

Game lines go back as far as the schedule does. Props before 2022 aren't in any free source found; `MAINTAINER.md` lists the paid ones.
