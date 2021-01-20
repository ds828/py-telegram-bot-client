try:
    import ujson as json
except ImportError:
    import json
from typing import Iterable, Tuple, Optional, List
from simplebot.utils import build_callback_data
from simplebot.base import InlineKeyboardButton


class Keyboard:
    __slots__ = ("_layout",)

    def __init__(self, layout: Optional[List] = None):
        self._layout = layout or []

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
        super().__init__(layout=layout)
        self._name = name
        self._emoji = emoji

    def add_options(self, *options: Iterable, col: int = 1):
        for idx in range(0, len(options), col):
            self._layout.append(
                [
                    InlineKeyboardButton(
                        text="{0}{1}".format(
                            self._emoji[0]
                            if len(option) == 3 and option[2] is True
                            else self._emoji[1],
                            option[0],
                        ),
                        callback_data=build_callback_data(
                            self._name,
                            option[1],
                        ),
                    )
                    for option in options[idx : idx + col]
                ]
            )

    def toggle(self, option: Tuple) -> bool:
        toggled = False
        toggled_option = build_callback_data(self._name, option)
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["text"][0] not in self._emoji:
                        continue
                    name, _ = json.loads(button["callback_data"])
                    if name != self._name:
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

    @property
    def selected_option(self) -> Optional[Tuple]:
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == self._emoji[0]:
                    name, option = json.loads(button["callback_data"])
                    if name == self._name:
                        return option
        return None


class MultiSelect(RadioGroup):
    def __init__(self, name: str, layout: Optional[List] = None, emoji=("✔", "")):
        super().__init__(name, layout=layout, emoji=emoji)

    def toggle(self, option: Tuple) -> bool:
        target_option = build_callback_data(self._name, option)
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == target_option:
                        if button["text"][0] == self._emoji[0]:
                            button["text"] = option[0]
                        else:
                            button["text"] = "{0}{1}".format(self._emoji[0], button["text"])
        return True

    @property
    def selected_options(self) -> Tuple:
        selected = []
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == self._emoji[0]:
                    name, option = json.loads(button["callback_data"])
                    if name == self._name:
                        selected.append(option)
        return tuple(selected)
