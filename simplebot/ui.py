<<<<<<< HEAD
<<<<<<< HEAD
from typing import Iterable, Tuple, Optional, List
=======
from typing import Callable, Iterable, Tuple, Optional, List
from datetime import datetime, date
>>>>>>> dev
=======
from typing import Callable, Tuple, Optional, List
>>>>>>> dev

from simplebot.bot import SimpleBot
from simplebot.router import SimpleRouter
from simplebot.utils import build_callback_data, parse_callback_data
from simplebot.base import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    SimpleBotException,
)

_RADIO_EMOJI = ("🔘", "⚪")
_SELECT_EMOJI = ("✔", "")
_TOGGLER_EMOJI = ("🔓", "🔒")


class ReplyKeyboard:
    __slots__ = ("_layout",)

    def __init__(self, keyboard: Optional[List] = None):
        self._layout = keyboard or []

    def add_buttons(self, *buttons, col: int = 1):
        for idx in range(0, len(buttons), col):
            self.add_line(*buttons[idx : idx + col])

    def add_line(self, *buttons):
        self._layout.append(tuple(buttons))

    def delete_line(self, line_idx: int):
        del self._layout[line_idx]

    def delete_button(self, line_idx: int, col_idx: int):
        del self._layout[line_idx][col_idx]

    def replace_button(self, line_idx: int, col_idx: int, button: KeyboardButton):
        self._layout[line_idx][col_idx] = button

    def markup(self, **kwargs):
        return ReplyKeyboardMarkup(keyboard=self._layout, **kwargs)


class InlineKeyboard(ReplyKeyboard):

    def __init__(self, keyboard: Optional[List] = None):
        super().__init__(keyboard=keyboard)

    def markup(self, **kwargs):
        return InlineKeyboardMarkup(inline_keyboard=self._layout)

    def has_button(self, name: str):
        for line in self._layout:
            for button in line:
                if button["callback_data"].split("|")[0] == name:
                    return True
        return False

    def add_radio_group(self, name: str, *options, col: int = 1, emoji=_RADIO_EMOJI):
        # option: (text, value, selected: optional)
        for idx in range(0, len(options), col):
            self._layout.append(
                [
                    InlineKeyboardButton(
                        text="{0}{1}".format(
                            emoji[0]
                            if len(option) == 3 and option[2] is True
                            else emoji[1],
                            option[0],
                        ),
                        callback_data=build_callback_data(name, option[1]),
                    )
                    for option in options[idx : idx + col]
                ]
            )

    def delete_radio_group(self, name: str):
        for line_idx, line in enumerate(self._layout):
            for btn_idx, button in enumerate(line):
                # the button is a inlinebutton
                if "callback_data" in button:
                    if button["callback_data"].split("|")[0] == name:
                        del self._layout[line_idx][btn_idx]


    def get_radio_value(self, name: str, emoji=_RADIO_EMOJI) -> Optional[Tuple]:
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == emoji[0]:
                    if button["callback_data"].startswith(name):
                        return parse_callback_data(button["callback_data"], name)[0]
        return None

    def change_radio_status(
        self, name: str, option, emoji=_RADIO_EMOJI
    ) -> bool:
        changed = False
        clicked_option = build_callback_data(name, option)
        for line in self._layout:
            for button in line:
                # the button is a inlinebutton
                if "callback_data" in button:
                    # it is a radio
                    if button["text"][0] in emoji:
                        # it is a radio I want
                        if button["callback_data"].split("|")[0] == name:
                            # it is the radio I click
                            if button["callback_data"] == clicked_option:
                                if button["text"][0] == emoji[0]:
                                    return False
                                button["text"] = "{0}{1}".format(
                                    emoji[0], button["text"][1:]
                                )  # make it select
                                changed = True
                            else:
                                if button["text"][0] == emoji[0]:
                                    button["text"] = "{0}{1}".format(
                                        emoji[1], button["text"][1:]
                                    )
        return changed

    @staticmethod
    def auto_radio(
        router: SimpleRouter,
        name: str,
        radio_changed_callback: Optional[Callable] = None,
        emoji=_RADIO_EMOJI,
    ):
        def on_radio_click(bot, callback_query, radio_option):
            keyboard = InlineKeyboard(
                keyboard=callback_query.message.reply_markup.inline_keyboard,
            )
            if keyboard.change_radio_status(name, radio_option, emoji=emoji):
                if radio_changed_callback:
                    radio_changed_callback(bot, callback_query, radio_option)
                bot.edit_message_reply_markup(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    reply_markup=keyboard.markup(),
                )

        router.register_callback_query_handler(
            callback=on_radio_click, callback_query_name=name
        )

    def add_select_group(self, name: str, *options, col: int = 1, emoji=_SELECT_EMOJI):
        self.add_radio_group(name, *options, col=col, emoji=emoji)

    def get_select_value(self, name: str, emoji=_SELECT_EMOJI) -> Tuple:
        selected_options = []
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == emoji[0]:
                    if button["callback_data"].startswith(name):
                        selected_options.append(
                            parse_callback_data(button["callback_data"], name=name)[0]
                        )
        return tuple(selected_options)

    def change_select_status(self, name: str, option, emoji=_SELECT_EMOJI):
        toggled_option = build_callback_data(name, option)
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == toggled_option:
                        if button["text"][0] == emoji[0]:  # selected
                            button["text"] = button["text"][1:]  # make it unselect
                            return False
                        # otherwise make it select
                        button["text"] = "{0}{1}".format(emoji[0], button["text"])
                        return True
        raise SimpleBotException("the option: {0} is not found".format(toggled_option))

    @staticmethod
    def auto_select(
        router: SimpleRouter,
        name: str,
        selected_callback: Optional[Callable] = None,
        unselected_callback: Optional[Callable] = None,
        emoji=_SELECT_EMOJI,
    ):
        def on_select_click(
            bot: SimpleBot, callback_query: CallbackQuery, clicked_option
        ):
            keyboard = InlineKeyboard(
                keyboard=callback_query.message.reply_markup.inline_keyboard,
            )
            selected = keyboard.change_select_status(name, clicked_option, emoji)
            if selected:
                if selected_callback:
                    selected_callback(bot, callback_query, clicked_option)
            elif unselected_callback:
                unselected_callback(bot, callback_query, clicked_option)
            bot.edit_message_reply_markup(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                reply_markup=keyboard.markup(),
            )

        router.register_callback_query_handler(
            callback=on_select_click,
            callback_query_name=name,
        )

<<<<<<< HEAD
class Toggler(RadioGroup):
    _emoji = ("😀", "🙁")

    def __init__(
        self,
        name: str,
        option_value: Optional[Tuple] = None,
        layout: Optional[Iterable] = None,
        emoji: Optional[Tuple] = None,
    ):
        super().__init__(name=name, layout=layout, emoji=emoji)
        if option_value:
            self.add_options(option_value)

    def toggle(self, option_value: Tuple) -> bool:
        target_option = build_callback_data(self._name, *option_value)
=======
    def add_toggler(self, name: str, checked: bool = True, emoji=_TOGGLER_EMOJI):
        select_emoji = emoji[1]
        if checked:
            select_emoji = emoji[0]
        self.add_buttons(
            InlineKeyboardButton(
                text="{0}{1}".format(select_emoji, name), callback_data=name
            )
        )

    def toggle(self, name, emoji=_TOGGLER_EMOJI) -> bool:
>>>>>>> dev
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == name:
                        if button["text"][0] == emoji[0]:  # status is checked
                            # make it be unchecked
                            button["text"] = "{0}{1}".format(emoji[1], name)
                            return False
                        # otherwise make it be checked
                        button["text"] = "{0}{1}".format(emoji[0], name)
                        return True
        raise SimpleBotException("toggler name: {0} is not found".format(name))

    def get_toggler_value(self, name: str, emoji=_TOGGLER_EMOJI):
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == name:
                        return button["text"][0] == emoji[0]
        raise SimpleBotException("toggler name: {0} is not found".format(name))

    @staticmethod
    def auto_toggle(
        router: SimpleRouter,
        name: str,
        toggle_on_callback: Optional[Callable] = None,
        toggle_off_callback: Optional[Callable] = None,
        emoji=_TOGGLER_EMOJI,
    ):
        def on_toggle_click(
            bot: SimpleBot, callback_query: CallbackQuery
        ):
            keyboard = InlineKeyboard(
                keyboard=callback_query.message.reply_markup.inline_keyboard,
            )
            checked = keyboard.toggle(name, emoji)
            if checked:
                if toggle_on_callback:
                    toggle_on_callback(
                        bot,
                        callback_query,
                    )
            elif toggle_off_callback:
                toggle_off_callback(bot, callback_query)
            bot.edit_message_reply_markup(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                reply_markup=keyboard.markup(),
            )

        router.register_callback_query_handler(
            callback=on_toggle_click,
            static_match=name,
        )
