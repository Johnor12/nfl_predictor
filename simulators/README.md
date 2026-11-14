# simulators

Simulators run a scenario many times and aggregate the outcomes (see the root README for the concepts). One package per scenario:

- `play/`: the play scenario over many inputs (`simulate_plays`).
- `game/`: whole games, played many times from the same inputs (`simulate_game`), and a forecast of the distributions (`python -m simulators.game <game id>`).
