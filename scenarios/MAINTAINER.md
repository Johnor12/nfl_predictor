# MAINTAINER

- __init__.py: package marker.
- play/: the play scenario (see its MAINTAINER.md).
- coin_toss/: the coin toss scenario (see its MAINTAINER.md).
- game/: the game scenario (see its MAINTAINER.md).

Notes:
- Dependencies point from parent to child: game -> coin_toss, play. The children know nothing about the game.
