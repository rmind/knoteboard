from typing import Callable

import urwid
from pydantic import BaseModel


class DialogButtons(BaseModel):
    text: str
    on_press: Callable
    keys: list[str] | None = None


class Dialog(urwid.WidgetWrap):
    """
    Generic dialog form.  Accepts an arbitrary list of buttons with the
    callbacks and key bindings.
    """

    def __init__(
        self,
        message: str,
        buttons: list[DialogButtons],
        align: str | None = None,
    ):
        self.btn_keymap = {
            key: btn.on_press for btn in buttons for key in (btn.keys or [])
        }
        btn_widgets = [
            urwid.Button(btn.text, on_press=btn.on_press, align="center")
            for btn in buttons
        ]
        self.text = urwid.Text(message, align=align or "center")
        pile = urwid.Pile(
            [
                self.text,
                urwid.Divider(),
                urwid.Columns(
                    [
                        (
                            "weight",
                            1,
                            urwid.Padding(
                                urwid.AttrMap(btn, "btn", "btn-focus"),
                                "center",
                                width=10,
                            ),
                        )
                        for btn in btn_widgets
                    ]
                ),
            ]
        )
        widget = urwid.AttrMap(urwid.Filler(pile), "dialog")
        super().__init__(widget)

    def get_text_rows(self, width: int):
        return self.text.rows((width,))

    def keypress(self, size, key):
        if callback := self.btn_keymap.get(key):
            callback(key)
            return
        return self._w.keypress(size, key)


def info_msg(message: str, app, align=None):
    """
    Generic information message with a single button to just dismiss.
    """

    return Dialog(
        message,
        [
            DialogButtons(
                text="OK",
                on_press=lambda _: app.close_dialog(),
                keys=["esc"],
            ),
        ],
        align=align,
    )


class DialogLauncher(urwid.PopUpLauncher):
    """
    A generic dialog launcher.  It will put the dialog in the center.
    """

    def __init__(self, widget):
        self._popup_widget = None
        super().__init__(widget)

    def open(self, popup_widget, cols, rows):
        width = 40
        height = 5 + popup_widget.get_text_rows(width=width)
        self._popup_params = {
            "left": max(0, (cols - width) // 2),
            "top": max(0, (rows - width) // 2),
            "overlay_width": width,
            "overlay_height": height,
        }
        self._popup_widget = popup_widget
        self.open_pop_up()

    def create_pop_up(self):
        return self._popup_widget

    def get_pop_up_parameters(self):
        return self._popup_params
