# START
# The audit report: reasonableness metrics (real vs simulated) and a markdown write-up.
# - METRICS: Metric definitions (section, label, filter, value, kind) over (context, outcome) pairs.
# - metrics(audit) -> list[dict]: each metric's real and simulated value, sample sizes, and a flag when they
#   differ by more than the tolerance (rates: 3 points or 15%; means: 1.0 or 20%; both need n >= 30).
# - write_report(audit, path=None) -> Path: summary, input problems, invariant failures, metrics table, examples.
# END
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from scenarios.play import describe_play, describe_situation

OUT = Path(__file__).resolve().parent.parent / "audit_output"
DROPBACK = {"pass", "sack", "scramble"}
RUN = {"run", "kneel"}


@dataclass(frozen=True)
class Metric:
    section: str
    label: str
    filter: Callable
    value: Callable
    kind: str  # rate or mean


def _scrimmage(c, o):
    return c.situation.kind == "scrimmage" and o["action"] != "no_play"


def _down(d):
    return lambda c, o: _scrimmage(c, o) and c.situation.down == d


def _fourth(low, high):
    return lambda c, o: _down(4)(c, o) and low <= c.situation.x < high


def _action(*actions):
    return lambda c, o: o["action"] in actions


def _fg(low, high):
    return lambda c, o: o["action"] == "field_goal" and o["kick_distance"] is not None and low <= o["kick_distance"] < high


def _play_calling(d):
    return [
        Metric("play calling", f"down {d}: dropback rate", _down(d), lambda c, o: o["action"] in DROPBACK | {"spike"}, "rate"),
        Metric("play calling", f"down {d}: punt rate", _down(d), lambda c, o: o["action"] == "punt", "rate"),
        Metric("play calling", f"down {d}: field goal rate", _down(d), lambda c, o: o["action"] == "field_goal", "rate"),
    ]


METRICS = [
    *_play_calling(1), *_play_calling(2), *_play_calling(3), *_play_calling(4),
    Metric("4th down", "own half: go for it", _fourth(0, 50), lambda c, o: o["action"] in DROPBACK | RUN, "rate"),
    Metric("4th down", "opp 50-31: go for it", _fourth(50, 70), lambda c, o: o["action"] in DROPBACK | RUN, "rate"),
    Metric("4th down", "opp 50-31: field goal", _fourth(50, 70), lambda c, o: o["action"] == "field_goal", "rate"),
    Metric("4th down", "opp 30-0: field goal", _fourth(70, 100), lambda c, o: o["action"] == "field_goal", "rate"),
    Metric("tries", "two-point attempt rate", lambda c, o: c.situation.kind == "try" and o["action"] != "no_play",
           lambda c, o: o["action"] != "extra_point", "rate"),
    Metric("tries", "extra point good", _action("extra_point"), lambda c, o: o["extra_point_result"] == "good", "rate"),
    Metric("outcomes", "run: mean yards", _action("run"), lambda c, o: o["yards"], "mean"),
    Metric("outcomes", "run: 10+ yard rate", _action("run"), lambda c, o: o["yards"] >= 10, "rate"),
    Metric("outcomes", "dropback: sack rate", _action(*DROPBACK), lambda c, o: o["action"] == "sack", "rate"),
    Metric("outcomes", "dropback: scramble rate", _action(*DROPBACK), lambda c, o: o["action"] == "scramble", "rate"),
    Metric("outcomes", "pass: completion rate", _action("pass"), lambda c, o: o["complete"], "rate"),
    Metric("outcomes", "dropback: mean yards", _action(*DROPBACK), lambda c, o: o["yards"], "mean"),
    Metric("outcomes", "dropback: 20+ yard rate", _action(*DROPBACK), lambda c, o: o["yards"] >= 20, "rate"),
    Metric("outcomes", "turnover rate (runs and dropbacks)", _action(*DROPBACK, "run"), lambda c, o: o["turnover"], "rate"),
    Metric("outcomes", "touchdown rate (scrimmage plays)", _scrimmage, lambda c, o: o["touchdown"], "rate"),
    Metric("outcomes", "touchdown rate inside the 10", lambda c, o: _scrimmage(c, o) and c.situation.x >= 90,
           lambda c, o: o["touchdown"], "rate"),
    Metric("outcomes", "3rd down conversion rate", _down(3), lambda c, o: o["first_down"], "rate"),
    Metric("outcomes", "penalty flag rate (snaps)", lambda c, o: c.situation.kind in ("scrimmage", "try"),
           lambda c, o: o["penalty"], "rate"),
    Metric("outcomes", "no-play rate (snaps)", lambda c, o: c.situation.kind in ("scrimmage", "try"),
           lambda c, o: o["action"] == "no_play", "rate"),
    Metric("kicking", "field goal good: under 40", _fg(0, 40), lambda c, o: o["field_goal_result"] == "made", "rate"),
    Metric("kicking", "field goal good: 40-49", _fg(40, 50), lambda c, o: o["field_goal_result"] == "made", "rate"),
    Metric("kicking", "field goal good: 50+", _fg(50, 99), lambda c, o: o["field_goal_result"] == "made", "rate"),
    Metric("kicking", "punt: mean gross yards", lambda c, o: o["action"] == "punt" and o["kick_distance"] is not None,
           lambda c, o: o["kick_distance"], "mean"),
    Metric("kicking", "punt: touchback rate", _action("punt"), lambda c, o: o["touchback"], "rate"),
    Metric("kicking", "kickoff: touchback rate", _action("kickoff"), lambda c, o: o["touchback"], "rate"),
    Metric("kicking", "kickoff: mean return yards (returns)", lambda c, o: o["action"] == "kickoff" and o["return_yards"],
           lambda c, o: o["return_yards"], "mean"),
    Metric("scoring", "points per scrimmage play, offense", _scrimmage,
           lambda c, o: o["points"][c.situation.offense], "mean"),
    Metric("scoring", "points per scrimmage play, defense", _scrimmage,
           lambda c, o: o["points"][c.situation.defense], "mean"),
    Metric("clock", "game seconds per scrimmage snap", lambda c, o: c.situation.kind == "scrimmage",
           lambda c, o: o.get("seconds_to_next", o.get("seconds")), "mean"),
]


def _evaluate(pairs, metric):
    values = [metric.value(c, o) for c, o in pairs if metric.filter(c, o)]
    values = [float(v) for v in values if v is not None]
    return (sum(values) / len(values) if values else None), len(values)


def metrics(audit) -> list[dict]:
    rows = []
    for m in METRICS:
        real, n_real = _evaluate(audit.actual, m)
        sim, n_sim = _evaluate(audit.simulated, m)
        flag = False
        if real is not None and sim is not None and min(n_real, n_sim) >= 30:
            tolerance = max(0.03, 0.15 * abs(real)) if m.kind == "rate" else max(1.0, 0.2 * abs(real))
            flag = abs(sim - real) > tolerance
        rows.append(dict(section=m.section, label=m.label, kind=m.kind, real=real, sim=sim,
                         n_real=n_real, n_sim=n_sim, flag=flag))
    return rows


def _fmt(value, kind):
    if value is None:
        return "-"
    return f"{100 * value:.1f}%" if kind == "rate" else f"{value:.2f}"


def write_report(audit, path=None) -> Path:
    path = Path(path) if path else OUT / f"report_{audit.season}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    kinds = {}
    for rp in audit.plays:
        kinds[rp.context.situation.kind] = kinds.get(rp.context.situation.kind, 0) + 1
    exceptions = [f for f in audit.failures if "Traceback" in f[2]]
    rows = metrics(audit)
    lines = [f"# Play scenario audit, {audit.season}", "",
             f"- real plays (inputs): {len(audit.plays)} ({', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))})",
             f"- inputs with problems: {len({id(rp) for rp, _ in audit.input_errors})}",
             f"- simulated plays: {len(audit.simulated)}",
             f"- simulated plays breaking an invariant: {len(audit.failures) - len(exceptions)}",
             f"- simulations that raised an error: {len(exceptions)}",
             f"- reasonableness metrics outside tolerance: {sum(r['flag'] for r in rows)} of {len(rows)}", ""]
    if audit.input_errors:
        lines += ["## Input problems", ""]
        lines += [f"- {rp.context.game.game_id} {describe_situation(rp.context.situation)}: {e}"
                  for rp, e in audit.input_errors[:50]] + [""]
    if audit.failures:
        lines += ["## Failures (first 20)", ""]
        for rp, message, detail in audit.failures[:20]:
            lines += [f"### {rp.context.game.game_id}: {message}", "", "```", detail.strip(), "```",
                      f"real: {rp.actual['desc']}", ""]
    lines += ["## Reasonableness: real vs simulated", "",
              "| section | metric | real | simulated | n real | n sim | |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['section']} | {r['label']} | {_fmt(r['real'], r['kind'])} | {_fmt(r['sim'], r['kind'])} "
                     f"| {r['n_real']} | {r['n_sim']} | {'**check**' if r['flag'] else ''} |")
    lines += ["", "## Example plays", ""]
    for rp, result in audit.examples:
        lines += ["```", describe_play(result), "```", f"real: {rp.actual['desc']}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
