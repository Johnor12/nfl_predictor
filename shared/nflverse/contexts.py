# START
# Real play contexts from nflverse data: every real snap or free kick as a play scenario input.
# - real_plays(season, weeks=None, games=None) -> list[RealPlay]: in game order; each has the PlayContext, a
#   dict of what actually happened (actual), and the pbp row index (row). weeks and games (game ids) each
#   narrow it down.
# - real_samples(season, weeks=None, games=None) -> iterator of shared.priors.Sample: each real play with its
#   nflverse rows (the pbp row, the FTN charting row or None, and the participation row or None), for code
#   that reads what an event's output was. A row is a plain object with the columns as attributes (_rows).
# Pipeline: _Rosters (active players per team-week: weekly roster status ACT minus injury-report Outs, plus
#   anyone who appears in the game's pbp; depth chart slots from the last snapshot before gameday, draft
#   pick, season-to-date stats from earlier weeks, career stats from earlier seasons, and recent snaps by
#   unit; the tallies themselves are form.py's), _players (both teams' for a game),
#   _game (schedule row -> Game, with the form of its teams, coaches, and referee, and the weather: _weather
#   fills what the schedule lacks from the play-by-play's report), _kind / _situation (pbp row -> Situation;
#   clock state inferred from the previous row by _clock_state), _actual (pbp row -> outcome dict), _summary
#   (row -> PlaySummary history),
#   _seconds_to_next (real snap-to-snap game time: actual["seconds_to_next"] for clock audits, and
#   actual["seconds_since_snap"], the same gap on the play that follows, for the pre-snap priors).
# Timeouts: actual["timeout"] is the team that called one before the play (None if nobody did; a lost
#   challenge on the previous play counts), and actual["timeout_clock_running"] whether the clock would have
#   been running at the snap without it. The context itself is the state after the timeout.
# Disqualification: a context's `warned` is the players already flagged for unsportsmanlike conduct in the game.
# Conventions: nflverse lists the receiving team as posteam on kickoffs, so the kicking team is our offense
#   there; a try's x is the two-point spot even when the row is a kick (see scenarios/play/context.py).
# END
import bisect
import dataclasses
import re
from dataclasses import dataclass
from types import SimpleNamespace

import pandas as pd

from shared.nflverse.depth import depth_charts
from shared.nflverse.download import load
from shared.nflverse.form import Forms, weekly_snaps, weekly_stats
from scenarios.play import Game, PlayContext, PlaySummary, Player, Situation
from shared.priors import Sample
from shared.rulebook import rules_for

SNAPPED = {"run", "pass", "punt", "field_goal", "extra_point", "qb_kneel", "qb_spike"}
SNAP_WEEKS = 4  # a player's snaps cover his team's games in this many weeks before the game
GROUPS = {  # the detailed roster positions of the seasons before 2016 -> the play scenario's
    "T": "OL", "G": "OL", "C": "OL", "DE": "DL", "DT": "DL", "NT": "DL", "OLB": "LB", "ILB": "LB", "MLB": "LB",
    "CB": "DB", "SS": "DB", "FS": "DB", "S": "DB", "KR": "WR", "PR": "WR",
}
UNSPORTSMANLIKE = ("Unsportsmanlike Conduct", "Taunting")
WEATHER = (re.compile(r"Temp: (-?\d+)"), re.compile(r"Wind:[^,]*?(\d+)"))  # in a play-by-play weather report


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
        depth = depth_charts(season)
        self.depth = {key: frame for key, frame in depth.groupby(["team", "dt"])}
        self.snapshots = {team: sorted(dt for t, dt in self.depth if t == team) for team in depth.team.unique()}
        snaps = weekly_snaps(season, pbp, self.rosters)
        self.stats = self._season_stats(pbp, snaps)
        self.snaps = self._recent_snaps(snaps, pbp)
        self.forms = Forms(season, pbp)

    @staticmethod
    def _recent_snaps(weekly, pbp):
        weekly = weekly.rename("snaps").reset_index()
        by_week = {}
        for week in [*sorted(pbp.week.unique()), pbp.week.max() + 1]:  # the last is for games not yet played
            recent = weekly[(weekly.week < week) & (weekly.week >= week - SNAP_WEEKS)]
            snaps = {}
            for (player, unit), value in recent.groupby(["player", "unit"]).snaps.sum().items():
                snaps.setdefault(player, []).append((unit, float(value)))
            by_week[week] = {player: tuple(sorted(s)) for player, s in snaps.items()}
        return by_week

    @staticmethod
    def _season_stats(pbp, snaps):
        weekly = weekly_stats(pbp, snaps)
        by_week = {}
        for week in [*sorted(pbp.week.unique()), pbp.week.max() + 1]:  # the last is for games not yet played
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
        """Active players: roster status ACT minus injury-report Outs, plus anyone who appears in the game's pbp.
        A week without a roster yet (a game not played) uses the team's latest one."""
        team_rows = self.rosters[(self.rosters.team == team) & (self.rosters.week <= week)]
        rows = team_rows[team_rows.week == team_rows.week.max()].drop_duplicates("gsis_id")
        slots = self._depth_slots(team, gameday)
        stats = self.stats.get(min(week, max(self.stats)), {})
        snaps = self.snaps.get(min(week, max(self.snaps)), {})
        players = []
        for r in rows.itertuples(index=False):
            active = r.status == "ACT" and (r.gsis_id, week) not in self.out
            if pd.isna(r.gsis_id) or not (active or r.gsis_id in appeared):
                continue
            position = "FB" if r.depth_chart_position == "FB" else GROUPS.get(r.position, r.position)
            jersey = int(r.jersey_number) if pd.notna(r.jersey_number) else None
            players.append(Player(r.gsis_id, r.full_name, team, position, jersey,
                                  tuple(slots.get(r.gsis_id, ())), int(r.years_exp) if pd.notna(r.years_exp) else None,
                                  int(r.draft_number) if pd.notna(r.draft_number) else None,
                                  stats.get(r.gsis_id, ()), self.forms.career(r.gsis_id),
                                  snaps.get(r.gsis_id, ())))
        punters = [p for p in players if p.position == "P"]
        if len(punters) > 1 and not any(p.position == "K" for p in players):
            # the roster lists the kicker as a punter (the 2022 Chargers): he is the depth chart's kicker
            kicker = min(punters, key=lambda p: p.rank("PK") or 99)
            players[players.index(kicker)] = dataclasses.replace(kicker, position="K")
        return tuple(players)


def _weather(schedule, report) -> list:
    """[temperature, wind]: the schedule's, and for an outdoor game it has none for, the play-by-play's
    weather report ("Sunny Temp: 73° F, Humidity: 79%, Wind: W 3 mph"). Indoors there is none."""
    weather = [_num(schedule.get("temp")), _num(schedule.get("wind"))]
    if schedule.get("roof") in ("outdoors", "open") and isinstance(report, str):
        for i, pattern in enumerate(WEATHER):
            found = pattern.search(report)
            if weather[i] is None and found:
                weather[i] = float(found.group(1))
    return weather


def _game(schedule, row, forms, report=None) -> Game:
    """row names the game (a pbp row, or the schedule row itself); schedule is its schedule row, or {};
    forms is the season's Forms; report is the play-by-play's weather report, if the game has been played."""
    home, away = row["home_team"], row["away_team"]
    coaches = _num(schedule.get("home_coach")), _num(schedule.get("away_coach"))
    referee = _num(schedule.get("referee"))
    return Game(row["game_id"], int(row["season"]), int(row["week"]), home, away,
                schedule.get("location") == "Neutral", _num(schedule.get("roof")), _num(schedule.get("surface")),
                *_weather(schedule, report), _num(schedule.get("stadium")),
                _num(schedule.get("gametime")), *coaches, referee, schedule.get("game_type", "REG") != "REG",
                _num(schedule.get("spread_line")), _num(schedule.get("total_line")),
                forms.game(row["game_id"], home, away, *coaches, referee))


def _players(rosters, game, gameday, rows) -> tuple[Player, ...]:
    """Both teams' active players; rows are the game's pbp rows (None if it hasn't been played)."""
    appeared = set() if rows is None else set(rows[[c for c in rows.columns if c.endswith("_player_id")]].stack())
    return (rosters.players(game.home, game.week, gameday, appeared)
            + rosters.players(game.away, game.week, gameday, appeared))


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


def real_plays(season: int, weeks=None, games=None) -> list[RealPlay]:
    rules = rules_for(season)
    season_pbp = load("pbp", season)
    pbp = season_pbp if weeks is None else season_pbp[season_pbp.week.isin(list(weeks))]
    pbp = pbp if games is None else pbp[pbp.game_id.isin(list(games))]
    schedule = load("games", season).set_index("game_id")
    rosters = _Rosters(season, season_pbp)  # season-to-date stats need the earlier weeks too
    plays = []
    for game_id, rows in pbp.groupby("game_id", sort=False):
        rows = rows.sort_values("order_sequence")
        first = rows.iloc[0]
        sched = schedule.loc[game_id].to_dict() if game_id in schedule.index else {}
        game = _game(sched, first, rosters.forms, first["weather"])
        players = _players(rosters, game, str(first["game_date"])[:10], rows)
        home, away = game.home, game.away
        score = {home: 0, away: 0}
        history, prev, prev_safety, warned = [], None, False, frozenset()
        timeout, before = None, None  # the first timeout since the last play, and the row before it
        for index, row in zip(rows.index, rows.to_dict("records")):
            after = {home: int(_num(row["total_home_score"], score[home])), away: int(_num(row["total_away_score"], score[away]))}
            if _is_play(row):
                kind = _kind(row, prev_safety)
                s = _situation(row, prev, kind, score, rules)
                actual = _actual(row, s, after)
                actual["timeout"] = timeout
                actual["timeout_clock_running"] = _clock_state(row, before, kind, rules)[0] if timeout else None
                plays.append(RealPlay(PlayContext(game, s, players, tuple(history), warned), actual, index))
                history.append(_summary(row, s))
                if row["penalty_type"] in UNSPORTSMANLIKE and _num(row["penalty_player_id"]):
                    warned |= {row["penalty_player_id"]}
                prev_safety = row["safety"] == 1
                timeout = None
            if row["timeout"] == 1 and timeout is None:  # on a play's own row: a lost challenge, charged after it
                timeout, before = _num(row["timeout_team"]), row if _is_play(row) else prev
            score, prev = after, row
        _seconds_to_next(plays[len(plays) - len(history):])
    return plays


def real_samples(season: int, weeks=None, games=None):
    pbp = load("pbp", season)
    ftn = load("ftn", season)
    if ftn is not None:
        ftn = ftn.set_index(["nflverse_game_id", "nflverse_play_id"])
    participation = load("participation", season)
    if participation is not None:
        participation = participation.drop_duplicates(["nflverse_game_id", "play_id"]).set_index(["nflverse_game_id", "play_id"])
    row, charting, on_field = _rows(pbp), _rows(ftn), _rows(participation)
    for play in real_plays(season, weeks, games):
        play_row = row(play.row)
        key = (play_row.game_id, int(play_row.play_id))
        yield Sample(play.context, play.actual, play_row, charting(key), on_field(key))


def _rows(frame):
    """A reader of the frame's rows: label -> the row as a plain object with the columns as attributes, or
    None if there is no such row (or no frame). A pandas Series reads the same way, 200 times slower."""
    if frame is None:
        return lambda label: None
    names = frame.columns.tolist()
    return lambda label: SimpleNamespace(**dict(zip(names, frame.loc[label].to_numpy()))) if label in frame.index else None


def _seconds_to_next(game_plays):
    """Real game time from each snap to the next one in the same quarter (None at the end of a quarter), on
    both plays: seconds_to_next on the first, seconds_since_snap on the second."""
    since = None
    for play, following in zip(game_plays, game_plays[1:] + [None]):
        s = play.context.situation
        same = following is not None and following.context.situation.quarter == s.quarter
        play.actual["seconds_since_snap"] = since
        play.actual["seconds_to_next"] = since = s.clock - following.context.situation.clock if same else None
