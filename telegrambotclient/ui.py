from collections import UserList

from telegrambotclient.base import InlineKeyboardMarkup, ReplyKeyboardMarkup


class ReplyKeyboard(UserList):
    def __init__(self, *lines):
        super().__init__(lines)

    def add_buttons(self, *buttons, col: int = 1):
        for idx in range(0, len(buttons), col):
            self.append(buttons[idx:idx + col])

    def add_lines(self, *lines):
        self.data += lines

    def markup(self, **kwargs):
        return ReplyKeyboardMarkup(keyboard=self.data, **kwargs)

    def __add__(self, keyboard):
        self.data += keyboard.data
        return self


class InlineKeyboard(ReplyKeyboard):
    def markup(self):
        return InlineKeyboardMarkup(inline_keyboard=self.data)

    def replace(self, callback_data: str, new_button) -> bool:
        replaced = False
        for row in self.data:
            for idx, button in enumerate(row):
                if "callback_data" in button and button[
                        "callback_data"] == callback_data:
                    if button["text"] != new_button.text or button[
                            "callback_data"] != new_button.callback_data:
                        row[idx] = new_button
                        replaced = True
        return replaced

    def remove(self, callback_data: str):
        removed = False
        for row in self.data:
            for button in row:
                if button.get("callback_data", "") == callback_data:
                    row.remove(button)
                    removed = True
        if [] in self.data:
            self.data.remove([])
        return removed

    def where(self, callback_data: str):
        for row_idx, row in enumerate(self.data):
            for col_idx, button in enumerate(row):
                if button.get("callback_data", "") == callback_data:
                    return row_idx, col_idx
        raise ValueError("{} is not found".format(callback_data))
