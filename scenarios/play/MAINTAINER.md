# MAINTAINER

- README.md: the design (inputs/outputs, event chain, rules, invariants) and the current implementation's gaps.
- __init__.py: the public API (re-exports).
- context.py: inputs (`Game`, `Player`, `Situation`, `PlaySummary`, `PlayContext`) and `validate_context`.
- events.py: the predictor interface (`Predictors`) and every event's output dataclass.
- record.py: facts the chain records (`Sack`, `Pass`, `Carry`, `LooseBall`, `Kick`), `Dead` (how and where the ball died), and `PlayResult`.
- field.py: coordinates (`rel`/`to_x`), line of scrimmage, field goal distance, eligible receivers, and lineup and formation legality.
- chain.py: `run_play`, which runs the event chain, masks illegal choices, and applies live-ball rules (goal lines, safeties, touchbacks, momentum, who may advance a loose ball, kick rules).
- fouls.py: the foul catalog, which fouls are possible on a play, and enforcement (accept/decline, offsetting, spots, half the distance).
- outcome.py: scores, the next situation (downs, possession, next kind of play), the clock, the accept/decline value, and assembling the `PlayResult`.
- stats.py: player and team stat crediting from the facts.
- validate.py: `validate_play`, the invariants.
- describe.py: narration.
- testing.py: synthetic contexts, random legal ("chaos") predictors, and `scripted` predictors for rule tests.
- test_play.py: fuzzed invariants and hand-built rule tests.

Notes:
- All spots inside a play are in play coordinates (yards from the play's offense's goal line). Predictors receive and return the same coordinates. The carry predictor is the exception: it gets the carrier's own yard line and returns yards in the carrier's direction of travel.
- Every live-ball path ends in a `Dead`. Penalties produce a new `Dead` (with `series`/`no_play`), and `outcome.next_situation` turns any `Dead` into the next situation, so enforcement and normal plays share one path.
- When adding a rule, add a scripted test in test_play.py. The fuzz test only proves internal consistency, not that the rule is right.
