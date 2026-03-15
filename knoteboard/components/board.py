import urwid

from knoteboard.components.dialog import Dialog, DialogButtons
from knoteboard.components.item import Item, ItemForm
from knoteboard.components.tags import SetTagDialog, TagPanel
from knoteboard.models import (
    BoardModel,
    ColumnModel,
    ItemModel,
    TagModel,
)


class Board:
    """
    Kanban-like board of items (tickets / notes).
    """

    DELETE_COMPLETED = 7  # days
    GC_DELETED = 30  # days

    columns: list[str]
    items: list[list[Item]]
    terminal_columns: tuple[int]
    deleted: list[Item]

    focus_col: int
    focus_idx: int

    def __init__(self, app, data: BoardModel, tags: TagPanel):
        self.app = app
        self.tags = tags

        # Initialize columns and items.
        tag_map = tags.get_tag_map()
        self.columns = [column.label for column in data.columns]
        self.items = [
            [Item(item, tag_map) for item in column.items]
            for column in data.columns
        ]
        self.terminal_columns = tuple(
            i for i, column in enumerate(data.columns) if column.terminal
        )
        self.deleted = data.deleted or []

        #
        # Setup the widget.
        #
        self.listwalkers = [
            urwid.SimpleFocusListWalker([]) for _ in self.columns
        ]
        self.column_frames = []
        for i, title in enumerate(self.columns):
            header = urwid.AttrMap(
                urwid.Text(("header", f" {title} "), align="center"), "header"
            )
            body = urwid.ListBox(self.listwalkers[i])
            frame = urwid.Frame(urwid.AttrMap(body, "column"), header=header)
            self.column_frames.append(frame)
        self.widget = urwid.Columns(self.column_frames, dividechars=1)

        # Load the items.
        self.focus_col = 0
        self.focus_idx = 0
        self.refresh()

    def get_items(self, ignore_done: bool = False) -> list[Item]:
        return [
            item
            for column_items in self.items
            for item in column_items
            if (not ignore_done or not item.done)
        ]

    def _get_current_item(self) -> Item | None:
        return (
            self.items[self.focus_col][self.focus_idx]
            if self.items[self.focus_col]
            else None
        )

    #
    # Rendering
    #

    def _refresh_column(self, col: int):
        widgets = []
        for i, item in enumerate(self.items[col]):
            item.set_location(col, i)
            focused = (col == self.focus_col) and (i == self.focus_idx)
            widgets.append(item.get_widget(focused=focused))

        walker = self.listwalkers[col]
        walker[:] = widgets
        if col == self.focus_col:
            walker.set_focus(self.focus_idx)

    def _update_column_headers(self):
        for i, frame in enumerate(self.column_frames):
            attr = "header-focus" if i == self.focus_col else "header"
            title = (
                f"{self.columns[i]}" if i == self.focus_col else self.columns[i]
            )
            frame.header = urwid.AttrMap(
                urwid.Text((attr, f" {title}"), align="center"), attr
            )

    def refresh(self):
        self.widget.focus_position = self.focus_col
        for i, _ in enumerate(self.columns):
            self._refresh_column(i)
        self._update_column_headers()

    #
    # Item management
    #

    def _on_submit(self, data: ItemModel, edit: bool):
        if edit:
            # Update the item.
            item = self.items[self.focus_col][self.focus_idx]
            item.update(data)
        else:
            # Add item the item.
            self.items[self.focus_col].append(
                Item(data, self.tags.get_tag_map())
            )
            self.focus_idx = len(self.items[self.focus_col]) - 1

        self._refresh_column(self.focus_col)
        self.app.flag_changed()
        self.app.pop_widget()

    def _remove_item(self, col: int, idx: int):
        # Remove the item.
        if self.items and (col_items := self.items[col]):
            item = col_items.pop(idx)
            self.deleted.append(item.get_model())
            self.focus_idx = max(min(self.focus_idx, len(col_items) - 1), 0)
            self._refresh_column(col)
            self.app.flag_changed()
        self.app.close_dialog()

    #
    # Item forms
    #

    def create_item(self):
        form = ItemForm(
            self.tags.get_tag_map(),
            on_submit=self._on_submit,
            on_cancel=lambda: self.app.pop_widget(),
        )
        self.app.push_widget(form, ItemForm.STATUS_MSG)

    def edit_item(self):
        if not (current_column := self.items[self.focus_col]):
            return
        current_item = current_column[self.focus_idx]
        form = ItemForm(
            self.tags.get_tag_map(),
            on_submit=self._on_submit,
            on_cancel=lambda: self.app.pop_widget(),
            edit_item=current_item.data,
        )
        self.app.push_widget(form, ItemForm.STATUS_MSG)

    def delete_item(self):
        if not self.items[self.focus_col]:
            return
        options = [
            DialogButtons(
                text="OK",
                on_press=lambda _: self._remove_item(
                    self.focus_col, self.focus_idx
                ),
                keys=["d"],
            ),
            DialogButtons(
                text="Cancel",
                on_press=lambda _: self.app.close_dialog(),
                keys=["esc"],
            ),
        ]
        self.app.open_dialog(
            Dialog("Delete the item?", options),
            ["[d] - delete", "[Esc] - cancel"],
        )

    #
    # Navigation and moving
    #

    def switch_to(self, column: int, index: int):
        self.focus_col = column
        self.focus_idx = index
        self.refresh()

    def switch_item(self, column: int = 0, index: int = 0):
        new_focus_col = self.focus_col + column
        self.focus_col = max(min(new_focus_col, len(self.columns) - 1), 0)

        nitems = len(self.items[self.focus_col])
        new_focus_idx = self.focus_idx + index
        self.focus_idx = max(min(new_focus_idx, nitems - 1), 0)

        self.refresh()

    def move_item(self, column: int = 0, index: int = 0):
        if not self.items[self.focus_col]:
            return

        # Capture the current item and switch to the target position.
        remove_col, remove_idx = self.focus_col, self.focus_idx
        item = self.items[remove_col][remove_idx]
        self.switch_item(column, index)

        #
        # Check that the target position is actually different.  Move.
        # However, if moving to a different column, then put at the top.
        #
        if (remove_col, remove_idx) != (self.focus_col, self.focus_idx):
            self.items[remove_col].pop(remove_idx)
            self.focus_idx = 0 if column else self.focus_idx
            self.items[self.focus_col].insert(self.focus_idx, item)
            item.set_done(done=self.focus_col in self.terminal_columns)
            self.refresh()
            self.app.flag_changed()

    #
    # Other
    #

    def tag_item(self):
        if not (item := self._get_current_item()):
            return
        self.app.open_dialog(
            SetTagDialog(self.app, item.data, self.tags.get_tag_map()),
            ["[Tab] - next", "[Esc] - cancel", "[Enter] - select"],
        )
        self._refresh_column(self.focus_col)

    def _cleanup_items(self):
        # Move the old completed items to 'deleted' list.
        for column, _ in enumerate(self.items):
            to_delete = [
                item.get_model()
                for item in self.items[column]
                if item.data.completed_ago(self.DELETE_COMPLETED)
            ]
            self.items[column] = [
                item
                for item in self.items[column]
                if not item.data.completed_ago(self.DELETE_COMPLETED)
            ]
            self.deleted += to_delete

        # G/C deleted items.
        self.deleted = [
            item_data
            for item_data in self.deleted
            if item_data.completed_at is not None
            and not item_data.completed_ago(self.GC_DELETED)
        ]

    def export(self) -> BoardModel:
        self._cleanup_items()
        return BoardModel(
            columns=[
                ColumnModel(
                    label=column_title,
                    items=[item.get_model() for item in self.items[i]],
                    terminal=(i in self.terminal_columns),
                )
                for i, column_title in enumerate(self.columns)
            ],
            deleted=self.deleted,
        )

    def get_widget(self):
        return self.widget
