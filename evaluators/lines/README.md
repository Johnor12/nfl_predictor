# lines evaluator

Betting lines as forecasts. Scores the market's lines against what happened, which is the accuracy our simulators are aiming for, and scores a simulator's distributions on the same lines.

Every line is the same thing: a threshold on a number, with the market's probability that the number ends above it.

| market | the number | the line | probability of going over |
|---|---|---|---|
| moneyline | home points minus away points | 0 | the home team wins, from the two moneylines |
| spread | home points minus away points | the spread | the home team covers, from the spread prices |
| total | total points | the total | over, from the over/under prices |
| a player stat (`pass_yds`, `receptions`, `tackles+assists`, `sacks`, `kick_pts`, ...: `shared.lines.STATS`) | the player's stat in the game, or the combined stat's weighted sum | the prop line | from the over and under prices; 50% where they aren't published |

API (`from evaluators.lines import ...`):

- `lines(games) -> list[Line]`: every game line and player prop of the games, with what really happened. `games` is `{season: [game id]}`, from `evaluators.sample.sample_games(seasons, weeks, n)`.
- `Line(market, key, line, p_over, actual)`: `key` names the number: `("margin", game_id)`, `("total", game_id)`, or `(stat, game_id, player_id)`. `actual` is None if the game hasn't been played or the player has no stat line for it.
- `score_lines(lines, samples=None) -> list[dict]`, one per market: `n`, `over` (how often the number went over), `brier` and `log_loss` of the market's probability, and `mae` of the line as a forecast of the number (not for the moneyline).
  With `samples` (`{key: [simulated values]}`) only the lines that have samples are scored, and the simulator gets the same columns from the same lines: `sim_brier` and `sim_log_loss` (its smoothed share of samples over the line), `sim_mae` (its median), and `sim_crps`.
- `expectations(lines, samples, resamples=200) -> list[dict]`, one for the margin and one for the total: how far the simulator's expectation of the number differs from game to game, next to the line's. `spread` is the standard deviation of its expected value across the games and `line_spread` the line's; `correlation` is between the two; `line_per_point` and `result_per_point` are how many points the line, and the real result, move for each point the expectation moves. The noise of simulating a finite number of times is taken out of all of them on average (the two halves of each game's samples estimate it), and `se` holds each one's standard error, from drawing the games again `resamples` times: with few sims they are unbiased and wide. A simulator that tells the teams apart as well as the market has the line's spread and 1 for the rest; one that knows who is better and makes too little of it has more than 1 per point.
- `no_vig(odds, other) -> float`: one side's probability from both sides' American odds, with the bookmaker's margin removed.
- `write_report(games, samples=None, path=None)`: markdown at `evaluation_output/lines_<seasons>.md` (gitignored).
- `lines_table(rows) -> list[str]` and `expectations_table(rows) -> list[str]`: `score_lines`' and `expectations`' rows as markdown tables, for other reports.
- CLI: `python -m evaluators.lines [--seasons 2021-2026] [--games 160] [--weeks 1-3]`: the same sample of games the other evaluators score (`evaluators/README.md`). The first run downloads each game's props.

This package's own report is the market on its own. `evaluators/game` passes the game simulator's margins, totals, and player stat lines as `samples`, and reports both side by side.
