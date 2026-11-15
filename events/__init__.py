# START
# Event packages, one per event (see README.md).
# - predictor(event, name=None) -> predict: the event's implementation `name` (events/<event>/predictors/<name>/),
#   or, without a name, the one the event uses by default (DEFAULT in events/<event>/predictors/__init__.py).
# END
from importlib import import_module


def predictor(event: str, name: str | None = None):
    package = import_module(f"events.{event}.predictors")
    return import_module(f"events.{event}.predictors.{name or package.DEFAULT}").predict
