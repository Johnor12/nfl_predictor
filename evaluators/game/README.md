# game evaluator

Scores the game scenario against real games and against the betting lines. Every game of a sample of played games is simulated many times from its inputs at kickoff; each simulated distribution is scored against what really happened with `evaluators.scoring`, and against the market on its own lines with `evaluators.lines`.

API (`from evaluators.game import ...`):

- `evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None, lines=()) -> Evaluation`: the played games of `seasons` (and `weeks`), or a fixed sample of `games` of them (see `evaluators/README.md`). `predictors` is a `game.GamePredictors` (each event's default implementation if omitted). Games run in parallel processes (`workers=1` to stay in this one). `lines` are `evaluators.lines.Line`s (from `lines.lines(sample_games(...))`); without them the lines section is left out. It costs about 0.17 core-seconds per game and sim: the CLI's default (160 games, 100 sims) is about 3 minutes on 16 cores and 11 on 4. Reading each season's games and scoring its timeouts and challenges run in the same worker processes.
- `Evaluation`: `seasons`, `sims`, `games`, `failures` (simulated games that raised or broke an invariant), `card` (a `scoring.Scorecard`), `lines`, and `samples` (`{line key: simulated values}`, what `lines.score_lines` takes).
- `evaluate_games(games, sims, seed, predictors, workers, lines) -> (card, samples, failures)`: the same for a list of games (anything with `.context` and `.actual`).
- `game_outputs(ctx, outcome) -> {(name, subject): value}`: the scored outputs, read the same way from a real outcome and a simulated one.
- `write_report(evaluation, path=None)`: markdown at `evaluation_output/game_<seasons>.md` (gitignored; `game_2021-2026.md`): the game and team scores, every player stat with its roles pooled, the event predictors, the betting lines, then every player stat by role, PIT histograms, and reliability. The CLI prints it down to the players by role.
- CLI: `python -m evaluators.game [--seasons 2021-2026] [--games 160] [--weeks 1-3] [--sims 100] [--swap carry=tuned] [--no-lines] [--save run.pkl]`. `--save` keeps the evaluation for `python -m evaluators.compare` (`evaluators/README.md`): with this many rows, that is how two runs are read. `--swap` evaluates `events/carry/predictors/tuned/` in place of the carry event's default: run it with and without, and compare the rows (`--swap snap=baseline` is the snap event's baseline against its default, the trained model). The first run downloads each game's player props.

## what is scored

**The game scenario**, against what happened:

- `game: ...`, one case per game: margin (home minus away), total, home win, overtime, plays.
- `team: ...`, one case per team and game: points, turnovers, and every stat a player can have (`shared/nflverse/README.md`, "every player": the box score, and from 2018 on the charted stats), summed over the team.
- `player: <stat> (<role>)`, one case per active player and game, whether or not he played, for every stat his position has a part in:

  | position | stats |
  |---|---|
  | QB | passing, the charted pressure on him, rushing, fumbles and two-point plays, flags |
  | RB, FB, WR | rushing, receiving, what was charted of both (contact, broken tackles, drops), fumbles and two-point plays, returns (not FB), flags |
  | TE | receiving, drops and broken tackles, fumbles and two-point plays, flags |
  | OL, LS | flags |
  | DL, LB, DB | every defensive stat, the charted rush and coverage, flags, and returns for DB |
  | K, P | kicking, punting |

  A stat outside a position's list (a receiver's pass) is still in his team's row. The backs, receivers, and quarterbacks also get `touchdown` (a rushing or receiving one, yes or no) and `fantasy` (fantasy points, a point per reception).
- Roles: a quarterback, back, receiver, or tight end by depth chart rank (`WR1`; a 3 means third or lower); a lineman or a defender as a `starter` (first at a depth chart slot) or a `backup`; anyone else by position.
- `player: <stat>` in the report: a stat's roles together, each weighted by its cases. The reference is each role's own, so the skill says what the forecast adds to knowing a player's role, for the stat as a whole.

**The betting lines** (when given): the market's probability and line scored against the result, and the simulator's share of samples over the same line, on the moneyline, spread, total, and every player prop (see `evaluators/lines/README.md`).

**Telling the teams apart** (when given the lines): how far the simulator's expected margin and total differ from game to game, next to the line's, and how many points the line and the result move per simulated point (`evaluators.lines.expectations`).

**The timeout predictor alone** (`timeout: caller (...)`): sampled on every real play's situation as it stood before any timeout, and scored against who called one (offense, defense, none).

**The challenge predictor alone** (`challenge: who and ruling`): sampled on every real play a coach could challenge, and scored against who challenged it and how the review came out (offense won, offense lost, defense won, defense lost, none).

The coin toss isn't in the data, so its two predictors aren't scored.

## reading the results

- The score columns are explained in `evaluators/scoring/README.md`.
- **A player row's skill**: the reference forecasts every player of a role with the role's real distribution, so a positive skill means the simulator tells one starting linebacker from another. A role that mixes regulars with players who never see the field (a backup lineman) has an easy reference to beat on usage alone. Read `mean` against `sim mean` first: most of what was wrong with defenders' stats was a total that was off (tackles, passes defended, flags), not who got them.
- **Rare stats** (a safety, a return touchdown, a blocked kick) score at their reference whatever the simulator does; their `mean` and `sim mean` are the check that it makes them about as often as they happen.
- **Charted stats** are scored against Pro Football Reference's charting, whose totals the simulator reproduces at league rates (who is hurried, who misses a tackle): they say less about a game than the box score does, and their skill is mostly who is on the field.
- **Out of sample**: a game is predicted from what was played before it (the exceptions are listed in `evaluators/README.md`).
- **Inputs at kickoff**: the active players include everyone who appeared in the real game, which is the inactive list announced before kickoff, not hindsight about who got hurt. The quarterback who started is first on the depth chart, as he is announced before kickoff too (`shared/nflverse/MAINTAINER.md`); how long he lasted is not an input.
- The market is the benchmark: the simulator's Brier, log loss, and MAE on a market are directly comparable with the market's own columns. A player prop's market probability comes from its two prices (2022 to 2025), and is 50% where they aren't published (2026). 2024 on has props for every kind of player, defenders and kickers included; 2022 and 2023 have a few per game, and earlier seasons none (`shared/lines/README.md`).
- **Telling the teams apart**: read this table for a change to who is playing next to the scores. It asks directly what the game rows' scores answer slowly: the line is a far less noisy stand-in for how good the teams are than one result. More than 1 point of line per simulated point means the simulator knows who is better and makes too little of it (1.8 ± 0.2 on 2026-11-17, with the expected margin's spread at 2.3 points against the line's 5.8). Each number has its standard error beside it: at 480 games and 50 sims a spread is good to about 0.13 points, so a single input rarely shows here either, and several together do.
- **Lines as inputs**: a game's inputs include the spread and total before it (`Game.spread`, `Game.total`), and a predictor may read them (none does yet). For such a predictor the market columns compare the simulator with a benchmark it has partly been told: beating the market on a line still means something, matching it means less. The scores against what really happened aren't affected.
- A simulated probability is the smoothed share of samples over the line, so with few sims it is coarse; `sim CRPS` doesn't depend on the number of sims.
- `game: plays` is where the clock gets scored (the play evaluator can't): too many plays means the simulated game uses too little clock per play.

## how many games and sims

The scores are fair, so the number of sims doesn't bias them. It sets how much two runs of one system differ from simulating alone (sim noise), and so the smallest change a comparison of two runs can show. `sims for 1%` says it per row: a row that needs 635 sims shows a change of √(635 / 100) = 2.5% at 100.

- For who gets a stat (a defender's tackles, a receiver's targets) the default is plenty: there are thousands of player cases, and a change in how players are picked showed at 5 to 10 standard errors. It is the game rows that need more games.
- The default (160 games, 100 sims) is a first look, not a verdict on a small change. The smallest change that stands 2 standard errors clear of sim noise (2026-11-16): `game: home win` 4.7%, `game: margin` and `game: total` 2.5%, the `team:` rows about 2%, a player's yards and counts 1.3 to 2.4%, his touchdown 2.3 to 4.6%. One predictor swap usually moves the game rows by less (every who-is-playing input together moved the margin by 3.5%).
- It is enough for bias (`mean` against `sim mean`): there the limit is the number of real games, not the sims.
- To compare two versions, add games, not sims. Sim noise depends on games times sims, whichever is raised, so they cost the same; more games also shrink the part of the error that comes from the games themselves, which more sims don't touch. On the who-is-playing comparison at 160 games and 100 sims the margin's difference had a standard error of 1.58%: about 1.26% from simulating and 0.95% from the games. Three times the games would make that about 0.9%, three times the sims about 1.2%.
- `--games 480` (about 9 minutes on 16 cores) shows 1.5% on the margin and 2.7% on the winner. `--games 0` (1,560 games on 2026-11-16, about 28 minutes on 16 cores) shows 0.8% and 1.5%; with `--sims 50` it takes half as long and shows 1.1% and 2.1%. The time is games times sims; the sample of a larger run contains a smaller one's.
- Read `game: margin` before `game: home win`: the same question at about half the noise.
- A small change is the play evaluator's to measure (it scores every play); the game evaluator says what the change adds up to over a game.
