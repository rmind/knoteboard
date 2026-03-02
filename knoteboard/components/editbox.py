import urwid


class EditBox(urwid.Edit):
    """
    An edit widget with Emacs-like key bindings.
    """

    def keypress(self, size, key):
        match key:
            #
            # Navigation
            #
            case "ctrl a":
                sol = self.edit_text.rfind("\n", 0, self.edit_pos)
                self.edit_pos = sol + 1 if sol != -1 else 0
            case "ctrl e":
                eol = self.edit_text.find("\n", self.edit_pos)
                self.edit_pos = eol if eol != -1 else len(self.edit_text)
            case "ctrl b":
                return super().keypress(size, "left")
            case "ctrl f":
                return super().keypress(size, "right")
            case "ctrl p":
                return super().keypress(size, "up")
            case "ctrl n":
                return super().keypress(size, "down")

            #
            # Deletion
            #
            case "ctrl w":
                i = self.edit_pos
                text = self.edit_text
                while i > 0 and text[i - 1].isspace():
                    i -= 1  # first, skip trailing whitespaces
                while i > 0 and not text[i - 1].isspace():
                    i -= 1  # then, skip the actual word
                self.edit_text = text[:i] + text[self.edit_pos :]
                self.edit_pos = i
            case "ctrl d":
                if (pos := self.edit_pos) < len(self.edit_text):
                    self.edit_text = (
                        self.edit_text[:pos] + self.edit_text[pos + 1 :]
                    )
            case "ctrl k":
                pos = self.edit_pos
                eol = self.edit_text.find("\n", pos)
                self.edit_text = (
                    self.edit_text[:pos]
                    if eol == -1
                    else self.edit_text[:pos] + self.edit_text[eol:]
                )
                self.edit_pos = pos
            case _:
                return super().keypress(size, key)
