# START
# Test support for the play scenario: synthetic inputs and cheap random ("chaos") predictors.
# - synthetic_roster(team) -> tuple[Player]: a 46-man active roster with jerseys and depth chart slots.
# - synthetic_context(rng, kind=None, **situation) -> PlayContext: a random legal situation (overridable).
# - chaos_predictors() -> Predictors: uniformly random legal choices, including rare branches (fumbles,
#   blocks, muffs, laterals excluded, every foul type), for fuzzing the invariants.
# - scripted(base, **outputs) -> Predictors: replace events with fixed outputs (a value, or a list consumed
#   in order), for hand-built rule tests.
# END
import dataclasses

from events.carry import CarryEnd
from events.defensive_formation import DefensiveFormation
from events.fouls import Foul
from events.free_kick import FreeKick
from events.injuries import Injury
from events.kick_attempt import KickAttempt
from events.kick_result import KickResult
from events.lineups import Lineup, Lineups
from events.loose_ball import Recovery
from events.offensive_formation import Formation
from events.pass_result import PassResult
from events.pass_rush import RESULTS as RUSH_RESULTS
from events.pass_rush import PassRush
from events.pre_snap import PreSnap
from events.punt_kick import PuntKick
from events.punt_result import PuntResult
from events.snap import Snap
from events.target import Target
from scenarios.play.chain import allowed_units
from scenarios.play.context import Game, PlayContext, Player, Situation
from scenarios.play.predictors import Predictors
from shared.rulebook import rules_for

ROSTER = [("QB", 2, 1), ("RB", 3, 20), ("WR", 5, 10), ("TE", 3, 80), ("OL", 8, 60), ("DL", 7, 90),
          ("LB", 6, 40), ("DB", 9, 21), ("K", 1, 3), ("P", 1, 5), ("LS", 1, 47)]


def synthetic_roster(team):
    players = []
    for position, count, jersey in ROSTER:
        for i in range(count):
            players.append(Player(f"{team}-{position}{i + 1}", f"{team} {position}{i + 1}", team, position,
                                  jersey + i, ((position, i + 1),)))
    return tuple(players)


def synthetic_context(rng, kind=None, **situation):
    kind = kind or rng.choices(["scrimmage", "try", "kickoff", "safety_kick"], [80, 8, 10, 2])[0]
    off, de = rng.sample(["HOME", "AWAY"], 2)
    x = {"try": 98.0, "kickoff": 35.0, "safety_kick": 20.0}.get(kind, float(rng.randint(1, 99)))
    down = rng.randint(1, 4) if kind == "scrimmage" else None
    distance = float(min(rng.randint(1, 20), 100 - x)) if kind == "scrimmage" else None
    s = Situation(kind, off, de, x, down, distance, {off: rng.randint(0, 40), de: rng.randint(0, 40)},
                  rng.randint(1, 5), float(rng.randint(0, 900)), rng.random() < 0.5, 40,
                  {off: rng.randint(0, 3), de: rng.randint(0, 3)})
    s = dataclasses.replace(s, **situation)
    game = Game("test", 2026, 1, "HOME", "AWAY")
    return PlayContext(game, s, synthetic_roster("HOME") + synthetic_roster("AWAY"))


def _team_players(ctx, lineups, team):
    return lineups.offense.players if team == ctx.situation.offense else lineups.defense.players


def chaos_predictors() -> Predictors:
    def lineups(ctx, rng):
        s = ctx.situation
        unit = rng.choice(allowed_units(ctx, rules_for(ctx.game.season)))
        roster = [p.id for p in ctx.roster(s.offense)]
        by_pos = {pos: [p.id for p in ctx.roster(s.offense) if p.position == pos] for pos in
                  ("QB", "OL", "K", "P", "LS")}
        if unit in ("offense", "victory"):
            core = [by_pos["QB"][0]] + by_pos["OL"][:5]
            if unit == "offense" and rng.random() < 0.3:
                core.append(by_pos["K"][0])  # occasionally a kicker on the field
        elif unit == "punt":
            core = by_pos["P"] + by_pos["LS"]
        elif unit == "field_goal":
            core = by_pos["K"] + by_pos["P"] + by_pos["LS"]
        else:
            core = by_pos["K"]
        rest = [pid for pid in roster if pid not in core
                and ctx.by_id[pid].position not in ("QB", "OL", "K", "P", "LS")]
        offense = tuple(core + rng.sample(rest, 11 - len(core)))
        defense = tuple(rng.sample([p.id for p in ctx.roster(s.defense)], 11))
        return Lineups(Lineup(unit, None, offense), Lineup("defense", None, defense))

    def offensive_formation(ctx, lineups, rng):
        players = list(lineups.offense.players)
        position = {pid: ctx.by_id[pid].position for pid in players}
        unit = lineups.offense.unit
        if unit in ("offense", "victory"):
            qb = next(p for p in players if position[p] == "QB")
            ol = [p for p in players if position[p] == "OL"]
            others = [p for p in players if p not in ol and p != qb]
            rng.shuffle(others)
            line = (others[0],) + tuple(ol) + (others[1],)
        else:
            qb = next(p for p in players if position[p] == "P")  # punter or holder
            others = [p for p in players if p != qb and position[p] != "K"]
            rng.shuffle(others)
            line = tuple(others[:7])
        backfield = tuple(p for p in players if p not in line)
        return Formation("chaos", line, backfield, qb, rng.random() < 0.4)

    def defensive_formation(ctx, lineups, formation, rng):
        return DefensiveFormation(rng.randint(4, 9), rng.randint(0, 2))

    def pre_snap(ctx, lineups, formation, allowed, rng):
        foul = None
        if rng.random() < 0.1:
            name, team, timing = rng.choice(sorted(allowed))
            foul = Foul(name, team, rng.choice(_team_players(ctx, lineups, team)), ctx.situation.x, timing)
        return PreSnap(rng.uniform(0, 40), foul)

    def snap(ctx, lineups, formation, defense, allowed, rng):
        return Snap(rng.choice(allowed), rng.choice(formation.backfield), rng.random() < 0.02)

    def pass_rush(ctx, lineups, formation, defense, rng):
        rushers = list(lineups.defense.players)
        sackers = tuple(rng.sample(rushers, rng.choice([1, 1, 2])))
        return PassRush(rng.randint(3, 7), rng.choice(RUSH_RESULTS), rng.uniform(1, 6),
                        tuple(rng.sample(rushers, rng.randint(0, 2))), sackers, rng.uniform(0, 15))

    def target(ctx, lineups, formation, eligible, rng):
        return Target(rng.choice(eligible), rng.uniform(-5, 60), rng.choice(["left", "middle", "right"]))

    def pass_result(ctx, lineups, target, rng):
        result = rng.choice(["complete", "incomplete", "intercepted"])
        defenders = lineups.defense.players + (() if result == "intercepted" else (None,))
        return PassResult(result, rng.choice(defenders))

    def carry(ctx, lineups, kind, carrier, yard_line, rng):
        team = ctx.by_id[carrier].team
        s = ctx.situation
        opponents = _team_players(ctx, lineups, s.defense if team == s.offense else s.offense)
        how = rng.choice(["tackled", "tackled", "out_of_bounds", "fumble", "down"])
        yards = rng.choice([rng.uniform(-10, 15), rng.uniform(-110, 110)])
        forced = rng.choice(opponents + (None,)) if how == "fumble" else None
        return CarryEnd(yards, how, tuple(rng.sample(opponents, rng.randint(0, 2))), forced, rng.uniform(0, 10))

    def loose_ball(ctx, lineups, cause, x, last_team, rng):
        s = ctx.situation
        team = rng.choice([s.offense, s.defense, None])
        player = rng.choice(_team_players(ctx, lineups, team)) if team else None
        return Recovery(team, player, x + rng.uniform(-15, 15), rng.uniform(0, 3))

    def punt_kick(ctx, lineups, punter, rng):
        blocked = rng.choice(lineups.defense.players) if rng.random() < 0.05 else None
        return PuntKick(rng.uniform(10, 75), blocked, rng.uniform(3, 6))

    def after_kick(output):  # punt_result and kick_result
        def predict(ctx, lineups, landing_x, allowed, rng):
            result = rng.choice(allowed)
            team_players = lineups.offense.players if result == "kicking_recovery" else lineups.defense.players
            return output(result, rng.choice(team_players))
        return predict

    def kick_attempt(ctx, lineups, kicker, distance, rng):
        result = rng.choice(["good", "no_good", "blocked"])
        return KickAttempt(result, rng.choice(lineups.defense.players) if result == "blocked" else None, 3.0)

    def free_kick(ctx, lineups, onside, rng):
        return FreeKick(rng.choice(lineups.offense.players), rng.uniform(5, 80), rng.random() < 0.05, 4.0)

    def fouls(ctx, lineups, record, allowed, rng):
        out = []
        for _ in range(rng.choice([0, 0, 0, 1, 1, 2])):
            name, team, timing = rng.choice(sorted(allowed))
            out.append(Foul(name, team, rng.choice(_team_players(ctx, lineups, team)), rng.uniform(-10, 110), timing))
        return tuple(out)

    def injuries(ctx, lineups, record, rng):
        if rng.random() < 0.05:
            return (Injury(rng.choice(lineups.offense.players + lineups.defense.players), rng.choice([1, 5, 999])),)
        return ()

    return Predictors(lineups, offensive_formation, defensive_formation, pre_snap, snap, pass_rush, target,
                      pass_result, carry, loose_ball, punt_kick, after_kick(PuntResult), kick_attempt, free_kick,
                      after_kick(KickResult), fouls, injuries)


def scripted(base: Predictors, **outputs) -> Predictors:
    """Replace events with fixed outputs: a value is returned every time; a list is consumed in order."""
    def fixed(value):
        queue = list(value) if isinstance(value, list) else None
        return lambda *args: queue.pop(0) if queue is not None else value
    return dataclasses.replace(base, **{name: fixed(value) for name, value in outputs.items()})
