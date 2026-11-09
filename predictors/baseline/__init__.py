# START
# Baseline predictors for the play scenario: simple priors from a season of real plays plus hand-set rules.
# - baseline_predictors(season=2026, priors=None) -> Predictors: ready to pass to run_play.
# - build_priors(season) / save_priors(priors, season) / load_priors(season): the priors file.
# END
import dataclasses

from predictors.baseline.predictors import Baseline
from predictors.baseline.priors import build_priors, load_priors, save_priors
from scenarios.play import Predictors


def baseline_predictors(season: int = 2026, priors: dict | None = None) -> Predictors:
    baseline = Baseline(priors or load_priors(season))
    return Predictors(**{f.name: getattr(baseline, f.name) for f in dataclasses.fields(Predictors)})


__all__ = ["baseline_predictors", "build_priors", "load_priors", "save_priors"]
