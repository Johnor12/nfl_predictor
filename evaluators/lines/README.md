# lines evaluator

Betting lines as forecasts. Scores the market's lines against what happened, which is the accuracy our simulators are aiming for, and scores a simulator's distributions on the same lines.

Every line is the same thing: a threshold on a number, with the market's probability that the number ends above it.

| market | the number | the line | probability of going over |
|---|---|---|---|
| moneyline | home points minus away points | 0 | the home team wins, from the two moneylines |
| spread | home points minus away points | the spread | the home team covers, from the spread prices |
| total | total points | the total | over, from the over/under prices |
| a player stat (`pass_yds`, `rush_yds`, `receptions`, ...) | the player's stat in the game | the prop line | 50% (prices aren't published) |

API (`from evaluators.lines import ...`):

- `lines(season, weeks=None) -> list[Line]`: every game line and player prop, with what really happened.
- `Line(market, key, line, p_over, actual)`: `key` names the number: `("margin", game_id)`, `("total", game_id)`, or `(stat, game_id, player_id)`. `actual` is None if the game hasn't been played or the player has no stat line for it.
- `score_lines(lines, samples=None) -> list[dict]`, one per market: `n`, `over` (how often the number went over), `brier` and `log_loss` of the market's probability, and `mae` of the line as a forecast of the number (not for the moneyline).
  With `samples` (`{key: [simulated values]}`) only the lines that have samples are scored, and the simulator gets the same columns from the same lines: `sim_brier` and `sim_log_loss` (its smoothed share of samples over the line), `sim_mae` (its median), and `sim_crps`.
- `no_vig(odds, other) -> float`: one side's probability from both sides' American odds, with the bookmaker's margin removed.
- `write_report(season, weeks=None, samples=None, path=None)`: markdown at `evaluation_output/lines_<season>.md` (gitignored).
- CLI: `python -m evaluators.lines --season 2026 [--weeks 1-3]`. The first run downloads each game's props (about a minute for half a season).

No simulator produces game-level distributions yet (the game scenario is next), so today the report is the market on its own. The game evaluator will pass its simulated margins, totals, and player stat lines as `samples`.
