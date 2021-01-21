from typing import Iterable, Tuple, Optional, List
from simplebot.utils import build_callback_data, parse_callback_data
from simplebot.base import InlineKeyboardButton


class Keyboard:
    __slots__ = ("_layout", "_buttons")

    def __init__(self, layout: Optional[List] = None):
        self._layout = layout or []
        self._buttons = []

    def add_buttons(self, *buttons, col: int = 1):
        for idx in range(0, len(buttons), col):
            self.add_line(*buttons[idx : idx + col])

    def add_line(self, *buttons):
        self._layout.append(tuple(buttons))

    def add_layout(self, layout: List):
        self._layout += layout

    @property
    def layout(self):
        return self._layout


class RadioGroup(Keyboard):
    __slots__ = ("_name", "_emoji")

    def __init__(self, name: str, layout: Optional[List] = None, emoji=("🔘", "⚪")):
        super(RadioGroup, self).__init__(layout=layout)
        self._name = name
        self._emoji = emoji

    def add_options(self, *options: Iterable, col: int = 1):
        for idx in range(0, len(options), col):
            self._layout.append(
                [
                    InlineKeyboardButton(
                        text="{0}{1}".format(
                            self._emoji[0] if option[0] is True else self._emoji[1],
                            option[1] if option[0] is True else option[0],
                        ),
                        callback_data=build_callback_data(
                            self._name, *(option[2:] if option[0] is True else option[1:])
                        ),
                    )
                    for option in options[idx : idx + col]
                ]
            )

    def toggle(self, option_value: tuple) -> bool:
        toggled = False
        toggled_option = build_callback_data(self._name, *option_value)
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["text"][0] not in self._emoji:
                        continue
                    if not button["callback_data"].startswith(self._name):
                        continue
                    if button["callback_data"] == toggled_option:
                        if button["text"][0] == self._emoji[1]:  # unselected
                            button["text"] = "{0}{1}".format(
                                self._emoji[0], button["text"][1:]
                            )  # selected
                            toggled = True
                        else:
                            return False
                    elif button["text"][0] == self._emoji[0]:
                        button["text"] = "{0}{1}".format(
                            self._emoji[1], button["text"][1:]
                        )  # unselected

        return toggled

    def get_selected(self) -> Optional[Tuple]:
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == self._emoji[0]:
                    if button["callback_data"].startswith(self._name):
                        return parse_callback_data(button["callback_data"], self._name)
        return None


class MultiSelect(RadioGroup):
    def __init__(self, name: str, layout: Optional[List] = None, emoji=("✔", "")):
        super(MultiSelect, self).__init__(name, layout=layout, emoji=emoji)

    def toggle(self, option_value: Tuple) -> bool:
        target_option = build_callback_data(self._name, *option_value)
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == target_option:
                        if button["text"][0] == self._emoji[0]:
                            button["text"] = button["text"][1:]
                        else:
                            button["text"] = "{0}{1}".format(self._emoji[0], button["text"])
        return True

    def get_selected(self) -> Tuple:
        selected = []
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == self._emoji[0]:
                    if button["callback_data"].startswith(self._name):
                        selected.append(
                            parse_callback_data(button["callback_data"], name=self._name)
                        )
        return tuple(selected)
