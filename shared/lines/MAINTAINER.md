# MAINTAINER

- __init__.py: exports `game_lines`, `player_lines`.
- lines.py: `game_lines` (a view of the nflverse schedule), `player_lines`, `STATS` (ESPN's prop name -> our stat name), `COMBINED` and `value` (the props on a sum of stats), `BOOKS` (which book's line is kept), and the ESPN download (`_props`, `_books`, `_fetch`, `_parse`).
- test_lines.py: parsing ESPN's prop list, with and without prices; a combined prop's value; the cached lines' shape. The last two are skipped if the caches are missing.

Notes:
- ESPN's endpoint is public but undocumented: `sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/<id>/competitions/<id>/odds` lists the sportsbooks with odds for a game (the event id is the schedule's `espn` column), and `.../odds/<book>/propBets` one book's props. Which book has props changes by season (DraftKings is book 100 in 2026 and 40 before; ESPN BET is 58), so every book the index lists is read, except its in-game lines ("Live Odds"). A game with no props has no books with a `propBets` link.
- Each prop is listed twice (over and under), each side on its own item. A book that publishes prices puts the side's price on it (`current.over.american`, "Even" for +100); DraftKings in 2026 publishes none. ESPN BET also lists a ladder of other lines for the same prop ("70 or more yards": whole numbers, without a price), which aren't over/unders: `_parse` drops an unpriced whole-number line, and keeps the priced line, or else the one updated last (about 1% of DraftKings' pairs disagree by a point).
- A prop's `over_odds` or `under_odds` can be missing on its own (the book took one side down); `evaluators.lines` then scores it at 50%.
- The cache holds the parsed rows of every book and every prop type, not just the ones in `STATS`, so adding a stat doesn't need a new download (not yet kept: longest reception, rush, and completion; first-half and first-quarter yards; touchdown scorers, which have no line). Delete `.cache/lines/` after changing `_parse`: a full download of 2022 to 2026 takes about 3 minutes.
- Where several books have a line for the same player and stat, `player_lines` keeps one: a book with both prices before one without, then `BOOKS`' order.
- ESPN athlete ids are mapped to gsis ids through nflverse's `players` file. A player missing there is dropped.
- A sportsbook's "tackles" are solo tackles, nflverse's `def_tackles_solo + def_tackles_with_assist` (`shared.nflverse.STAT_COLUMNS`). With that, the tackle lines go over 43% of the time and tackles plus assists 47%, like the other markets.
- ESPN BET's lines stop after week 13 of 2025. ESPN has nothing for the rest of that regular season or the wild-card round, and DraftKings' lines for five of the playoff games after it.
- Other sources checked (2026-11-16). Free: nflverse has no player props; Sleeper's public API has weekly stat projections (means, not lines) if a second benchmark is wanted; no free source has props before 2022. Paid, for props with prices:
  - The Odds API: closing props from 2023-05 on, with prices, including solo tackles, assists, tackles plus assists, sacks, defensive interceptions, field goals, kicking points, and extra points. 10 credits per market and game; the defender and kicker markets of every game since 2023 are about 80,000 credits, one month of the $59 plan (100,000 credits), and every prop market about one month of the $119 plan. It would fill 2023, the end of 2025, and 2026's prices.
  - SportsDataIO: the only one found claiming props before 2023 (from about 2020); priced by quote, and whether it has defender and kicker markets is unverified.
  - Sports Game Odds ($299 a month), OpticOdds (about $5,000 a month, unverified), Sportradar and Unabated (by quote): more than this needs.
