from functools import cache

from dateparser import DateDataParser


@cache
def _date_parser():
    return DateDataParser(languages=["en"])


def date_parse(text: str):
    dd = _date_parser().get_date_data(text)
    return dd.date_obj


def human_due_days(days: int) -> str:
    ndays = abs(days)
    match ndays:
        case 0:
            days_expr = "today"
        case 1 if days < 0:
            days_expr = f"{ndays} day ago"
        case 1:
            days_expr = f"{ndays} day"
        case _ if days < 0:
            days_expr = f"{ndays} days ago"
        case _:
            days_expr = f"{ndays} days"
    return days_expr


def deadline_to_color(ndays: int) -> str:
    if ndays >= 3:
        return "cyan-fg"
    if ndays > 0:
        return "yellow-fg"
    if ndays == 0:
        return "orange-fg"
    if ndays < 0:
        return "red-fg"
    return None
