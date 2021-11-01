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

    def replace(self, callback_data: str, new_button):
        for line in self.data:
            for idx, button in enumerate(line):
                if button.get("callback_data", "") == callback_data:
                    line[idx] = new_button

    def get_button(self, callback_data: str):
        for line in self.data:
            for button in line:
                if button.get("callback_data", "") == callback_data:
                    return button

    def get_buttons(self, callback_data_name: str):
        buttons = []
        for line in self.data:
            for button in line:
                if button.get("callback_data",
                              "").startswith(callback_data_name):
                    buttons.append(button)
        return buttons
