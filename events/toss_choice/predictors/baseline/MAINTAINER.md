# MAINTAINER

- __init__.py: `predict`, and the rates (`OPENING`, `OVERTIME` by format).

Notes:
- No priors: play-by-play data doesn't record who won the toss or what they chose. Who received the opening kickoff is recorded, which bounds the rates but can't separate "won and received" from "lost, and the winner deferred".
- The overtime rate under the both-possess format is a guess. It only matters for overtime games.
