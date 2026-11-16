# START
# Real stat lines: what every player did in every game, in the play scenario's stat names.
# - stat_lines(season) -> DataFrame, one row per game and player who did anything: game_id, week, player_id
#   (gsis), team, and a column per stat (0 where he had none). A game is in once every file has it (its box
#   score and, from 2018 on, its charting, which comes a few days later), so no charted stat reads 0 for
#   a game that hasn't been charted yet. The box score's stats (STAT_COLUMNS) are there
#   for every season; the charted ones (CHARTED) only for the seasons Pro Football Reference charted (2018
#   on), and a season without them has no such columns.
# - STAT_COLUMNS: stat -> the nflverse player stats columns it is the sum of. Every stat the play scenario
#   credits that a box score has.
# - CHARTED: PFR file -> {stat: its column}: a defender's pressures, hurries, blitzes, missed tackles, and
#   what he allowed in coverage; a passer's pressures and bad throws; a runner's yards before and after
#   contact; a receiver's drops. CHARTED_SINCE: the first season that has them.
# Internals: _box (the box score in our names), _charted (one PFR file in our names, by gsis id).
# END
from functools import lru_cache

import pandas as pd

from shared.nflverse.download import load

STAT_COLUMNS = {
    "pass_att": ("attempts",), "pass_cmp": ("completions",), "pass_yds": ("passing_yards",),
    "pass_td": ("passing_tds",), "int_thrown": ("passing_interceptions",), "sacked": ("sacks_suffered",),
    "sack_yards": ("sack_yards_lost",), "pass_air_yds": ("passing_air_yards",),
    "pass_yac": ("passing_yards_after_catch",), "pass_first_downs": ("passing_first_downs",),
    "rush_att": ("carries",), "rush_yds": ("rushing_yards",), "rush_td": ("rushing_tds",),
    "rush_first_downs": ("rushing_first_downs",),
    "targets": ("targets",), "receptions": ("receptions",), "rec_yds": ("receiving_yards",),
    "rec_td": ("receiving_tds",), "target_air_yds": ("receiving_air_yards",),
    "rec_yac": ("receiving_yards_after_catch",), "rec_first_downs": ("receiving_first_downs",),
    "two_pt": ("passing_2pt_conversions", "rushing_2pt_conversions", "receiving_2pt_conversions"),
    "fumbles": ("fumbles_total",), "fumbles_lost": ("fumbles_lost_total",),
    "penalties": ("penalties",), "penalty_yards": ("penalty_yards",),
    # the box score's solo tackles: alone, or as the tackler another player assisted
    "tackles": ("def_tackles_solo", "def_tackles_with_assist"), "assists": ("def_tackle_assists",),
    "tfl": ("def_tackles_for_loss",), "sacks": ("def_sacks",), "qb_hits": ("def_qb_hits",),
    "interceptions": ("def_interceptions",), "int_ret_yds": ("def_interception_yards",),
    "passes_defended": ("def_pass_defended",), "forced_fumbles": ("def_fumbles_forced",),
    "fumble_recoveries": ("fumble_recovery_own", "fumble_recovery_opp"),
    "fumble_ret_yds": ("fumble_recovery_yards_own", "fumble_recovery_yards_opp"),
    "fumble_ret_td": ("fumble_recovery_tds",),
    "kicks_blocked": ("def_punt_blocks", "def_pat_blocks", "def_fg_blocks"),
    "safeties": ("def_safeties",), "def_td": ("def_tds",), "special_teams_td": ("special_teams_tds",),
    "punt_returns": ("punt_returns",), "punt_ret_yds": ("punt_return_yards",),
    "kick_returns": ("kickoff_returns",), "kick_ret_yds": ("kickoff_return_yards",),
    "fg_att": ("fg_att",), "fg_made": ("fg_made",), "fg_made_yds": ("fg_made_distance",),
    "xp_att": ("pat_att",), "xp_made": ("pat_made",),
    "punts": ("pt_att",), "punt_yds": ("pt_yards",),
}
CHARTED_SINCE = 2018
CHARTED = {
    "pfr_def": {"pressures": "def_pressures", "hurries": "def_times_hurried", "blitzes": "def_times_blitzed",
                "missed_tackles": "def_missed_tackles", "coverage_targets": "def_targets",
                "coverage_cmp": "def_completions_allowed", "coverage_yds": "def_yards_allowed",
                "coverage_td": "def_receiving_td_allowed"},
    "pfr_pass": {"pressured": "times_pressured", "hurried": "times_hurried", "hit": "times_hit",
                 "blitzed": "times_blitzed", "bad_throws": "passing_bad_throws", "pass_drops": "passing_drops"},
    "pfr_rush": {"rush_yds_before_contact": "rushing_yards_before_contact",
                 "rush_yds_after_contact": "rushing_yards_after_contact",
                 "rush_broken_tackles": "rushing_broken_tackles"},
    "pfr_rec": {"drops": "receiving_drop", "rec_broken_tackles": "receiving_broken_tackles"},
}


def _box(season) -> pd.DataFrame:
    box = load("player_stats", season)
    box = box[box.player_id.notna()]  # a team's leftover row (penalties nobody was charged with) isn't a player
    stats = {stat: box[list(columns)].fillna(0).sum(axis=1) for stat, columns in STAT_COLUMNS.items()}
    stats["sack_yards"] = -stats["sack_yards"]  # the box score has them as a loss; ours are the yards lost
    return pd.DataFrame({"game_id": box.game_id, "player_id": box.player_id, "team": box.team, **stats})


def _charted(name, season, gsis) -> pd.DataFrame | None:
    charted = load(name, season)
    if charted is None:
        return None
    columns = {column: stat for stat, column in CHARTED[name].items()}
    charted = charted.assign(player_id=charted.pfr_player_id.map(gsis)).dropna(subset=["player_id"])
    return charted.groupby(["game_id", "player_id", "team"], as_index=False)[list(columns)].sum().rename(columns=columns)


@lru_cache(maxsize=None)
def stat_lines(season: int) -> pd.DataFrame:
    players = load("players").dropna(subset=["pfr_id", "gsis_id"])
    gsis = players[players.gsis_id.str.startswith("00-")].drop_duplicates("pfr_id").set_index("pfr_id").gsis_id
    lines = _box(season)
    complete = set(lines.game_id)
    for name in CHARTED:
        charted = _charted(name, season, gsis)
        if charted is not None:
            lines = lines.merge(charted, how="outer", on=["game_id", "player_id", "team"])
            complete &= set(charted.game_id)
    lines = lines[lines.game_id.isin(complete)]  # the box score and the charting are published days apart
    weeks = load("games", season).set_index("game_id").week
    lines.insert(1, "week", lines.game_id.map(weeks))
    stats = [column for column in lines.columns if column not in ("game_id", "week", "player_id", "team")]
    return lines.dropna(subset=["week"]).fillna({stat: 0.0 for stat in stats}).astype({"week": int}).reset_index(drop=True)
