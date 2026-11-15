# START
# Evaluator packages (see README.md).
# - parse_weeks(text) -> list[int] | None: a CLI's --weeks or --seasons value ("1-3" or "1,4"; None if empty).
# END


def parse_weeks(text):
    if not text:
        return None
    if "-" in text:
        low, high = map(int, text.split("-"))
        return list(range(low, high + 1))
    return [int(week) for week in text.split(",")]
