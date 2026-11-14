# MAINTAINER

Technical map of the project. Read a directory's README.md for its API, and its MAINTAINER.md for its files.

## layout

The folders follow the architecture in README.md:

- README.md: project goals, concepts, and phases (plain text, edited by hand only).
- .claude/rules/general.md: working rules for agents.
- pyproject.toml / uv.lock: Python 3.12+ project managed with uv (pandas, pyarrow; pytest for dev).
- events/: one package per event: its output type, and under `predictors/` one package per implementation (`baseline/` for all 20 so far: 17 play events, `coin_toss`, `toss_choice`, `timeout`). Also `baseline_priors.py`, which rebuilds every baseline's priors.
- scenarios/play/: the play scenario: inputs, event chain, rules, enforcement, stats, validator, narration, outcome summary, and the `Predictors` bundle (`load_predictors`).
- scenarios/coin_toss/: the coin toss scenario: the toss, the winner's choice, and who kicks off (`run_coin_toss`).
- scenarios/game/: the game scenario: the coin toss, then plays until the final whistle, with the clock, timeouts, halftime, overtime, and injuries between them (`run_game`, `validate_game`, `load_game_predictors`).
- simulators/play/: runs the play scenario over many inputs and summarizes each outcome.
- simulators/game/: plays a game many times and presents the distributions (`simulate_game`, `forecast`).
- evaluators/scoring/: the evaluators' shared toolkit: fair CRPS and Brier scores, the reference to beat, sim noise, PIT histograms, reliability (`Scorecard`).
- evaluators/play/: scores the play scenario and each event predictor against real plays (`evaluate`).
- evaluators/lines/: scores betting lines against results, and a simulator's distributions on the same lines (`lines`, `score_lines`).
- evaluators/game/: scores the game scenario against real games and the betting lines, and the timeout predictor alone (`evaluate`).
- evaluators/audit/: checks the play simulator against real plays (validity and reasonableness metrics) and writes a report.
- shared/rulebook/: season-versioned rule constants, overtime included (`rules_for(season)`).
- shared/priors/: the toolkit behind the count-based baseline predictors (sampling, buckets, player picking, priors files, and building them).
- shared/nflverse/: downloads and caches nflverse data (`load`); turns real plays into play scenario inputs (`real_plays`, `real_samples`) and real games into game scenario inputs (`real_games`).
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

- Tests: `uv run pytest -q` (about 2 minutes with the cache). The nflverse, audit, priors-build, play and game evaluation, and lines tests skip unless `.cache/` has the 2026 files.
- Forecast a game: `uv run python -m simulators.game 2026_10_NE_DET --sims 1000` prints win probabilities and the distributions of the score and the main stat lines (about 0.25 seconds per simulated game and core).
- Evaluate the game scenario: `uv run python -m evaluators.game --season 2026` writes `evaluation_output/game_2026.md` (about half an hour for half a season at 100 sims on 2 cores; `--weeks 1 --sims 10` for a quick look; `--no-lines` to skip the betting lines; `--swap carry=other` for another implementation).
- Evaluate the play scenario and its event predictors: `uv run python -m evaluators.play --season 2026` writes `evaluation_output/play_2026.md` (about 5 minutes on 16 cores; `--weeks 1-2 --sims 20` for a quick look; `--swap carry=other` for another implementation).
- Score the betting lines: `uv run python -m evaluators.lines --season 2026` writes `evaluation_output/lines_2026.md` (downloads each game's props on first use).
- Audit: `uv run python -m evaluators.audit --season 2026` writes `audit_output/report_2026.md`.
- Rebuild the baseline priors: `uv run python -m events.baseline_priors 2026`.
- In this environment `UV_INDEX` points at an unauthenticated private registry. Run uv with it unset: `env -u UV_INDEX uv ...` in bash, or `$env:UV_INDEX=$null` first in PowerShell.

## conventions

- Every play and every game must be reproducible from its seed: a predictor only draws from the `random.Random` it's handed, and never iterates a set (or anything else unordered) on the way to a draw.
- A refactor shouldn't change a single simulated play. Check by hashing a few thousand seeded plays (`describe_play` output and stats) and the audit's metrics before and after.
- A predictor change is measured, not eyeballed: run `evaluators.play` before and after and compare the event's rows (and the play scenario's), then `evaluators.game` for its effect on whole games and against the betting lines. The baseline priors are built from 2026, so 2026 scores are in-sample; `--season 2025` is the out-of-sample check.
- A scenario's outcome summary and the real outcome built from nflverse must have the same keys and meaning: `scenarios.play.summarize` with `shared/nflverse/contexts.py`, `simulators.game.summarize` with `shared/nflverse/games.py`.
- Every evaluator scores with `evaluators.scoring` (fair CRPS for numbers, fair Brier for yes/no and categories), so scores mean the same thing at every level.

## generated files (gitignored)

- .cache/nflverse/: downloaded nflverse files.
- .cache/lines/: downloaded player prop lines, one file per played game.
- evaluation_output/: play evaluation, game evaluation, and betting lines reports.
- audit_output/: audit reports.
