# scenarios

Scenarios chain events together under the rules (see the root README for the concepts). Each scenario is its own package with its own API:

- `play/`: a single play (`run_play`). The core unit; a game is a sequence of plays.
- `coin_toss/`: the coin toss before a game and before overtime (`run_coin_toss`).
- `game/`: a whole game (`run_game`): the coin toss, then plays until the final whistle, with the clock, timeouts, halftime, overtime, and injuries in between.

Planned: `season/` and multi-season. Parent scenarios call child scenarios directly.
