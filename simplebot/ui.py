from typing import Iterable, Tuple, Optional, List
from datetime import datetime, date

from simplebot.bot import SimpleBot
from simplebot.router import SimpleRouter
from simplebot.utils import build_callback_data, parse_callback_data
from simplebot.base import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup


class Keyboard:
    __slots__ = ("_layout",)

    def __init__(self, layout: Optional[List] = None):
        self._layout = layout or []

    def add_buttons(self, *buttons, col: int = 1):
        for idx in range(0, len(buttons), col):
            self.add_line(*buttons[idx : idx + col])

    def add_line(self, *buttons):
        self._layout.append(tuple(buttons))

    def add_keyboard(self, keyboard):
        self._layout += keyboard.layout

    @property
    def layout(self):
        return self._layout


class RadioGroup(Keyboard):
    __slots__ = ("_name", "_emoji")

    def __init__(self, name: str, layout: Optional[List] = None, emoji=("🔘", "⚪")):
        self._name = name
        self._emoji = emoji
        if layout:
            for line in layout:
                for button in line:
                    if parse_callback_data(button["callback_data"], name):
                        super().__init__(layout=layout)
                        return
        super().__init__(layout=None)

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
                            self._name,
                            *(option[2:] if option[0] is True else option[1:])
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
                    if button["callback_data"].split("|")[0] != self._name:
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

    @staticmethod
    def set_auto_toggle(router: SimpleRouter, name: str, emoji=("🔘", "⚪")):
        def on_radio_button_click(bot, callback_query, *callback_data_args):
            radio_group = RadioGroup(
                name=name,
                layout=callback_query.message.reply_markup.inline_keyboard,
                emoji=emoji,
            )
            if radio_group.toggle(callback_data_args):
                bot.edit_message_reply_markup(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=radio_group.layout
                    ),
                )

        router.register_callback_query_handler(
            callback=on_radio_button_click,
            callable_match=parse_callback_data,
            name=name,
        )


class MultiSelect(RadioGroup):
    def __init__(self, name: str, layout: Optional[List] = None, emoji=("✔", "")):
        super().__init__(name, layout=layout, emoji=emoji)

    def toggle(self, option_value: Tuple) -> bool:
        target_option = build_callback_data(self._name, *option_value)
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == target_option:
                        if button["text"][0] == self._emoji[0]:
                            button["text"] = button["text"][1:]
                        else:
                            button["text"] = "{0}{1}".format(
                                self._emoji[0], button["text"]
                            )
        return True

    def get_selected(self) -> Tuple:
        selected = []
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == self._emoji[0]:
                    if button["callback_data"].startswith(self._name):
                        selected.append(
                            parse_callback_data(
                                button["callback_data"], name=self._name
                            )
                        )
        return tuple(selected)

    @staticmethod
    def set_auto_toggle(router: SimpleRouter, name: str, emoji=("✔", "")):
        def on_select_button_click(
            bot: SimpleBot, callback_query: CallbackQuery, *callback_data_args
        ):
            mulit_select = MultiSelect(
                name=name,
                layout=callback_query.message.reply_markup.inline_keyboard,
                emoji=emoji,
            )
            mulit_select.toggle(callback_data_args)
            bot.edit_message_reply_markup(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=mulit_select.layout),
            )

        router.register_callback_query_handler(
            callback=on_select_button_click,
            callable_match=parse_callback_data,
            name=name,
        )


class DateTimePicker(RadioGroup):
    def __init__(
        self,
        name: str,
        start_date: str = None,
        end_date: str = None,
        week_start: int = 0,
        format: str = "dd/mm/yyyy",
        disabled_days_of_week=None,
        today_button: bool = True,
        languages=None,
        layout: Optional[List] = None,
        emoji=("⭐", ""),
    ):
        super().__init__(name=name, layout=layout, emoji=emoji)
        self._start_date = (
            datetime.strptime(start_date, format) if start_date else date.today()
        )
        self._end_date = (
            datetime.strptime(end_date, format) if end_date else date.today()
        )
        self._week_start = week_start
        self._format = format
        self._disabled_days_of_week = disabled_days_of_week
        self._today_button = today_button
        self._languages = languages

    def next(self, days=7, col=1):
        pass
