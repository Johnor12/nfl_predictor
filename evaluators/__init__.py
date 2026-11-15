# START
# Evaluator packages (see README.md).
# - parse_weeks(text) -> list[int] | None: a CLI's --weeks or --seasons value ("1-3" or "1,4"; None if empty).
# - executor(workers=None) -> concurrent.futures.Executor: where an evaluation's jobs run: a pool of worker
#   processes (one per core if workers is None), or this process if workers is 1 (Inline).
# END
from concurrent.futures import Executor, Future, ProcessPoolExecutor


def parse_weeks(text):
    if not text:
        return None
    if "-" in text:
        low, high = map(int, text.split("-"))
        return list(range(low, high + 1))
    return [int(week) for week in text.split(",")]


class Inline(Executor):
    """Runs each job when it is submitted, in this process."""

    def submit(self, fn, /, *args, **kwargs):
        future = Future()
        future.set_result(fn(*args, **kwargs))
        return future


def executor(workers=None) -> Executor:
    return Inline() if workers == 1 else ProcessPoolExecutor(workers)
