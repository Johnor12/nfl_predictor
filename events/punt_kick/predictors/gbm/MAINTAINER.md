# MAINTAINER

- __init__.py: `predict` (the baseline's, with this package's `distance`) and `distance` (a draw from the season's model on a scrimmage down; the baseline's when the season has no model).
- inputs.py: `NAMES`, `WHO`, `CUTS`, `LIMIT`, and `features(ctx, punter)`, the one place the model's inputs are read, for training and for predicting.
- train.py: `example` (a real punt as a training row), `train(season)`, `TABLES`, and the CLI.
- model_<season>.txt: the model for that season's games (LightGBM's text format, about 0.5 MB), trained on 2011 up to the season before. `python -m events.training` keeps them current with the rest.
- test_gbm.py: the model reads the punter and the weather and knows the goal line; synthetic plays stay valid; the fallback before the first model.

Measured (2026-11-16, against the baseline, which is still the punt kick event's default):
- Play evaluator (the default 160 games of 2021 to 2026 at 100 sims, case by case): `punt_kick: distance` 4.266 -> 4.182 (-2.0%, 2.0 standard errors on 1,200 punts; skill +16.3% -> +17.9%). With the weather read exactly it was 4.217 (-1.1%): coarse is better here too.
- Game evaluator (480 games at 50 sims, twice, with two seeds): `game: total` +2.6% (2.9 standard errors) and +0.8% (0.8), `team: points` +1.8% and +0.9%, `game: margin` +1.2% and +0.7%. Worse both times, by more than chance once. The punts themselves are right (in simulated games 46.2 yards and 6.3% touchbacks against a real 47.1 and 7.3%; the baseline's 46.6 and 5.4%).
- So it is better at punts and no better, probably worse, at games, and it isn't the default. The likely reason: the weather. This model is the only thing in the simulator that knows the wind or the roof, and what it knows is that punts are shorter in the wind and longer indoors, which gives both offenses a shorter field in bad weather and a longer one in a dome. Real games go the other way (bad weather costs points, through passing and kicking, which nothing here models), so the one true effect moves a game's total the wrong way. The harm was largest in indoor games.
- It becomes worth using when the offense feels the weather too, or without the weather (the punter's average alone was worth as much on 2013 to 2020 and wasn't run through the game evaluator).

Notes:
- Out of sample: a season's model has seen nothing of that season, and the inputs were chosen on 2013 to 2020, each season scored by a model of the others.
- What each input was worth there, per punt (squared error of the expected distance) and per team and game (expected against real yards, squared), on top of the situation, read coarsely: the weather -1.3% and -4.7% (4.8 and 4.3 standard errors); the punter's yards per punt -1.3% and -5.2% (4.6 and 4.4); both -2.5% and -8.7% (7.1 and 5.7). The surface, a neutral site, his draft pick, and his years in the league added nothing.
- This is where the weather is worth most per play. It was tried on field goals, extra points, pass results, air yards, yards after the catch, run yards, fumbles, the shotgun, run or pass, sacks and scrambles, and the fourth-down decision (`events/MAINTAINER.md`).
- A punt into the end zone is recorded at the goal line, as a carry is: the model is fitted with the yards to the goal line as its limit, and `distance` takes a draw between two cuts that hold the goal line from the histogram's whole tail (`events/carry/predictors/gbm/MAINTAINER.md` has what happens without).
- The cuts are 2 yards apart, not 1: a punt's distance is spread over 40 yards, and the baseline's histogram for that part of the field fills in the yard.
- After changing `inputs.py` or `example`, delete `.cache/training/punt_kick_gbm_*.parquet` and retrain every model.
