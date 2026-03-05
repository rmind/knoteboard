import urwid

from knoteboard.components import Item
from knoteboard.components.editbox import EditBox


class SearchPanel(urwid.WidgetWrap):
    STATUS_MSG = ["[Esc] - cancel", "[Tab] - next item", "[Enter] - open"]
    TOP_ITEMS = 10  # how many items to show

    focus_item: Item

    def __init__(self, app):
        self.app = app

        search_edit = EditBox(" > ", "")
        self.results = urwid.SimpleFocusListWalker([])
        pile = urwid.Pile(
            [
                urwid.AttrMap(search_edit, "column"),
                urwid.Divider(),
                urwid.BoxAdapter(urwid.ListBox(self.results), self.TOP_ITEMS),
            ]
        )
        urwid.connect_signal(search_edit, "change", self._on_change)
        widget = urwid.AttrMap(
            urwid.LineBox(
                pile, title="Search", title_align="left", title_attr="yellow-fg"
            ),
            "column",
        )
        super().__init__(widget)

    def _get_text_rows(self) -> int:
        cols, _ = self.app.loop.screen.get_cols_rows()
        return cols

    def _get_item_text(self, item: Item) -> str:
        text = item.title
        if item.description:
            description = item.description.replace("\n", " ")
            text = f"{text} | {description}"
        if len(text) > self._get_text_rows():
            text = text[: self._get_text_rows() - 10] + " ..."
        return text

    def _on_change(self, widget, text):
        self.results.clear()
        self.focus_item = None
        if not (q := text.strip().lower()):
            return
        items = self.app.board.get_items()
        if not items:
            self.results.append(urwid.Text("No results."))
            return
        for item in items:
            if q in item.data.title.lower():
                item_entry = urwid.AttrMap(
                    urwid.Padding(
                        urwid.Text(self._get_item_text(item.data)),
                        left=1,
                        right=1,
                    ),
                    "item" if self.results else "item-focus",
                )
                item_entry.user_data = item
                self.results.append(item_entry)
        self.focus_item = self.results[0] if self.results else None

    def _set_focus(self, direction: int):
        if self.results:
            idx = max(0, self.results.focus + direction) % len(self.results)
            for i, item in enumerate(self.results):
                item.attr_map = {None: "item-focus" if i == idx else "item"}
            self.results.set_focus(idx)
            self.focus_item = self.results[idx]

    def _submit(self):
        if self.focus_item:
            item = self.focus_item.user_data
            self.app.board.switch_to(item.column, item.row)
            self.app.board.edit_item()

    def keypress(self, size, key):
        match key:
            case "esc":
                self.app.pop_widget()
            case "enter":
                self._submit()
            case "tab" | "down":
                self._set_focus(+1)
            case "shift tab" | "up":
                self._set_focus(-1)
            case _:
                return self._w.keypress(size, key)

    def selectable(self):
        return True

    def open(self, base_widget):
        body = urwid.Pile(
            [
                ("pack", self),
                base_widget,
            ]
        )
        self.app.push_widget(body, self.STATUS_MSG)
