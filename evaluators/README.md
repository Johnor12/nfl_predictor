# evaluators

Evaluators score a simulator's output against something external (see the root README for the concepts).

- `scoring/`: the shared toolkit. Fair CRPS and Brier scores, a reference to beat, sim noise, PIT histograms, and reliability, for any output of any simulator.
- `play/`: the play scenario and each of its event predictors, scored against real plays (`python -m evaluators.play`).
- `lines/`: betting lines scored against results, and a simulator's distributions scored on the same lines (`python -m evaluators.lines`).
- `game/`: the game scenario scored against real games (scores, and every stat of every team and player) and against the betting lines, and the timeout and challenge predictors on their own (`python -m evaluators.game`).
- `audit/`: the play simulator against real plays: are the simulated plays valid, and are their overall rates reasonable?

Reports are written to `evaluation_output/` (`audit_output/` for the audit); both are gitignored.

## which games

An evaluation covers a sample of games drawn from several seasons, not one season: the aim is accuracy on any given game, and one score over many seasons says more about that than a score per season.

- `--seasons 2021-2026` (the default, `sample.EVALUATED`: the six most recent) or `--seasons 2026`, and `--weeks` to narrow them.
- `--games 160` (the default): a sample of that many of the seasons' played games (a game counts once its stat lines are published, a few days after it's played). It is always the same sample, and a larger one contains a smaller one, so two runs compare on the same games. `--games 0` is every game. More games, not more sims, is what makes a comparison of two versions sharper (`game/README.md`).
- Every game is predicted from what was played before it: the earlier seasons and its own season's earlier weeks (`shared/priors/README.md`), so the scores are out of sample. Three exceptions, where a season has nothing earlier to learn from and uses all of its own plays: kickoffs in 2024 and 2025 (each the first season of a kickoff rule), and the charted outputs in 2022 (box count, pass rushers, throwaways).

API (`from evaluators.sample import ...`): `EVALUATED`, `sample_games(seasons, weeks=None, n=None) -> {season: [game id]}` (what `evaluate` covers; `evaluators.lines.lines` takes it), and `label(seasons)` for report names.

## comparing two runs

A change is judged by running an evaluation before and after it, on the same games, and comparing them case by case: the two runs share the games' own difficulty, so a difference shows long before the two score tables' standard errors would let it.

- `python -m evaluators.game --save before.pkl` (and `python -m evaluators.play --save ...`) keeps a run; run it again after the change (or with `--swap`) into `after.pkl`.
- `python -m evaluators.compare before.pkl after.pkl [name ...]` prints one row per output: the two mean scores, the change, `z` (the mean difference of the cases' scores over its standard error: beyond about 2 is more than chance, and with hundreds of rows a few reach it by chance), and the real and simulated averages. A name narrows it down: `"player: tackles"`, `"game:"`.
- From code: `from evaluators.compare import save, load, compare, table`.

Both runs have to cover the same games (the same `--seasons`, `--weeks`, `--games`, and the same day's data). An output whose cases differ between the runs is left out. Simulating adds its own noise to both runs, which `z` doesn't know about when the runs' random draws differ: `game/README.md` says how small a change each row can show.

`from evaluators import parse_weeks` reads a CLI's `--weeks` or `--seasons` value (`1-3` or `1,4`). `executor(workers=None)` is where an evaluation's jobs run: a pool of worker processes (one per core), or the calling process when `workers` is 1.

## run times

Both evaluations cost about 0.17 core-seconds per game and sim with every baseline (the seven trained models, the defaults, add about 10% to a play evaluation, and the game evaluation took no longer with them than with two), and split across every core: the default 160 games at 100 sims take 11 to 12 minutes on 4 cores. The fixed cost is reading a season's files (1 to 2 seconds a season, in the worker processes). Nearly all the time is the play scenario itself, so a slow predictor shows up here first: `MAINTAINER.md` says how to find it and how to check that a speedup changes no score.
