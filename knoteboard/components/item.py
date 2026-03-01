import urwid

from knoteboard.models import ItemModel
from knoteboard.utils import date_parse


class Item:
    """
    An item - ticket or note.  The abstraction wraps the data and provides
    the widget, including the item's current state.
    """

    data: ItemModel

    def __init__(self, data: ItemModel):
        self.data = data

    def update(self, data: ItemModel):
        data.created_at = self.data.created_at
        self.data = data

    @property
    def color(self):
        return "yellow"  # default

    @property
    def done(self):
        return bool(self.data.completed_at)

    def get_model(self) -> ItemModel:
        return self.data

    def get_widget(self, focused: bool = False):
        bar = urwid.AttrMap(urwid.Text(" "), self.color)
        item_attr = "item-focus" if focused else "item"
        label = urwid.Text((item_attr, self.data.title))
        item = urwid.Columns([("fixed", 1, bar), label], dividechars=1)
        return urwid.LineBox(item)


class DateEdit(urwid.WidgetWrap):
    """
    Date field.  Implements parsing and validation of the date.
    """

    def __init__(self, date=None):
        self.date = date
        self._edit = urwid.Edit(edit_text=self._get_date_text() if date else "")
        self._hint = urwid.Text(("field-label", ""))

        edit_map = urwid.AttrMap(self._edit, "field-box", "field-box-focus")
        pile = urwid.Pile([edit_map, self._hint])
        super().__init__(pile)

    @property
    def edit_text(self):
        return self._edit.edit_text

    def keypress(self, size, key):
        result = self._w.keypress(size, key)
        self._update_hint()
        return result

    def _get_date_text(self):
        return self.date.strftime("%Y-%m-%d (%a) %H:%M")

    def _update_hint(self):
        if (text := self.edit_text) and len(text.strip()) >= 3:
            self.date = date_parse(text)
            if self.date:
                date_text = self._get_date_text()
                attr, msg = ("date-ok", f"✓ {date_text}")
            else:
                attr, msg = ("date-err", "✗ Invalid date")
        else:
            attr, msg = ("field-label", "")
            self.date = None
        self._hint.set_text((attr, msg))

    def get_date(self):
        return self.date

    def is_invalid(self):
        return self.edit_text and not self.date

    def selectable(self):
        return True


class ItemForm(urwid.WidgetWrap):
    """
    A form to create or edit a new item (ticket/note).
    """

    STATUS_MSG = ["[Tab] - next field", "[Enter] - submit", "[Esc] - cancel"]

    def __init__(
        self, on_submit, on_cancel, edit_item: ItemModel | None = None
    ):
        self._on_submit = on_submit
        self._on_cancel = on_cancel
        self.edit = bool(edit_item)

        self._title_edit = urwid.Edit(
            edit_text=edit_item.title if edit_item else ""
        )
        self._desc_edit = urwid.Edit(
            edit_text=edit_item.description if edit_item else "", multiline=True
        )
        self._date_edit = DateEdit(edit_item.date if edit_item else None)

        title_map = urwid.AttrMap(
            self._title_edit, "field-box", "field-box-focus"
        )
        desc_map = urwid.AttrMap(
            urwid.BoxAdapter(
                urwid.ListBox(urwid.SimpleFocusListWalker([self._desc_edit])),
                height=15,
            ),
            "field-box",
            "field-box-focus",
        )

        btn_ok = urwid.AttrMap(
            urwid.Button("OK", align="center"), "btn", "btn-focus"
        )
        btn_cancel = urwid.AttrMap(
            urwid.Button("Cancel", align="center"), "btn", "btn-focus"
        )
        buttons = urwid.Columns(
            [
                ("weight", 1, urwid.Padding(btn_ok, "center", width=10)),
                ("weight", 1, urwid.Padding(btn_cancel, "center", width=10)),
            ]
        )

        #
        # Focusable items (in their order).
        #
        self._items = urwid.SimpleFocusListWalker(
            [
                self._labeled("Title", title_map),
                self._labeled("Description", desc_map),
                self._labeled("Target date", self._date_edit),
                urwid.Divider(),
                buttons,
            ]
        )

        #
        # Form.
        #
        form_body = urwid.LineBox(
            urwid.AttrMap(
                urwid.Padding(urwid.ListBox(self._items), left=1, right=1),
                "form-bg",
            ),
            title="EDIT ITEM" if self.edit else "ADD ITEM",
            title_attr="form-title",
        )
        overlay = urwid.Overlay(
            urwid.AttrMap(form_body, "form-bg"),
            urwid.SolidFill(" "),
            align="center",
            width=("relative", 60),
            valign="middle",
            height=("relative", 60),
            min_width=30,
            min_height=20,
        )
        super().__init__(overlay)

    @staticmethod
    def _labeled(label, widget):
        return urwid.Pile(
            [
                urwid.Text(("field-label", label)),
                urwid.LineBox(widget),
            ]
        )

    def _submit(self):
        if self._date_edit.is_invalid():
            return  # invalid date, keep the form open

        if not self._title_edit.edit_text.strip():
            return  # invalid title

        item = ItemModel(
            title=self._title_edit.edit_text,
            description=self._desc_edit.edit_text,
            date=self._date_edit.get_date(),
        )
        self._on_submit(item, self.edit)

    def keypress(self, size, key):
        match key:
            case "esc":
                self._on_cancel()
                return
            case "enter":
                self._submit()
            case "tab":
                idx = self._items.focus
                self._items.set_focus((idx + 1) % len(self._items))
            case "shift tab":
                idx = self._items.focus
                self._items.set_focus((idx - 1) % len(self._items))
            case _:
                return self._w.keypress(size, key)

    def selectable(self):
        return True
