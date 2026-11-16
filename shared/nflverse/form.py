# START
# Form: what teams, head coaches, referees, and players did before a game, from the play-by-play. These are
# the inputs that say who is playing.
# - Forms(season, pbp): one season's.
#   .game(game_id, home, away, home_coach, away_coach, referee) -> ((who, Form), ...): `Game.forms`. Each one's
#     totals in this season's earlier games and in earlier seasons (a season counting DECAY times the one
#     after it). A game that hasn't been played gets everything the season has so far.
#   .career(player) -> ((stat, total), ...): `Player.career_stats`, a player's weekly_stats over earlier
#     seasons, discounted the same way.
# - TEAM_STATS: the stats of a team's offense, counted play by play (_counted): its plays (runs and dropbacks
#   on scrimmage downs) and what came of them, its snaps with the flags on it and on the defense, and its
#   fourth downs. A team's form holds
#   them under these names, and what its defense allowed under "allowed_<stat>" (the same stats of its
#   opponents' offenses), plus `games`, `points`, and `allowed_points`. A coach's form is his teams'; a
#   referee's is both offenses' stats in his games.
# - weekly_stats(season, pbp, weekly_snaps) -> DataFrame, a row per (player, week) and a column per stat:
#   everything recorded about a player, by week. Four sources, so a lineman or a defender has a history as a
#   passer or a receiver does:
#   - USAGE: counted from the play-by-play: how he was used (carries, dropbacks, scrambles, air yards) and the
#     passing, rushing, receiving, and punting stats the predictors read.
#   - every other stat of his stat lines (shared.nflverse.stat_lines): the rest of the box score (tackles,
#     sacks, penalties, returns, kicks) and, from 2018 on, what was charted (pressures, coverage, drops).
#   - his snaps: offense_snaps, defense_snaps, special_teams_snaps.
#   - ON_FIELD, where the season has a participation file: what his team's offense did on the plays he was on
#     the field for it (on_<stat>), and what the other offense did on the plays he was on the field against
#     it (on_allowed_<stat>). The stats are a team's (TEAM_STATS), so what happened without him is his team's
#     form less his own; `pressures` (the dropbacks the passer was pressured on) is only here.
# - Totals(weekly_stats): .before(player, week) -> ((stat, total), ...): `Player.season_stats`.
# - weekly_snaps(season, pbp, rosters) -> Series by (player, week, unit): snaps, from who was on the field
#   where the season has a participation file, else from the per-game snap counts, else empty.
# Earlier seasons are read once and kept in .cache/form/<season>.parquet (who, stat, value): delete it after
# refreshing a past season's files.
# Internals: _on_the_field (each counted play with who was on the field), _usage, _snap_totals, _on_field (the
#   parts of weekly_stats), _counted (each play as its offense's stats), _team_games (a row per team and
#   game), _subjects (the season's rows per team, coach, and referee), _totals (a season's totals per team, coach, referee, and
#   player; cached on disk), _earlier (those of every earlier season, discounted and summed).
# END
import bisect
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

from scenarios.play import Form
from shared.nflverse.download import SEASONS, load
from shared.nflverse.stat_lines import stat_lines

CACHE = Path(__file__).resolve().parents[2] / ".cache" / "form"
DECAY = 0.5  # an earlier season counts this much of the one after it (as the priors do)
UNITS = {  # play type -> (the unit of the team nflverse lists in possession, the other team's)
    "run": ("offense", "defense"), "pass": ("offense", "defense"), "qb_kneel": ("offense", "defense"),
    "qb_spike": ("offense", "defense"), "punt": ("punt", "punt_return"),
    "field_goal": ("field_goal", "field_goal_block"), "extra_point": ("field_goal", "field_goal_block"),
    "kickoff": ("kick_return", "kickoff"),
}
SNAP_COUNTS = {"offense_snaps": "offense", "defense_snaps": "defense", "st_snaps": "special_teams"}
USAGE = [  # (stat, player id column, value column), counted from the play-by-play
    ("pass_att", "passer_player_id", "attempt"),
    ("pass_cmp", "passer_player_id", "complete_pass"),
    ("pass_yds", "passer_player_id", "passing_yards"),
    ("pass_td", "passer_player_id", "pass_touchdown"),
    ("int_thrown", "passer_player_id", "interception"),
    ("rush_att", "rusher_player_id", "rush_attempt"),
    ("rush_yds", "rusher_player_id", "rushing_yards"),
    ("rush_td", "rusher_player_id", "rush_touchdown"),
    ("carries", "rusher_player_id", "carry"),          # designed runs: rush_att without scrambles and kneels
    ("scrambles", "rusher_player_id", "qb_scramble"),
    ("dropbacks", "passer_player_id", "qb_dropback"),  # passes and sacks...
    ("dropbacks", "rusher_player_id", "qb_scramble"),  # ...and scrambles
    ("times_sacked", "passer_player_id", "sack"),
    ("targets", "receiver_player_id", "attempt"),
    ("receptions", "receiver_player_id", "complete_pass"),
    ("rec_yds", "receiver_player_id", "receiving_yards"),
    ("rec_td", "receiver_player_id", "pass_touchdown"),
    ("target_air_yds", "receiver_player_id", "air_yards"),      # how deep he is thrown to
    ("rec_yac", "receiver_player_id", "yards_after_catch"),
    ("punts", "punter_player_id", "punt"),             # the ones that got away
    ("punt_yds", "punter_player_id", "punt_yards"),
]
USAGE_STATS = {stat for stat, _, _ in USAGE}
TEAM_STATS = ("plays", "dropbacks", "runs", "shotgun", "pass_att", "pass_cmp", "pass_yds", "air_yds", "int_thrown",
              "sacked", "scrambles", "rush_yds", "dropback_yds", "first_downs", "touchdowns", "fumbles_lost", "snaps",
              "flags", "defense_flags", "fourth_downs", "fourth_down_goes")
ON_FIELD = ("plays", "dropbacks", "runs", "pass_att", "pass_cmp", "pass_yds", "int_thrown", "sacked", "scrambles",
            "rush_yds", "dropback_yds", "first_downs", "touchdowns", "fumbles_lost", "pressures")


def _plain(name) -> str:
    return "".join(c for c in str(name).lower() if c.isalpha()).removesuffix("jr").removesuffix("sr").rstrip("iv")


def weekly_snaps(season, pbp, rosters) -> pd.Series:
    participation = load("participation", season)
    if participation is not None:
        plays = pbp[pbp.play_type.isin(list(UNITS))][["game_id", "play_id", "week", "play_type"]].merge(
            participation, left_on=["game_id", "play_id"], right_on=["nflverse_game_id", "play_id"])
        sides = [plays.assign(player=plays[column].str.split(";"), unit=plays.play_type.map(lambda kind: UNITS[kind][i]))
                 for i, column in enumerate(("offense_players", "defense_players"))]
        on_field = pd.concat(sides)[["player", "week", "unit"]].explode("player")
        return on_field[on_field.player.str.len() > 0].groupby(["player", "week", "unit"]).size()
    counts = load("snap_counts", season)
    if counts is None or counts.empty:  # before 2013: nobody has snaps
        return pd.Series(dtype=float, index=pd.MultiIndex.from_arrays([[], [], []], names=["player", "week", "unit"]))
    known = rosters.dropna(subset=["gsis_id"])
    by_pfr = known.dropna(subset=["pfr_id"]).drop_duplicates("pfr_id").set_index("pfr_id").gsis_id
    by_name = dict(zip(zip(known.team, known.full_name.map(_plain)), known.gsis_id))
    named = [by_name.get(key) for key in zip(counts.team, counts.player.map(_plain))]
    counts = counts.assign(player=counts.pfr_player_id.map(by_pfr).fillna(pd.Series(named, index=counts.index)))
    snaps = counts.dropna(subset=["player"]).melt(["player", "week"], list(SNAP_COUNTS), "unit", "snaps")
    return snaps[snaps.snaps > 0].assign(unit=snaps.unit.map(SNAP_COUNTS)).groupby(["player", "week", "unit"]).snaps.sum()


def _usage(pbp) -> pd.DataFrame:
    plays = pbp[(pbp.play_type != "no_play") & (pbp.two_point_attempt != 1)].copy()
    plays["attempt"] = plays.complete_pass + plays.incomplete_pass + plays.interception
    plays["carry"] = ((plays.play_type == "run") & (plays.qb_scramble != 1)).astype(int)
    plays["punt"] = ((plays.play_type == "punt") & (plays.punt_blocked != 1)).astype(int)
    plays["punt_yards"] = plays.kick_distance.where(plays.punt == 1)
    usage = {}
    for stat, pid, value in USAGE:
        counted = plays.groupby([pid, "week"])[value].sum().rename_axis(["player", "week"])
        usage[stat] = usage[stat].add(counted, fill_value=0) if stat in usage else counted
    return pd.DataFrame(usage)


def _snap_totals(weekly_snaps) -> pd.DataFrame:
    snaps = weekly_snaps.rename("snaps").reset_index()
    stat = snaps.unit.where(snaps.unit.isin(["offense", "defense"]), "special_teams") + "_snaps"
    return snaps.groupby(["player", "week", stat]).snaps.sum().unstack()


def _on_the_field(season, pbp) -> pd.DataFrame | None:
    """Each counted play of a season with a participation file: its week, its offense's ON_FIELD stats, and
    both sides' players."""
    participation = load("participation", season)
    if participation is None:
        return None
    counted = _counted(pbp)
    plays = counted[counted.plays > 0].join(pbp[["play_id", "week"]]).merge(
        participation[["nflverse_game_id", "play_id", "offense_players", "defense_players", "was_pressure"]],
        left_on=["game_id", "play_id"], right_on=["nflverse_game_id", "play_id"])
    return plays.assign(pressures=plays.dropbacks * (plays.was_pressure == True))  # noqa: E712 (None: not charted)


def _on_field(season, pbp) -> list:
    plays = _on_the_field(season, pbp)
    if plays is None:
        return []
    parts = []
    for column, prefix in (("offense_players", "on_"), ("defense_players", "on_allowed_")):
        players = plays[["week", *ON_FIELD]].assign(player=plays[column].str.split(";")).explode("player")
        players = players[players.player.str.len() > 0]
        parts.append(players.groupby(["player", "week"])[list(ON_FIELD)].sum().add_prefix(prefix))
    return parts


def weekly_stats(season, pbp, weekly_snaps) -> pd.DataFrame:
    lines = stat_lines(season).rename(columns={"player_id": "player"})
    recorded = [stat for stat in lines.columns if stat not in ("game_id", "week", "player", "team", *USAGE_STATS)]
    parts = [_usage(pbp), lines.groupby(["player", "week"])[recorded].sum(), _snap_totals(weekly_snaps),
             *_on_field(season, pbp)]
    weekly = pd.concat(parts, axis=1).fillna(0.0).astype(float)
    return weekly[sorted(weekly.columns)].sort_index()


class Totals:
    """A season's running totals. .before(player, week) -> ((stat, total), ...): what he had done before the
    week, without the stats he has none of."""

    def __init__(self, weekly):
        self.stats = list(weekly.columns)
        self.values = weekly.groupby(level="player").cumsum().to_numpy()
        self.rows = {}  # player -> (his first row, the weeks of his rows)
        for row, (player, week) in enumerate(weekly.index):
            self.rows.setdefault(player, (row, []))[1].append(week)

    def before(self, player, week) -> tuple:
        first, weeks = self.rows.get(player, (0, ()))
        played = bisect.bisect_left(weeks, week)
        if not played:
            return ()
        totals = self.values[first + played - 1]
        return tuple((self.stats[i], float(totals[i])) for i in totals.nonzero()[0])


def _counted(pbp) -> pd.DataFrame:
    """Each play as its offense's TEAM_STATS, with its game, offense (`team`), and defense (`opponent`)."""
    n = lambda column: pbp[column].fillna(0)  # noqa: E731
    play = pbp.down.notna() & pbp.play_type.isin(["run", "pass"]) & (n("two_point_attempt") != 1)
    dropback = play & ((pbp.play_type == "pass") | (n("qb_scramble") == 1))
    run = play & ~dropback
    attempt = play & ((n("complete_pass") + n("incomplete_pass") + n("interception")) > 0)
    snap = pbp.posteam.notna() & pbp.play_type.isin(["run", "pass", "no_play", "punt", "field_goal", "extra_point"])
    flag = snap & (n("penalty") == 1)
    fourth = (pbp.down == 4) & pbp.play_type.isin(["run", "pass", "punt", "field_goal"])
    out = pd.DataFrame({
        "game_id": pbp.game_id, "team": pbp.posteam, "opponent": pbp.defteam,
        "plays": play, "dropbacks": dropback, "runs": run, "shotgun": play & (n("shotgun") == 1),
        "pass_att": attempt, "pass_cmp": attempt & (n("complete_pass") == 1), "pass_yds": attempt * n("passing_yards"),
        "air_yds": attempt * n("air_yards"), "int_thrown": attempt & (n("interception") == 1),
        "sacked": play & (n("sack") == 1), "scrambles": play & (n("qb_scramble") == 1),
        "rush_yds": run * n("yards_gained"), "dropback_yds": dropback * n("yards_gained"),
        "first_downs": play & (n("first_down") == 1),
        "touchdowns": play & (n("touchdown") == 1) & (pbp.td_team == pbp.posteam),
        "fumbles_lost": play & (n("fumble_lost") == 1),
        "snaps": snap, "flags": flag & (pbp.penalty_team == pbp.posteam),
        "defense_flags": flag & (pbp.penalty_team == pbp.defteam),
        "fourth_downs": fourth, "fourth_down_goes": fourth & pbp.play_type.isin(["run", "pass"]),
    })
    return out[out.team.notna()].astype({stat: float for stat in TEAM_STATS})


def _team_games(pbp) -> pd.DataFrame:
    """A row per team and game, in the order the games were played: the team's coach, its TEAM_STATS, what
    it allowed, and the points."""
    counted, stats = _counted(pbp), list(TEAM_STATS)
    offense = counted.groupby(["game_id", "team"])[stats].sum()
    allowed = counted.groupby(["game_id", "opponent"])[stats].sum().add_prefix("allowed_").rename_axis(["game_id", "team"])
    games = pbp.drop_duplicates("game_id")[["game_id", "game_date", "home_team", "away_team", "home_coach", "away_coach",
                                           "home_score", "away_score"]]
    sides = [games.rename(columns={f"{us}_team": "team", f"{us}_coach": "coach", f"{us}_score": "points",
                                   f"{them}_score": "allowed_points"})
             for us, them in (("home", "away"), ("away", "home"))]
    rows = pd.concat(sides)[["game_id", "game_date", "team", "coach", "points", "allowed_points"]]
    rows = rows.assign(games=1.0).join(offense, on=["game_id", "team"]).join(allowed, on=["game_id", "team"])
    return rows.fillna({column: 0.0 for column in offense.columns.union(allowed.columns)}).sort_values(
        ["game_date", "game_id"], ignore_index=True)


def _subjects(season, pbp) -> list:
    """[(who, rows)]: the season's rows for the teams, the head coaches, and the referees, each a frame of
    stats per game in the order the games were played, with `who` naming each row's subject."""
    games, stats = _team_games(pbp), list(TEAM_STATS)
    both = ["games", "points", "allowed_points"] + stats + ["allowed_" + stat for stat in stats]
    crew = games.groupby("game_id", sort=False)[stats].sum().assign(games=1.0).reset_index()  # both offenses
    referee = crew.game_id.map(load("games", season).set_index("game_id").referee)
    return [(games.team, games[["game_id"] + both]), (games.coach, games[["game_id"] + both]), (referee, crew)]


def _totals(season) -> pd.DataFrame:
    """The season's totals as (who, stat, value) rows: each team, head coach, referee, and player."""
    path = CACHE / f"{season}.parquet"
    if not path.exists():
        pbp = load("pbp", season)
        parts = [rows.drop(columns="game_id").groupby(who).sum().rename_axis("who").reset_index().melt("who", var_name="stat")
                 for who, rows in _subjects(season, pbp)]
        players = weekly_stats(season, pbp, weekly_snaps(season, pbp, load("rosters", season)))
        players = players.groupby(level="player").sum().rename_axis("who").reset_index().melt("who", var_name="stat")
        parts.append(players[players.value != 0])
        path.parent.mkdir(parents=True, exist_ok=True)
        unfinished = path.with_suffix(f".{os.getpid()}")  # several processes may be building it at once
        pd.concat(parts).astype({"value": float}).to_parquet(unfinished)
        os.replace(unfinished, path)
    return pd.read_parquet(path)


@lru_cache(maxsize=None)
def _earlier(season) -> dict:
    """{who: ((stat, total), ...)} over the seasons before this one, each discounted by its age."""
    parts = [_totals(s).assign(value=lambda t, s=s: t.value * DECAY ** (season - 1 - s)) for s in SEASONS if s < season]
    if not parts:
        return {}
    pooled = pd.concat(parts).groupby(["who", "stat"]).value.sum()
    out = {}
    for (who, stat), value in pooled[pooled != 0].items():
        out.setdefault(who, []).append((stat, float(value)))
    return {who: tuple(stats) for who, stats in out.items()}


class Forms:
    def __init__(self, season, pbp):
        self.earlier = _earlier(season)
        self.before = {}   # (who, game id) -> the season's totals before that game
        self.so_far = {}   # who -> the season's totals so far, for a game that hasn't been played
        for who, rows in _subjects(season, pbp):
            rows, who = rows[who.notna()], who[who.notna()]
            stats = rows.drop(columns="game_id")
            groups = stats.groupby(who, sort=False)
            before = (groups.cumsum() - stats).to_numpy().tolist()
            for name, game, row in zip(who, rows.game_id, before):
                self.before[name, game] = tuple((stat, value) for stat, value in zip(stats.columns, row) if value)
            for name, row in groups.sum().iterrows():
                self.so_far[name] = tuple((stat, value) for stat, value in row.items() if value)

    def game(self, game_id, *who) -> tuple:
        return tuple((name, Form(self.before.get((name, game_id), self.so_far.get(name, ())), self.earlier.get(name, ())))
                     for name in dict.fromkeys(who) if name)

    def career(self, player) -> tuple:
        return self.earlier.get(player, ())
