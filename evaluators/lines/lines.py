# START
# Betting lines as forecasts: how good the market was, and how a simulator's distributions compare with it.
# - Line(market, key, line, p_over, actual): a threshold on a number. market is moneyline, spread, total, or
#   a player stat (pass_yds, ...); key names the number: ("margin", game_id) for home minus away points,
#   ("total", game_id), or (stat, game_id, player_id); p_over is the market's probability that the number
#   ends above the line, with the bookmaker's margin removed (0.5 for player props, whose prices aren't
#   published); actual is what the number turned out to be (None if the game hasn't been played, or the
#   player has no stat line for it).
# - lines(season, weeks=None) -> list[Line]: every game line (the moneyline is a line of 0 on the margin) and
#   every player prop.
# - no_vig(odds, other) -> float: the probability of one side of a two-way bet from both American odds.
# - score_lines(lines, samples=None) -> list[dict], one per market: n, over (how often the number went
#   over), brier and log_loss of p_over, and mae of the line as a forecast of the number (not for the
#   moneyline). With samples ({key: simulated values}) only the lines that have samples are scored, and the
#   simulator gets the same columns from the same lines: sim_brier and sim_log_loss of its smoothed share of
#   samples over the line, sim_mae of its median, and sim_crps.
# - favorites(lines) -> [(probability, happened)]: each moneyline from the favorite's side, for reliability.
# Pushes (the number landing exactly on the line) aren't scored.
# END
import math
from dataclasses import dataclass
from statistics import fmean, median

from evaluators.scoring import brier, fair_crps, log_loss, probability
from shared.lines import game_lines, player_lines
from shared.nflverse import load

ACTUAL = {  # our stat name -> nflverse player stats column
    "pass_yds": "passing_yards", "pass_cmp": "completions", "pass_att": "attempts", "pass_td": "passing_tds",
    "int_thrown": "passing_interceptions", "rush_yds": "rushing_yards", "rush_att": "carries",
    "rec_yds": "receiving_yards", "receptions": "receptions", "fg_made": "fg_made", "xp_made": "pat_made",
}


@dataclass(frozen=True)
class Line:
    market: str
    key: tuple
    line: float
    p_over: float
    actual: float | None


def no_vig(odds, other) -> float:
    if math.isnan(odds) or math.isnan(other):
        return 0.5
    implied = [-o / (100 - o) if o < 0 else 100 / (100 + o) for o in (odds, other)]
    return implied[0] / sum(implied)


def lines(season: int, weeks=None) -> list[Line]:
    weeks = None if weeks is None else list(weeks)
    results = load("games", season).set_index("game_id")
    stats = load("player_stats", season).set_index(["game_id", "player_id"])
    out = []
    for g in game_lines(season).itertuples():
        if weeks is None or g.week in weeks:
            margin, total = (None if math.isnan(v) else float(v) for v in results.loc[g.game_id, ["result", "total"]])
            out += [Line("moneyline", ("margin", g.game_id), 0.0, no_vig(g.home_moneyline, g.away_moneyline), margin),
                    Line("spread", ("margin", g.game_id), g.spread, no_vig(g.home_spread_odds, g.away_spread_odds), margin),
                    Line("total", ("total", g.game_id), g.total, no_vig(g.over_odds, g.under_odds), total)]
    for p in player_lines(season, weeks).itertuples():
        played = (p.game_id, p.player_id) in stats.index
        actual = float(stats.at[(p.game_id, p.player_id), ACTUAL[p.stat]]) if played else None
        out.append(Line(p.stat, (p.stat, p.game_id, p.player_id), p.line, 0.5, actual))
    return out


def score_lines(lines, samples=None) -> list[dict]:
    rows = []
    for market in ("moneyline", "spread", "total", *ACTUAL):
        scored = [l for l in lines if l.market == market and l.actual is not None and l.actual != l.line
                  and (samples is None or l.key in samples)]
        if not scored:
            continue
        over = [l.actual > l.line for l in scored]
        median_like = market != "moneyline"
        row = dict(market=market, n=len(scored), over=fmean(over),
                   brier=fmean(brier(l.p_over, o) for l, o in zip(scored, over)),
                   log_loss=fmean(log_loss(l.p_over, o) for l, o in zip(scored, over)),
                   mae=fmean(abs(l.line - l.actual) for l in scored) if median_like else None)
        if samples is not None:
            shares = [probability([x > l.line for x in samples[l.key]]) for l in scored]
            row.update(sim_brier=fmean(brier(p, o) for p, o in zip(shares, over)),
                       sim_log_loss=fmean(log_loss(p, o) for p, o in zip(shares, over)),
                       sim_mae=fmean(abs(median(samples[l.key]) - l.actual) for l in scored) if median_like else None,
                       sim_crps=fmean(fair_crps(samples[l.key], l.actual) for l in scored))
        rows.append(row)
    return rows


def favorites(lines) -> list[tuple[float, bool]]:
    played = [l for l in lines if l.market == "moneyline" and l.actual not in (None, 0)]
    return [(max(l.p_over, 1 - l.p_over), (l.actual > 0) == (l.p_over >= 0.5)) for l in played]
