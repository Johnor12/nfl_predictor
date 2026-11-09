# scenarios

Scenarios chain events together under the rules (see the root README for the concepts). Each scenario is its own package with its own API:

- `play/`: a single play (`run_play`). The core unit; games will be sequences of plays.

Planned: `game/` (phase 0), then `season/` and multi-season. Parent scenarios call child scenarios directly.
