# START
# Scoring the play scenario and each of its event predictors against real plays.
# - evaluate(season=2026, weeks=None, sims=100, seed=0, predictors=None, workers=None) -> Evaluation: every
#   real play of the weeks is simulated `sims` times and scored; each week runs in its own process.
# - Evaluation: season, weeks, sims, plays, failures (simulated plays that raised or broke an invariant), and
#   card, a scoring.Scorecard with outputs named "play: yards (scrimmage)" or "carry: yards (run)".
# - play_outputs(ctx, outcome) -> {name: value}: the play scenario's scored outputs, read the same way from a
#   real outcome (RealPlay.actual) and a simulated one (simulators.play.summarize). The clock isn't one of
#   them: nflverse times a play from its snap to the next snap, the scenario from the previous play's end.
# Internals: _evaluate_week (one week's scorecard), _score_play (the scenario: the simulated outcomes against
#   the real one), _score_events (each event case: `sims` samples of its predictor against the real output),
#   _traced / _runs (the predictors wrapped to record every call, split into one cases.Run per simulated run).
# END
import dataclasses
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from evaluators.play.cases import Run, event_cases, read
from evaluators.scoring import Scorecard
from scenarios.play import load_predictors
from shared.nflverse import load, real_samples
from simulators.play import simulate_play, summarize


@dataclass
class Evaluation:
    season: int
    weeks: list
    sims: int
    plays: int
    failures: int
    card: Scorecard


def play_outputs(ctx, outcome) -> dict:
    s = ctx.situation
    points = float(outcome["points"][s.offense] - outcome["points"][s.defense])
    if s.kind == "scrimmage":
        return {"action (scrimmage)": outcome["action"], "yards (scrimmage)": float(outcome["yards"]),
                "first down (scrimmage)": bool(outcome["first_down"]),
                "touchdown (scrimmage)": bool(outcome["touchdown"]),
                "turnover (scrimmage)": bool(outcome["turnover"]), "penalty (scrimmage)": bool(outcome["penalty"]),
                "points for minus against (scrimmage)": points}
    if s.kind == "try":
        return {"action (try)": outcome["action"], "points for minus against (try)": points}
    return {"touchback (free kick)": bool(outcome["touchback"]),
            "return yards (free kick)": float(outcome["return_yards"])}


def _traced(predictors):
    calls = []

    def trace(event):
        predict = getattr(predictors, event)

        def traced(*args):
            out = predict(*args)
            calls.append((event, args[1:-1], out))
            return out
        return traced

    events = [f.name for f in dataclasses.fields(predictors)]
    return dataclasses.replace(predictors, **{event: trace(event) for event in events}), calls


def _runs(calls) -> list[Run]:
    runs = []
    for event, args, out in calls:
        if event == "lineups":
            runs.append(Run(out, {}))
        runs[-1].calls.setdefault(event, []).append((args, out))
    return runs


def _score_play(card, ctx, actual, results):
    simulated = [play_outputs(ctx, summarize(result)) for result in results]
    for name, value in play_outputs(ctx, actual).items():
        if value is not None:
            card.add(f"play: {name}", [outputs[name] for outputs in simulated], value)


def _score_events(card, predictors, sample, runs, sims, rng):
    ctx = sample.context
    for case in event_cases(sample, runs):
        predict = getattr(predictors, case.event)
        if case.args is None:
            outs = []
        elif case.args:
            outs = [predict(ctx, *case.args, rng) for _ in range(sims)]
        else:  # the context is the predictor's only input, so the runs have already sampled it
            outs = [run.calls[case.event][0][1] for run in runs]
        samples = [read(ctx, case, out) for out in outs]
        for name, value in case.actual.items():
            label = f" ({case.label})" if case.label else ""
            card.add(f"{case.event}: {name}{label}", [outputs[name] for outputs in samples], value)


def _evaluate_week(season, week, sims, seed, predictors):
    predictors = predictors or load_predictors("baseline")
    traced, calls = _traced(predictors)
    card, plays, failures = Scorecard(), 0, 0
    for i, sample in enumerate(real_samples(season, [week])):
        calls.clear()
        results, failed = simulate_play(sample.context, traced, sims, seed * 100 + week, i)
        plays, failures = plays + 1, failures + len(failed)
        _score_play(card, sample.context, sample.actual, results)
        _score_events(card, predictors, sample, _runs(calls), sims, random.Random(f"{seed} {week} {i}"))
    return card, plays, failures


def evaluate(season: int = 2026, weeks=None, sims: int = 100, seed: int = 0, predictors=None,
             workers: int | None = None) -> Evaluation:
    weeks = sorted(int(week) for week in (weeks or load("pbp", season).week.unique()))
    jobs = [[season] * len(weeks), weeks, [sims] * len(weeks), [seed] * len(weeks), [predictors] * len(weeks)]
    if workers == 1 or len(weeks) == 1:
        parts = list(map(_evaluate_week, *jobs))
    else:
        with ProcessPoolExecutor(workers) as pool:
            parts = list(pool.map(_evaluate_week, *jobs))
    card = Scorecard()
    for part, _, _ in parts:
        card.merge(part)
    return Evaluation(season, weeks, sims, sum(p for _, p, _ in parts), sum(f for _, _, f in parts), card)
