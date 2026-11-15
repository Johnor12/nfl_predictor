# START
# Scoring the play scenario and each of its event predictors against real plays.
# - evaluate(seasons=EVALUATED, weeks=None, games=None, sims=100, seed=0, predictors=None, workers=None) ->
#   Evaluation: every real play of the seasons' games (of `games` of them, sampled by evaluators.sample_games)
#   is simulated `sims` times and scored, a few games per process.
# - Evaluation: seasons, games, sims, plays, failures (simulated plays that raised or broke an invariant),
#   and card, a scoring.Scorecard with outputs named "play: yards (scrimmage)" or "carry: yards (run)".
# - play_outputs(ctx, outcome) -> {name: value}: the play scenario's scored outputs, read the same way from a
#   real outcome (RealPlay.actual) and a simulated one (simulators.play.summarize). The clock isn't one of
#   them: nflverse times a play from its snap to the next snap, the scenario from the previous play's end.
# Internals: _evaluate_games (some games' scorecard; a play's seed comes from its game and its place in it,
#   so it doesn't depend on which other games are evaluated), _score_play (the scenario: the simulated outcomes against
#   the real one), _score_events (each event case: `sims` samples of its predictor against the real output,
#   each sample with another simulated run standing in for the inputs the data doesn't record, so the forecast
#   is spread over what they might have been instead of pinned to one draw),
#   _traced / _runs (the predictors wrapped to record every call, split into one cases.Run per simulated run).
# END
import dataclasses
import random
import zlib
from dataclasses import dataclass

from evaluators import executor
from evaluators.sample import EVALUATED, sample_games
from evaluators.play.cases import Run, read, stand_ins
from evaluators.scoring import Scorecard
from scenarios.play import load_predictors
from shared.nflverse import real_samples
from simulators.play import simulate_play, summarize


@dataclass
class Evaluation:
    seasons: list
    games: int
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
    cases = stand_ins(sample, runs)  # each run leads once
    for k, case in enumerate(cases[0]):
        predict = getattr(predictors, case.event)
        if case.args is None:
            outs = []
        elif case.args:
            outs = [predict(ctx, *cases[i % len(cases)][k].args, rng) for i in range(sims)]
        else:  # the context is the predictor's only input, so the runs have already sampled it
            outs = [run.calls[case.event][0][1] for run in runs]
        samples = [read(ctx, case, out) for out in outs]
        for name, value in case.actual.items():
            label = f" ({case.label})" if case.label else ""
            card.add(f"{case.event}: {name}{label}", [outputs[name] for outputs in samples], value)


def _evaluate_games(season, games, sims, seed, predictors):
    predictors = predictors or load_predictors()
    traced, calls = _traced(predictors)
    card, plays, failures, index = Scorecard(), 0, 0, {}
    for sample in real_samples(season, games=games):
        game = sample.context.game.game_id
        i = index[game] = index.get(game, -1) + 1  # the play's place in its game
        calls.clear()
        results, failed = simulate_play(sample.context, traced, sims, zlib.crc32(f"{seed} {game}".encode()), i)
        plays, failures = plays + 1, failures + len(failed)
        _score_play(card, sample.context, sample.actual, results)
        _score_events(card, predictors, sample, _runs(calls), sims, random.Random(f"{seed} {game} {i}"))
    return card, plays, failures


def evaluate(seasons=EVALUATED, weeks=None, games=None, sims: int = 100, seed: int = 0, predictors=None,
             workers: int | None = None) -> Evaluation:
    sample = sample_games(seasons, weeks, games)
    chunks = [(season, ids[i:i + 8]) for season, ids in sample.items() for i in range(0, len(ids), 8)]
    with executor(1 if len(chunks) == 1 else workers) as pool:
        parts = list(pool.map(_evaluate_games, [season for season, _ in chunks], [ids for _, ids in chunks],
                              [sims] * len(chunks), [seed] * len(chunks), [predictors] * len(chunks)))
    card = Scorecard()
    for part, _, _ in parts:
        card.merge(part)
    return Evaluation(sorted(sample), sum(map(len, sample.values())), sims, sum(p for _, p, _ in parts),
                      sum(f for _, _, f in parts), card)
