# game evaluator

Scores the game scenario against real games and against the betting lines. Every game of a sample of played games is simulated many times from its inputs at kickoff; each simulated distribution is scored against what really happened with `evaluators.scoring`, and against the market on its own lines with `evaluators.lines`.

API (`from evaluators.game import ...`):

- `evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None, lines=()) -> Evaluation`: the played games of `seasons` (and `weeks`), or a fixed sample of `games` of them (see `evaluators/README.md`). `predictors` is a `game.GamePredictors` (each event's default implementation if omitted). Games run in parallel processes (`workers=1` to stay in this one). `lines` are `evaluators.lines.Line`s (from `lines.lines(sample_games(...))`); without them the lines section is left out. It costs about 0.17 core-seconds per game and sim: the CLI's default (160 games, 100 sims) is about 3 minutes on 16 cores and 11 on 4. Reading each season's games and scoring its timeouts run in the same worker processes.
- `Evaluation`: `seasons`, `sims`, `games`, `failures` (simulated games that raised or broke an invariant), `card` (a `scoring.Scorecard`), `lines`, and `samples` (`{line key: simulated values}`, what `lines.score_lines` takes).
- `evaluate_games(games, sims, seed, predictors, workers, lines) -> (card, samples, failures)`: the same for a list of games (anything with `.context` and `.actual`).
- `game_outputs(ctx, outcome) -> {(name, subject): value}`: the scored outputs, read the same way from a real outcome and a simulated one.
- `write_report(evaluation, path=None)`: markdown at `evaluation_output/game_<seasons>.md` (gitignored; `game_2021-2026.md`): score tables, the betting lines, PIT histograms, reliability.
- CLI: `python -m evaluators.game [--seasons 2021-2026] [--games 160] [--weeks 1-3] [--sims 100] [--swap carry=tuned] [--no-lines]`. `--swap` evaluates `events/carry/predictors/tuned/` in place of the carry event's default: run it with and without, and compare the rows (`--swap snap=baseline` is the snap event's baseline against its default, the trained model). The first run downloads each game's player props.

## what is scored

**The game scenario**, against what happened:

- `game: ...`, one case per game: margin (home minus away), total, home win, overtime, plays.
- `team: ...`, one case per team and game: points, turnovers, pass_yds, pass_att, rush_yds, rush_att, sacked, penalties, punts, fg_att.
- `player: <stat> (<role>)`, one case per active player with that depth chart role and game, whether or not he played: passing stats and rush_yds for QB1; rush_yds, rush_att, rec_yds, receptions for RB1 and RB2; rec_yds and receptions for WR1, WR2, WR3, TE1, TE2; fg_made and xp_made for K; and `touchdown` (a rushing or receiving one) for the backs and receivers. A 3 means third or lower on the depth chart.

**The betting lines** (when given): the market's probability and line scored against the result, and the simulator's share of samples over the same line, on the moneyline, spread, total, and every player prop (see `evaluators/lines/README.md`).

**The timeout predictor alone** (`timeout: caller (...)`): sampled on every real play's situation as it stood before any timeout, and scored against who called one (offense, defense, none). The coin toss isn't in the data, so its two predictors aren't scored.

## reading the results

- The score columns are explained in `evaluators/scoring/README.md`.
- **Out of sample**: a game is predicted from what was played before it (the exceptions are listed in `evaluators/README.md`).
- **Inputs at kickoff**: the active players include everyone who appeared in the real game, which is the inactive list announced before kickoff, not hindsight about who got hurt.
- The market is the benchmark: the simulator's Brier, log loss, and MAE on a market are directly comparable with the market's own columns. Player props are scored at 50% for the market because prices aren't published, and only 2026's games have any (`shared/lines/README.md`).
- **Lines as inputs**: a game's inputs include the spread and total before it (`Game.spread`, `Game.total`), and a predictor may read them (none does yet). For such a predictor the market columns compare the simulator with a benchmark it has partly been told: beating the market on a line still means something, matching it means less. The scores against what really happened aren't affected.
- A simulated probability is the smoothed share of samples over the line, so with few sims it is coarse; `sim CRPS` doesn't depend on the number of sims.
- `game: plays` is where the clock gets scored (the play evaluator can't): too many plays means the simulated game uses too little clock per play.
