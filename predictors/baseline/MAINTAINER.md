# MAINTAINER

- __init__.py: `baseline_predictors` (wraps `Baseline` into a `Predictors` bundle) and the priors I/O re-exports.
- predictors.py: `Baseline`, one method per event. Hand-set rules are marked in comments.
- lineups.py: personnel mix, depth-chart lineups for offense, defense (base/nickel/dime, 4-3 or 3-4 aware) and special teams units, and formation templates.
- roles.py: player roles (`RB1`, `WR3`), position groups, and the bucket functions shared by priors and predictors.
- priors.py: `build_priors` from `nflverse.real_plays` (+ FTN charting), the nflverse penalty-name map, and the CLI.
- priors_2026.json: the built priors (raw counts and histograms).
- test_baseline.py: baseline plays on synthetic contexts are valid, plus spot checks.

Notes:
- Priors are keyed by strings like `"3|4-6|7"` (down|distance bucket|field bucket). The predictors back off to coarser keys when a cell has few samples (`_blend`).
- Yardage histograms come from plays far from the goal line (so touchdowns don't cut off long gains), plus separate goal-to-go histograms (`*_goal`, by 1-2/3-5/6-10 yards to go).
- After changing priors.py, rebuild the JSON and rerun `python -m audit` to see the effect.
