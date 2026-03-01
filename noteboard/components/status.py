from datetime import datetime

import urwid


class StatusBar:
    def __init__(self, msgs: list[str]):
        self.status = urwid.Text(("status", ""), align="left")
        self.update(msgs)

        self.clock_widget = urwid.Text(("clock", ""), align="right")
        self.status_bar = urwid.AttrMap(
            urwid.Columns([self.status, self.clock_widget]), "status"
        )

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d (%a) - %H:%M:%S")
        self.clock_widget.set_text(("clock", f"{now} "))

    def _get_message(self, msgs: list[str]) -> str:
        shortened_msgs = msgs[:5] + (["..."] if len(msgs) > 5 else [])
        return "; ".join(shortened_msgs)

    def update(self, msgs: list[str]):
        msg = self._get_message(msgs)
        self.status.set_text(f"OK: {msg}")

    def get_widget(self):
        return self.status_bar
