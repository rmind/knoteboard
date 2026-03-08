import urwid

from knoteboard.components.editbox import EditBox
from knoteboard.models import TagModel
from knoteboard.palette import Palette


class NavColumns(urwid.Columns):
    def keypress(self, size, key):
        match key:
            case "j":
                return super().keypress(size, "down")
            case "k":
                return super().keypress(size, "up")
            case "h":
                return super().keypress(size, "left")
            case "l":
                return super().keypress(size, "right")
            case _:
                return super().keypress(size, key)


class TagPanel(urwid.WidgetWrap):
    """
    Panel to manage the arbitrary tags.
    """

    TAG_COLORS = [
        name for name in Palette.list().keys() if not name.startswith("base")
    ]
    STATUS_MSG = [
        "[Tab / Shift-Tab] - next/previous field",
        "[Space] - select",
        "[Esc] - cancel",
    ]

    tags: list[tuple[str, int]]
    color_idx: int

    def __init__(self, app, tags: list[TagModel] | None):
        self.app = app
        self.tags = [(tag.name, tag.color) for tag in tags or []]
        self.color_idx = 0

        group = []
        color_buttons = []
        for i, label in enumerate(self.TAG_COLORS):
            rb = urwid.RadioButton(
                group,
                (label, "  "),
                state=(i == self.color_idx),
                on_state_change=self._on_color,
                user_data=i,
            )
            color_buttons.append(urwid.AttrMap(rb, "item", "item-focus"))

        self.edit = EditBox()
        self.pile = urwid.Pile([])
        self._refresh()
        self.elements = urwid.Pile(
            [
                urwid.Divider(),
                urwid.Columns(
                    [
                        ("fixed", 9, urwid.Text(("field-label", "New tag:"))),
                        urwid.AttrMap(
                            self.edit, "field-box", "field-box-focus"
                        ),
                    ]
                ),
                urwid.Divider(),
                NavColumns(color_buttons, dividechars=1),
                urwid.Divider(),
                urwid.Padding(
                    urwid.AttrMap(
                        urwid.Button("Add", on_press=lambda _: self._on_add()),
                        "btn",
                        "btn-focus",
                    ),
                    align="center",
                    width=7,
                ),
                urwid.Divider("─"),
                self.pile,
            ]
        )
        panel = urwid.LineBox(
            urwid.Padding(self.elements, left=1, right=1),
            title="Tags",
            title_attr="field-label",
        )
        overlay = urwid.Overlay(
            urwid.AttrMap(panel, "form-bg"),
            urwid.SolidFill(" "),
            align="center",
            valign="middle",
            width=("relative", 30),
            height="pack",
        )
        super().__init__(overlay)

    def _get_tag_item(self, name, color):
        bar = urwid.AttrMap(urwid.Text("   "), color)
        label = urwid.Text(("item", name))
        return urwid.Columns([("fixed", 3, bar), label], dividechars=1)

    def _refresh(self):
        items = []
        for i, (name, color) in enumerate(sorted(self.tags)):
            rm = urwid.AttrMap(
                urwid.Button("✕", on_press=self._on_remove, user_data=i),
                "orange-fg",
                "red-fg",
            )
            items.append(
                urwid.Columns(
                    [self._get_tag_item(name, color), ("fixed", 5, rm)],
                    dividechars=1,
                )
            )
        items = items or [urwid.Text(("column", "(no tags)"))]
        self.pile.contents = [(w, self.pile.options()) for w in items]

    def _on_color(self, _, state: bool, index: int):
        if state:
            self.color_idx = index

    def _on_cancel(self):
        self.color_idx = 0
        self.edit.edit_text = ""
        self.app.pop_widget()

    def _on_add(self):
        if not (name := self.edit.edit_text.strip()):
            return
        # Add the new tag.
        color = self.TAG_COLORS[self.color_idx]
        self.tags.append((name, color))
        self.app.flag_changed()
        # Clear and refresh.
        self.elements.set_focus(1)
        self.edit.edit_text = ""
        self._refresh()

    def _on_remove(self, _btn, idx: int):
        self.tags.pop(idx)
        self.app.flag_changed()
        self._refresh()

    def keypress(self, size, key):
        match key:
            case "tab":
                self._w.keypress(size, "down")
            case "shift tab":
                self._w.keypress(size, "up")
            case "esc":
                self._on_cancel()
            case _:
                return self._w.keypress(size, key)

    def selectable(self):
        return True

    def open(self):
        self.app.push_widget(self, self.STATUS_MSG)

    def export(self) -> list[TagModel]:
        """
        Export the current tags.
        """
        return [TagModel(name=name, color=color) for name, color in self.tags]
