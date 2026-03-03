import urwid

from knoteboard.components import (
    Board,
    DialogLauncher,
    EventPanel,
    SearchPanel,
    StatusBar,
    info_msg,
)
from knoteboard.models import AppDataModel
from knoteboard.palette import Palette
from knoteboard.storage import Storage, get_storage


class App:
    STATUS_MSG = [
        "[?] - help",
        "[q] - quit",
        "[a] - add",
        "[d] - delete",
        "[Enter] - edit",
        "[h/j/k/l] - navigation",
        "[Shift + h/j/k/l] - move item",
        "[/] - search",
    ]

    PALETTE = (
        [
            #
            # Main view
            #
            ("title", *Palette.format(Palette.YELLOW, Palette.BASE03)),
            ("header", *Palette.format(Palette.BASE1, Palette.BASE02)),
            ("header-focus", *Palette.format(Palette.BASE2, Palette.BASE01)),
            ("column", *Palette.format(Palette.BASE0, Palette.BASE03)),
            ("status", *Palette.format(Palette.BASE1, Palette.BASE02)),
            ("clock", *Palette.format(Palette.YELLOW, Palette.BASE02)),
            #
            # Board
            #
            ("item", *Palette.format(Palette.BASE0, Palette.BASE03)),
            ("item-focus", *Palette.format(Palette.BASE2, Palette.BASE01)),
            #
            # Item edit form
            #
            ("form-bg", *Palette.format(Palette.BASE0, Palette.BASE03)),
            ("form-title", *Palette.format(Palette.YELLOW, Palette.BASE03)),
            # Regular field
            ("field-label", *Palette.format(Palette.YELLOW, Palette.BASE03)),
            ("field-box", *Palette.format(Palette.BASE0, Palette.BASE03)),
            ("field-box-focus", *Palette.format(Palette.BASE1, Palette.BASE02)),
            # Date validation
            ("date-ok", *Palette.format(Palette.GREEN, Palette.BASE03)),
            ("date-err", *Palette.format(Palette.RED, Palette.BASE03)),
            #
            # Buttons
            #
            ("btn", *Palette.format(Palette.BASE3, Palette.BASE01)),
            ("btn-focus", *Palette.format(Palette.BASE2, Palette.YELLOW)),
            #
            # Dialog
            #
            ("dialog", *Palette.format(Palette.BASE3, Palette.BASE00)),
        ]
        + [
            #
            # Base colors to fill space.
            #
            (name, *Palette.format(value, value))
            for name, value in Palette.list().items()
        ]
        + [
            (f"{name}-fg", *Palette.format(value, Palette.BASE03))
            for name, value in Palette.list().items()
        ]
    )

    storage: Storage
    widgets: list[tuple]
    popup: bool = False
    refresh_in: int = 0

    def __init__(self, path: str | None = None):
        self.storage = get_storage(path)
        state = self.storage.load()

        self.status_bar = StatusBar(self.STATUS_MSG)
        self.board = Board(self, state.board)
        self.search = SearchPanel(self)
        self.events = EventPanel(self, self.board)
        self.events.update()
        self.widgets = []

        #
        # Initialize the root frame and the event loop.
        #
        header = urwid.AttrMap(
            urwid.Text(("title", self.storage.title()), align="center"), "title"
        )
        self.body = urwid.Pile(
            [
                ("weight", 5, self.board.get_widget()),
                (
                    "weight",
                    1,
                    self.events.get_widget(),
                ),
            ]
        )
        self.root_frame = urwid.Frame(
            self.body,
            header=header,
            footer=self.status_bar.get_widget(),
        )
        self.root_launcher = DialogLauncher(self.root_frame)
        self.loop = urwid.MainLoop(
            self.root_launcher,
            self.PALETTE,
            unhandled_input=self._key_handler,
            handle_mouse=False,
            pop_ups=True,
        )
        self.loop.screen.set_terminal_properties(colors=2**24)
        self.loop.set_alarm_in(0, self._tick)

    def _check_sync(self):
        if not self.board.changed:
            return  # no status change
        self.board.changed = False
        self.events.update()
        self.storage.save(
            AppDataModel(
                board=self.board.export(),
            )
        )
        self.flash_message("saved")

    def _tick(self, loop: urwid.MainLoop, _):
        self._check_sync()
        if self.refresh_in:
            self.refresh_in -= 1
            if self.refresh_in == 0:
                self._refresh()
        self.status_bar.update_clock()
        loop.set_alarm_in(1, self._tick)

    def _refresh(self):
        widget, message = (
            self.widgets[-1] if self.widgets else (self.body, self.STATUS_MSG)
        )
        self.root_frame.set_body(widget)
        self.status_bar.update(message)

    def _get_help_msg(self):
        current_status_msgs = (
            self.widgets[-1][1] if self.widgets else self.STATUS_MSG
        )
        return "\n".join([line.strip() for line in current_status_msgs])

    def flash_message(self, msg: str):
        self.status_bar.update([msg])
        self.refresh_in = 3  # seconds

    #
    # Key handler.
    #

    def _key_handler(self, key: str):
        if self.widgets or self.popup:
            # Handling some other widget.
            return
        match key:
            case "q" | "Q":
                self._check_sync()
                raise urwid.ExitMainLoop()

            # Navigation
            case "l" | "right":
                self.board.switch_item(column=+1)
            case "h" | "left":
                self.board.switch_item(column=-1)
            case "k" | "up":
                self.board.switch_item(index=-1)
            case "j" | "down":
                self.board.switch_item(index=+1)

            # Moving the item
            case "L" | "shift right":
                self.board.move_item(column=+1)
            case "H" | "shift left":
                self.board.move_item(column=-1)
            case "K" | "shift up":
                self.board.move_item(index=-1)
            case "J" | "shift down":
                self.board.move_item(index=+1)

            # Add/edit/delete
            case "a" | "A":
                self.board.create_item()
            case "enter":
                self.board.edit_item()
            case "d":
                self.board.delete_item()
            case "/":
                self.search.open(self.body)
            case "?":
                self.open_dialog(
                    info_msg(self._get_help_msg(), self, align="left")
                )

    #
    # Widget and dialog handling.
    #

    def push_widget(self, widget, status):
        self.widgets.append((widget, status))
        self._refresh()

    def pop_widget(self):
        if self.widgets:
            self.widgets.pop()
        self._refresh()

    def open_dialog(self, dialog, status_msgs: list[str] | None = None):
        self.popup = True
        cols, rows = self.loop.screen.get_cols_rows()
        self.root_launcher.open(dialog, cols, rows)
        if status_msgs:
            self.status_bar.update(status_msgs)

    def close_dialog(self):
        self.root_launcher.close_pop_up()
        self.popup = False
        self._refresh()

    def run(self):
        self.loop.run()
