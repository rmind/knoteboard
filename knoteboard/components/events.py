from datetime import datetime

import urwid

from knoteboard.utils import deadline_to_color, human_due_days


class EventPanel:
    """
    Events as deadlines ("due in") panel.
    """

    TOP_ITEMS = 10  # how many items to get

    def __init__(self, app, board):
        self.board = board
        self.title_line = urwid.AttrMap(
            urwid.Text(
                ("clock", "DUE IN:"),
                align="left",
            ),
            "header",
        )
        self.pile = urwid.Pile([self.title_line])
        self.widget = urwid.AttrMap(
            urwid.Filler(
                urwid.Padding(self.pile, left=1, right=1),
                valign="top",
            ),
            "column",
        )

    @staticmethod
    def _get_due_date(now: datetime, target_date: datetime):
        ndays = (target_date - now).days
        attr = deadline_to_color(ndays)
        expr = human_due_days(ndays)
        return (attr or "item", expr)

    def _get_top_items(self):
        now = datetime.now()
        dated_items = (
            item.data
            for item in self.board.get_items()
            if item.data.date and not item.done
        )
        earliest_items = sorted(dated_items, key=lambda item: item.date)
        return [
            (*self._get_due_date(now, item.date), item.title)
            for item in earliest_items[0 : self.TOP_ITEMS]
        ]

    def update(self):
        rows = [self.title_line]
        for tag_attr, tag_text, msg in self._get_top_items():
            row = urwid.Columns(
                [
                    (
                        "fixed",
                        14,
                        urwid.AttrMap(urwid.Text(tag_text), tag_attr),
                    ),
                    urwid.AttrMap(urwid.Text(msg), "item"),
                ],
                dividechars=1,
            )
            rows.append(urwid.AttrMap(row, "column"))
        self.pile.widget_list = rows

    def get_widget(self):
        return self.widget
