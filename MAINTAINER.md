# MAINTAINER

Technical map of the project. Read a directory's README.md for its API, and its MAINTAINER.md for its files.

## layout

The folders follow the architecture in README.md:

- README.md: project goals, concepts, and phases (plain text, edited by hand only).
- .claude/rules/general.md: working rules for agents.
- .claude/keepalive/: keeps the codespace awake while Claude Code is working, through the hooks in `.claude/settings.json` (`node .claude/keepalive/keepalive.js status`).
- pyproject.toml / uv.lock: Python 3.12+ project managed with uv (pandas, pyarrow; pytest for dev).
- events/: one package per event: its output type, and under `predictors/` one package per implementation (`baseline/` for all 20 so far: 17 play events, `coin_toss`, `toss_choice`, `timeout`), with a priors file per season from 2011 on, counted week by week. Also `baseline_priors.py`, which rebuilds every baseline's priors.
- scenarios/play/: the play scenario: inputs, event chain, rules, enforcement, stats, validator, narration, outcome summary, and the `Predictors` bundle (`load_predictors`).
- scenarios/coin_toss/: the coin toss scenario: the toss, the winner's choice, and who kicks off (`run_coin_toss`).
- scenarios/game/: the game scenario: the coin toss, then plays until the final whistle, with the clock, timeouts, halftime, overtime, injuries, and disqualifications between them (`run_game`, `validate_game`, `load_game_predictors`).
- simulators/play/: runs the play scenario over many inputs and summarizes each outcome.
- simulators/game/: plays a game many times and presents the distributions (`simulate_game`, `forecast`).
- evaluators/sample.py: which games an evaluation covers: a fixed sample of games across seasons (`sample_games`, `EVALUATED`).
- evaluators/scoring/: the evaluators' shared toolkit: fair CRPS and Brier scores, the reference to beat, sim noise, PIT histograms, reliability (`Scorecard`).
- evaluators/play/: scores the play scenario and each event predictor against real plays (`evaluate`).
- evaluators/lines/: scores betting lines against results, and a simulator's distributions on the same lines (`lines`, `score_lines`).
- evaluators/game/: scores the game scenario against real games and the betting lines, and the timeout predictor alone (`evaluate`).
- evaluators/audit/: checks the play simulator against real plays (validity and reasonableness metrics) and writes a report.
- shared/rulebook/: season-versioned rule constants from 2011 on, overtime included (`rules_for(season)`), and which seasons share a set of rules (`same_rules`, `KICKOFF`, `TRY`).
- shared/priors/: the toolkit behind the count-based baseline predictors (sampling, buckets, player picking, building priors files per season and week, and pooling what was played before a game into its priors).
- shared/nflverse/: downloads and caches nflverse data (`load`) for 2011 on (`SEASONS`), every season in the same shape; turns real plays into play scenario inputs (`real_plays`, `real_samples`) and real games into game scenario inputs (`real_games`), with each player's recent snaps from the best on-field source the season has.
- shared/lines/: betting lines: game lines from the nflverse schedule (`game_lines`) and DraftKings player props via ESPN (`player_lines`).

Not built yet: the season scenario (phase 2). Known gaps inside what is built are listed in `scenarios/play/RULES.md` and `scenarios/game/RULES.md`.

## dependencies

They point one way: evaluators -> simulators -> scenarios -> events (output types) -> nothing, with shared/rulebook and shared/priors below everything. Among the scenarios, game -> coin_toss and play.

- An event's `__init__.py` holds only its output type, so the play scenario can import it. The play scenario knows nothing about data or about any predictor implementation; `load_predictors` imports them by name.
- Predictor implementations (`events/<event>/predictors/<name>/`) sit above the play scenario: they import its public API (`from scenarios.play import ...`) for inputs and helpers, and `shared.priors`.
- The game scenario runs the child scenarios directly (`run_coin_toss`, `run_play`) and bundles their predictors with its own (`GamePredictors`). A play's outcome summary (`scenarios.play.summarize`) lives in the play scenario because the game needs it for its history.
- shared/nflverse is the one part of shared/ that isn't at the bottom: it imports `scenarios.play` and `scenarios.game` (it builds `PlayContext`s and `GameContext`s). shared/lines sits on top of it. Only `events/baseline_priors.py`, the evaluators, the game simulator's CLI, and tests import them; the scenarios never do.
- evaluators/scoring imports nothing from the rest of the project; the other evaluators score with it.

## commands

- Tests: `uv run pytest -q` (about 90 seconds with the cache). The nflverse, audit, priors-build, play and game evaluation, and lines tests skip unless `.cache/` has the 2026 files (and the 2014, 2016, 2019, and 2025 ones, for the tests that use them).
- Forecast a game: `uv run python -m simulators.game 2026_10_NE_DET --sims 1000` prints win probabilities and the distributions of the score and the main stat lines (about 0.1 seconds per simulated game and core).
- Evaluate the game scenario: `uv run python -m evaluators.game` writes `evaluation_output/game_2021-2026.md`: 160 games sampled from the last six seasons (about 3 minutes on 16 cores, 11 on 4; `--games 16 --sims 10` for a quick look, about 15 seconds; `--seasons 2026 --games 0` for every game of a season; `--no-lines` to skip the betting lines; `--swap carry=other` for another implementation).
- Evaluate the play scenario and its event predictors: `uv run python -m evaluators.play` writes `evaluation_output/play_2021-2026.md`, on the same 160 games (about 3 minutes on 16 cores, 12 on 4; `--games 16 --sims 20` for a quick look, about 20 seconds; `--swap carry=other` for another implementation).
- Score the betting lines: `uv run python -m evaluators.lines` writes `evaluation_output/lines_2021-2026.md` for the same games (downloads each game's props on first use).
- Audit: `uv run python -m evaluators.audit --season 2026` writes `audit_output/report_2026.md`.
- Rebuild the baseline priors: `uv run python -m events.baseline_priors` (every season from 2011, one file per season and predictor; about 20 minutes on 2 cores; `2026` or `2020-2026` for some of them). The first run downloads about 25 MB of nflverse files per season.
- Each week, after its games: `uv run python -m events.baseline_priors 2026` adds them to the priors (refresh the cached 2026 nflverse files first: `shared/nflverse/MAINTAINER.md`). A game is predicted from the earlier seasons and its own season's earlier weeks, so next week's forecasts only see this week once it's built.
- `NFL_PRIORS_DECAY=0.5` in the environment tries another weight for older seasons. Any evaluator, the audit, and the simulators take it.
- In this environment `UV_INDEX` points at an unauthenticated private registry. Run uv with it unset: `env -u UV_INDEX uv ...` in bash, or `$env:UV_INDEX=$null` first in PowerShell.

## conventions

- Every play and every game must be reproducible from its seed: a predictor only draws from the `random.Random` it's handed, and never iterates a set (or anything else unordered) on the way to a draw.
- A refactor shouldn't change a single simulated play. Check by hashing a few thousand seeded plays (`describe_play` output and stats) and the audit's metrics before and after.
- A predictor change is measured, not eyeballed: run `evaluators.play` before and after and compare the event's rows (and the play scenario's), then `evaluators.game` for its effect on whole games and against the betting lines. Both score the same fixed sample of games across seasons, so two runs compare case by case. A game is predicted from what was played before it (the earlier seasons and its own season's earlier weeks), so the scores are out of sample.
- Each season is predicted with everything its data has, and nothing is held back to the level of the poorest season. Priors: a season's file holds only the keys its data supports, and a predictor pools each key over the earlier seasons and weeks that have it (on-field personnel from 2016 on, charting from 2022 on; a 2026 game gets both from the seasons that have them). Inputs: a field only some seasons can fill (`Player.snaps` by kicking unit) is filled where they can, and the predictor falls back where it's empty. A new data source goes in the same way: through `shared.nflverse` into an input or a `Sample`, counted by the `priors.py` of the events it informs.
- A player's own season moves a baseline's rate toward his own: `Player.stats` (his season to date, from `shared.nflverse`) against the league's or his depth chart role's rate, shrunk by how much he has played (`shared.priors.usage` for carriers and targets, the pass rush baseline's `_dropback` for sacks and scrambles). Another one goes in the same way: the stat in `shared/nflverse/contexts.py`'s `SEASON_STATS`, one hand-set number of plays at which his season counts as much as the prior, and a before and after on the game evaluator's player rows. Anything richer than a shrunk rate is a job for a trained model.
- The clock: the data records the game clock at each snap and nothing in between. So the time teams let run before a snap or a timeout comes from the real gaps between snaps (`snap_gap` in the pre-snap and timeout priors) less the play itself (`shared.priors.PLAY_SECONDS`), and the hand-set durations of a play's parts are set to what real plays that stop the clock take. `game: plays` in `evaluators/game` is the check on all of it.
- Seasons: everything takes any season from 2011 on (`shared.nflverse.SEASONS`). What differs between seasons is handled in three places and nowhere else: the rules in `shared/rulebook` (the scenarios read every season-dependent value from it), the data's formats in `shared/nflverse` (every season comes out in one shape), and what earlier seasons can teach in `shared/priors` (pooled, older seasons discounted, and never across a rule change that the predictor ties its counts to).
- A rule change needs: the value in `shared/rulebook/rules.py`, the scenario reading it, a scripted test, and, if it changes how an event plays out, its fields in a group like `KICKOFF` with the affected priors keys tied to it.
- A scenario's outcome summary and the real outcome built from nflverse must have the same keys and meaning: `scenarios.play.summarize` with `shared/nflverse/contexts.py`, `simulators.game.summarize` with `shared/nflverse/games.py`.
- Every evaluator scores with `evaluators.scoring` (fair CRPS for numbers, fair Brier for yes/no and categories), so scores mean the same thing at every level.
- The evaluators' run time is the development loop's: a predictor runs on every simulated play, so anything it works out that doesn't change from play to play (a roster's ranking, a table built from the priors) should be worked out once. `evaluators/MAINTAINER.md` says where the time goes and how to check a speedup changes no score.

## generated files (gitignored)

- .cache/nflverse/: downloaded nflverse files.
- .cache/lines/: downloaded player prop lines, one file per played game.
- evaluation_output/: play evaluation, game evaluation, and betting lines reports.
- audit_output/: audit reports.
