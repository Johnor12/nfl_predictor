# evaluators

Evaluators score a simulator's output against something external (see the root README for the concepts).

- `scoring/`: the shared toolkit. Fair CRPS and Brier scores, a reference to beat, sim noise, PIT histograms, and reliability, for any output of any simulator.
- `play/`: the play scenario and each of its event predictors, scored against real plays (`python -m evaluators.play`).
- `lines/`: betting lines scored against results, and a simulator's distributions scored on the same lines (`python -m evaluators.lines`).
- `audit/`: the play simulator against real plays: are the simulated plays valid, and are their overall rates reasonable?

Reports are written to `evaluation_output/` (`audit_output/` for the audit); both are gitignored.

`from evaluators import parse_weeks` reads a CLI's `--weeks` value (`1-3` or `1,4`).

Planned (phase 0/1): the game simulator against betting lines and player props, by passing its simulated margins, totals, and stat lines to `lines.score_lines`.
