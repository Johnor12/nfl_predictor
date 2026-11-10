# START
# Real play contexts from nflverse data: every real snap or free kick as a play scenario input.
# - real_plays(season, weeks=None) -> list[RealPlay]: in game order; each has the PlayContext, a dict of what
#   actually happened (actual), and the pbp row index (row).
# - real_samples(season, weeks=None) -> iterator of shared.priors.Sample: each real play with its nflverse
#   rows (the pbp row and the FTN charting row, or None), for code that reads what an event's output was.
# Pipeline: _Rosters (active players per team-week: weekly roster status ACT minus injury-report Outs, plus
#   anyone who appears in the game's pbp; depth chart slots from the last snapshot before gameday, draft
#   pick, season-to-date stats from earlier weeks),
#   _game (schedule row -> Game), _kind / _situation (pbp row -> Situation; clock state inferred from the
#   previous row by _clock_state), _actual (pbp row -> outcome dict), _summary (row -> PlaySummary history),
#   _seconds_to_next (real snap-to-snap game time, for clock audits).
# Conventions: nflverse lists the receiving team as posteam on kickoffs, so the kicking team is our offense
#   there; a try's x is the two-point spot even when the row is a kick (see scenarios/play/context.py).
# END
import bisect
from dataclasses import dataclass

import pandas as pd

from shared.nflverse.download import load
from scenarios.play import Game, PlayContext, PlaySummary, Player, Situation
from shared.priors import Sample
from shared.rulebook import rules_for

SNAPPED = {"run", "pass", "punt", "field_goal", "extra_point", "qb_kneel", "qb_spike"}
SEASON_STATS = [  # (stat, player id column, value column), summed over earlier weeks
    ("pass_att", "passer_player_id", "attempt"),
    ("pass_yds", "passer_player_id", "passing_yards"),
    ("pass_td", "passer_player_id", "pass_touchdown"),
    ("int_thrown", "passer_player_id", "interception"),
    ("rush_att", "rusher_player_id", "rush_attempt"),
    ("rush_yds", "rusher_player_id", "rushing_yards"),
    ("rush_td", "rusher_player_id", "rush_touchdown"),
    ("targets", "receiver_player_id", "attempt"),
    ("receptions", "receiver_player_id", "complete_pass"),
    ("rec_yds", "receiver_player_id", "receiving_yards"),
    ("rec_td", "receiver_player_id", "pass_touchdown"),
    ("sacks", "sack_player_id", "sack"),
    ("interceptions", "interception_player_id", "interception"),
    ("fg_made", "kicker_player_id", "fg_made"),
]


@dataclass(frozen=True)
class RealPlay:
    context: PlayContext
    actual: dict
    row: int


def _num(value, default=None):
    return default if value is None or pd.isna(value) else value


class _Rosters:
    def __init__(self, season, pbp):
        self.rosters = load("rosters", season)
        injuries = load("injuries", season)
        self.out = set(zip(injuries[injuries.report_status == "Out"].gsis_id,
                           injuries[injuries.report_status == "Out"].week))
        depth = load("depth_charts", season)
        depth = depth[depth.dt >= f"{season}-08-01"]
        self.depth = {key: frame for key, frame in depth.groupby(["team", "dt"])}
        self.snapshots = {team: sorted(dt for t, dt in self.depth if t == team) for team in depth.team.unique()}
        self.stats = self._season_stats(pbp)

    @staticmethod
    def _season_stats(pbp):
        plays = pbp[(pbp.play_type != "no_play") & (pbp.two_point_attempt != 1)].copy()
        plays["attempt"] = plays.complete_pass + plays.incomplete_pass + plays.interception
        plays["fg_made"] = (plays.field_goal_result == "made").astype(int)
        parts = [plays[[pid, "week", value]].dropna(subset=[pid]).set_axis(["player", "week", "value"], axis=1)
                 .assign(stat=stat) for stat, pid, value in SEASON_STATS]
        weekly = pd.concat(parts).groupby(["player", "week", "stat"]).value.sum().reset_index()
        by_week = {}
        for week in sorted(pbp.week.unique()):
            before = weekly[weekly.week < week].groupby(["player", "stat"]).value.sum()
            stats = {}
            for (player, stat), value in before.items():
                if value:
                    stats.setdefault(player, []).append((stat, float(value)))
            by_week[week] = {player: tuple(sorted(s)) for player, s in stats.items()}
        return by_week

    def _depth_slots(self, team, gameday):
        dates = self.snapshots.get(team, [])
        i = bisect.bisect_left(dates, gameday) - 1  # last snapshot before gameday
        if i < 0:
            return {}
        slots = {}
        for gsis, slot, rank in self.depth[(team, dates[i])][["gsis_id", "pos_abb", "pos_rank"]].itertuples(index=False):
            slots.setdefault(gsis, []).append((slot, int(rank)))
        return slots

    def players(self, team, week, gameday, appeared) -> tuple[Player, ...]:
        """Active players: roster status ACT minus injury-report Outs, plus anyone who appears in the game's pbp."""
        rows = self.rosters[(self.rosters.team == team) & (self.rosters.week == week)].drop_duplicates("gsis_id")
        slots = self._depth_slots(team, gameday)
        stats = self.stats.get(week, {})
        players = []
        for r in rows.itertuples(index=False):
            active = r.status == "ACT" and (r.gsis_id, week) not in self.out
            if pd.isna(r.gsis_id) or not (active or r.gsis_id in appeared):
                continue
            position = "FB" if r.depth_chart_position == "FB" else r.position
            jersey = int(r.jersey_number) if pd.notna(r.jersey_number) else None
            players.append(Player(r.gsis_id, r.full_name, team, position, jersey,
                                  tuple(slots.get(r.gsis_id, ())), int(r.years_exp),
                                  int(r.draft_number) if pd.notna(r.draft_number) else None,
                                  stats.get(r.gsis_id, ())))
        return tuple(players)


def _game(schedule, row) -> Game:
    return Game(row["game_id"], int(row["season"]), int(row["week"]), row["home_team"], row["away_team"],
                schedule.get("location") == "Neutral", _num(schedule.get("roof")), _num(schedule.get("surface")),
                _num(schedule.get("temp")), _num(schedule.get("wind")), _num(schedule.get("stadium")),
                _num(schedule.get("gametime")), _num(schedule.get("home_coach")), _num(schedule.get("away_coach")),
                _num(schedule.get("referee")))


def _is_play(row) -> bool:
    if pd.isna(row["posteam"]):
        return False
    return row["play_type"] in SNAPPED or row["play_type"] == "kickoff" or (
        row["play_type"] == "no_play" and row["penalty"] == 1)


def _kind(row, prev_safety) -> str:
    if row["play_type"] == "kickoff":
        return "safety_kick" if prev_safety else "kickoff"
    if prev_safety:
        return "safety_kick"  # punted safety kick
    return "try" if pd.isna(row["down"]) else "scrimmage"


def _late(quarter, seconds):
    return (quarter == 2 and seconds <= 120) or (quarter == 4 and seconds <= 300) or quarter >= 5


def _clock_state(row, prev, kind, rules):
    """(clock running at the snap, play clock), inferred from the previous row of the game."""
    if kind != "scrimmage" or prev is None or prev["qtr"] != row["qtr"]:
        return False, rules.admin_play_clock
    quarter, seconds = row["qtr"], row["quarter_seconds_remaining"]
    two_minute_warning = quarter in (2, 4) and prev["quarter_seconds_remaining"] > 120 >= seconds
    possession_change = prev["posteam"] != row["posteam"] or prev["play_type"] in ("kickoff", "punt")
    admin = (prev["timeout"] == 1 or prev["penalty"] == 1 or possession_change or two_minute_warning
             or pd.isna(prev["play_type"]) or "injur" in str(prev["desc"]).lower())
    stopped = (admin and not prev["penalty"] == 1
               or prev["play_type"] in ("field_goal", "extra_point", "qb_spike")
               or 1 in (prev["incomplete_pass"], prev["interception"], prev["fumble_lost"], prev["touchdown"])
               or (prev["out_of_bounds"] == 1 and _late(quarter, seconds)))
    return not stopped, rules.admin_play_clock if admin else rules.play_clock


def _situation(row, prev, kind, score, rules) -> Situation:
    home, away = row["home_team"], row["away_team"]
    if row["play_type"] == "kickoff":  # posteam is the receiving team
        offense, defense, x = row["defteam"], row["posteam"], float(row["yardline_100"])
    else:
        offense, defense, x = row["posteam"], row["defteam"], 100.0 - row["yardline_100"]
    kick_try = kind == "try" and (row["extra_point_attempt"] == 1 or str(row["desc"]).startswith("(Kick formation)"))
    if kick_try:  # x is the two-point spot; a kick try snapped inside the 13 can't be expressed exactly
        x = min(99.0, x + rules.pat_line - rules.two_point_line)
    running, play_clock = _clock_state(row, prev, kind, rules)
    scrimmage = kind == "scrimmage"
    return Situation(kind, offense, defense, x, int(row["down"]) if scrimmage else None,
                     float(row["ydstogo"]) if scrimmage else None, dict(score), int(row["qtr"]),
                     float(row["quarter_seconds_remaining"]), running, play_clock,
                     {home: int(row["home_timeouts_remaining"]), away: int(row["away_timeouts_remaining"])})


def _action(row) -> str:
    kind = row["play_type"]
    if kind == "pass":
        return "sack" if row["sack"] == 1 else "pass"
    if kind == "run":
        return "scramble" if row["qb_scramble"] == 1 else "run"
    return {"qb_kneel": "kneel", "qb_spike": "spike"}.get(kind, kind)


def _actual(row, s, score_after) -> dict:
    return {
        "action": _action(row),
        "desc": row["desc"],
        "yards": _num(row["yards_gained"], 0.0),
        "points": {team: score_after[team] - s.score[team] for team in s.score},
        "touchdown": row["touchdown"] == 1,
        "turnover": row["interception"] == 1 or row["fumble_lost"] == 1,
        "penalty": row["penalty"] == 1,
        "penalty_type": _num(row["penalty_type"]),
        "first_down": row["first_down"] == 1,
        "complete": row["complete_pass"] == 1,
        "field_goal_result": _num(row["field_goal_result"]),
        "extra_point_result": _num(row["extra_point_result"]),
        "kick_distance": _num(row["kick_distance"]),
        "touchback": row["touchback"] == 1,
        "return_yards": _num(row["return_yards"], 0.0),
    }


def _summary(row, s) -> PlaySummary:
    tags = [tag for tag, col in (("touchdown", "touchdown"), ("interception", "interception"),
                                 ("fumble lost", "fumble_lost"), ("penalty", "penalty"),
                                 ("first down", "first_down")) if row[col] == 1]
    return PlaySummary(s.offense, _action(row), float(_num(row["yards_gained"], 0.0)), ", ".join(tags))


def real_plays(season: int, weeks=None) -> list[RealPlay]:
    rules = rules_for(season)
    season_pbp = load("pbp", season)
    pbp = season_pbp if weeks is None else season_pbp[season_pbp.week.isin(list(weeks))]
    schedule = load("games", season).set_index("game_id")
    rosters = _Rosters(season, season_pbp)  # season-to-date stats need the earlier weeks too
    plays = []
    for game_id, rows in pbp.groupby("game_id", sort=False):
        rows = rows.sort_values("order_sequence")
        first = rows.iloc[0]
        sched = schedule.loc[game_id].to_dict() if game_id in schedule.index else {}
        game = _game(sched, first)
        gameday = str(first["game_date"])[:10]
        appeared = set(rows[[c for c in rows.columns if c.endswith("_player_id")]].stack())
        players = (rosters.players(game.home, game.week, gameday, appeared)
                   + rosters.players(game.away, game.week, gameday, appeared))
        home, away = game.home, game.away
        score = {home: 0, away: 0}
        history, prev, prev_safety = [], None, False
        for index, row in zip(rows.index, rows.to_dict("records")):
            after = {home: int(_num(row["total_home_score"], score[home])), away: int(_num(row["total_away_score"], score[away]))}
            if _is_play(row):
                kind = _kind(row, prev_safety)
                s = _situation(row, prev, kind, score, rules)
                plays.append(RealPlay(PlayContext(game, s, players, tuple(history)), _actual(row, s, after), index))
                history.append(_summary(row, s))
                prev_safety = row["safety"] == 1
            score, prev = after, row
        _seconds_to_next(plays[len(plays) - len(history):])
    return plays


def real_samples(season: int, weeks=None):
    pbp = load("pbp", season)
    ftn = load("ftn", season).set_index(["nflverse_game_id", "nflverse_play_id"])
    for play in real_plays(season, weeks):
        row = pbp.loc[play.row]
        key = (row.game_id, int(row.play_id))
        yield Sample(play.context, play.actual, row, ftn.loc[key] if key in ftn.index else None)


def _seconds_to_next(game_plays):
    """Real game time from each snap to the next one in the same quarter (None at the end of a quarter)."""
    for play, following in zip(game_plays, game_plays[1:] + [None]):
        s = play.context.situation
        same = following is not None and following.context.situation.quarter == s.quarter
        play.actual["seconds_to_next"] = s.clock - following.context.situation.clock if same else None
