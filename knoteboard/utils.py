import os
from fcntl import LOCK_EX, LOCK_NB, LOCK_UN, flock
from functools import cache

from dateparser import DateDataParser


class FileLock:
    """
    Wrapper for file (or directory) locking.
    Just use a BSD-style advisory lock.
    """

    def __init__(self, path):
        self.path = path
        self.fd = 0

    def __del__(self):
        self.release()

    def acquire(self) -> bool:
        """
        Acquire the lock; return True if acquired successfully.
        """
        self.fd = self.fd or os.open(self.path, os.O_RDONLY)
        try:
            flock(self.fd, LOCK_EX | LOCK_NB)
        except BlockingIOError:
            return False
        return True

    def release(self):
        if self.fd:
            os.close(self.fd)  # closing releases the lock too
            self.fd = 0


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
