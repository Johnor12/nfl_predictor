# evaluators

Evaluators score a simulator's output against something external (see the root README for the concepts).

- `scoring/`: the shared toolkit. Fair CRPS and Brier scores, a reference to beat, sim noise, PIT histograms, and reliability, for any output of any simulator.
- `play/`: the play scenario and each of its event predictors, scored against real plays (`python -m evaluators.play`).
- `lines/`: betting lines scored against results, and a simulator's distributions scored on the same lines (`python -m evaluators.lines`).
- `game/`: the game scenario scored against real games (scores, team and player stat lines) and against the betting lines, and the timeout predictor on its own (`python -m evaluators.game`).
- `audit/`: the play simulator against real plays: are the simulated plays valid, and are their overall rates reasonable?

Reports are written to `evaluation_output/` (`audit_output/` for the audit); both are gitignored.

## which games

An evaluation covers a sample of games drawn from several seasons, not one season: the aim is accuracy on any given game, and one score over many seasons says more about that than a score per season.

- `--seasons 2021-2026` (the default, `sample.EVALUATED`: the six most recent) or `--seasons 2026`, and `--weeks` to narrow them.
- `--games 160` (the default): a sample of that many of the seasons' played games. It is always the same sample, and a larger one contains a smaller one, so two runs compare on the same games. `--games 0` is every game.
- Every game is predicted from the seasons before its own (`shared/priors/README.md`), so the scores are out of sample. Three exceptions, where a season has nothing earlier to learn from and uses its own plays: kickoffs in 2024 and 2025 (each the first season of a kickoff rule), and the charted outputs in 2022 (box count, pass rushers, throwaways).

API (`from evaluators.sample import ...`): `EVALUATED`, `sample_games(seasons, weeks=None, n=None) -> {season: [game id]}` (what `evaluate` covers; `evaluators.lines.lines` takes it), and `label(seasons)` for report names.

`from evaluators import parse_weeks` reads a CLI's `--weeks` or `--seasons` value (`1-3` or `1,4`).
