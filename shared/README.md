# shared

Logic and data shared across events, scenarios, simulators, and evaluators. Each package has its own API:

- `rulebook/`: NFL rules that change between seasons (`rules_for(season)`).
- `priors/`: the toolkit behind the count-based baseline predictors: sampling, buckets, picking players, and building and loading priors files.
- `nflverse/`: real NFL data, downloaded and cached (`load`), and every real play as a play scenario input (`real_plays`).
