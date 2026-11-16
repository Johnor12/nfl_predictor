# MAINTAINER

- README.md: the API, the event chain, and the rules.
- __init__.py: the public API (re-exports).
- toss.py: all of it: `TossContext`, `Toss`, `TossPredictors`, `load_toss_predictors`, `allowed_choices`, `run_coin_toss`.
- test_coin_toss.py: each choice's kickoffs, illegal choices, and the baseline predictors.

Notes:
- The game scenario is the only caller: once before the opening kickoff, once more if the game goes to overtime, and again before every fourth overtime period of a postseason game after that.
- The events' packages hold no output types (a team name and a choice are plain strings), so nothing here imports them except by name in `load_toss_predictors`.
