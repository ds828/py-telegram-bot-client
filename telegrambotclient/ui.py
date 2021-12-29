from collections import UserList

from telegrambotclient.base import InlineKeyboardMarkup, ReplyKeyboardMarkup


class ReplyKeyboard(UserList):
    def __init__(self, rows=None):
        super().__init__(rows)

    def add_buttons(self, *buttons, col: int = 1):
        for idx in range(0, len(buttons), col):
            self.append(buttons[idx:idx + col])

    def add_rows(self, *rows):
        self.data += rows

    def markup(self, **kwargs):
        return ReplyKeyboardMarkup(keyboard=self.data, **kwargs)

    def __add__(self, keyboard):
        self.data += keyboard.data
        return self


class InlineKeyboard(ReplyKeyboard):
    def markup(self):
        return InlineKeyboardMarkup(inline_keyboard=self.data)

    def where(self, callback_data: str):
        for row_idx, row in enumerate(self.data):
            for col_idx, button in enumerate(row):
                if button.get("callback_data", "") == callback_data:
                    return row_idx, col_idx
        raise ValueError("{} is not found".format(callback_data))

    def replace(self, callback_data: str, new_button) -> bool:
        try:
            row_idx, col_idx = self.where(callback_data)
            self.data[row_idx][col_idx] = new_button
            return True
        except ValueError:
            return False

    def remove(self, callback_data: str) -> bool:
        try:
            row_idx, col_idx = self.where(callback_data)
            row = self.data[row_idx]
            del row[col_idx]
            if not row:
                del self.data[row_idx]
            return True
        except ValueError:
            return False

    def group(self, callback_data: str):
        buttons = []
        for row in self.data:
            for button in row:
                if button.get("callback_data", "").startswith(callback_data):
                    buttons.append(button)
        return tuple(buttons)
