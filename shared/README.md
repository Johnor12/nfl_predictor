# shared

Logic and data shared across events, scenarios, simulators, and evaluators. Each package has its own API:

- `rulebook/`: NFL rules that change between seasons (`rules_for(season)`).
- `priors/`: the toolkit behind the count-based baseline predictors: sampling, buckets, picking players, and building and loading priors files.
- `nflverse/`: real NFL data, downloaded and cached (`load`), every real play as a play scenario input (`real_plays`, `real_samples`), and every real game as a game scenario input (`real_games`).
- `lines/`: betting lines: each game's spread, total, and moneylines (`game_lines`) and player props (`player_lines`).
