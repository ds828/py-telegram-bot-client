from typing import Callable, List, Optional, Tuple

from telegrambotclient.api import TelegramBotAPIException
from telegrambotclient.base import (CallbackQuery, InlineKeyboardButton,
                                    InlineKeyboardMarkup, KeyboardButton,
                                    ReplyKeyboardMarkup, TelegramBotException)
from telegrambotclient.bot import TelegramBot
from telegrambotclient.router import TelegramRouter
from telegrambotclient.utils import build_callback_data, parse_callback_data

_RADIO_EMOJI = ("🔘", "⚪")
_SELECT_EMOJI = ("✔", "")
_TOGGLER_EMOJI = ("🔓", "🔒")


class ReplyKeyboard:
    __slots__ = ("_layout", )

    def __init__(self, keyboard: Optional[List] = None):
        self._layout = keyboard or []

    def add_buttons(self, *buttons, col: int = 1):
        for idx in range(0, len(buttons), col):
            self.add_line(*buttons[idx:idx + col])

    def add_line(self, *buttons):
        self._layout.append(tuple(buttons))

    def delete_line(self, line_idx: int):
        del self._layout[line_idx]

    def delete_button(self, line_idx: int, col_idx: int):
        del self._layout[line_idx][col_idx]

    def replace_button(self, line_idx: int, col_idx: int,
                       button: KeyboardButton):
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
                if "callback_data" in button:
                    callback_query_name_arg = button["callback_data"].split(
                        "|")
                    if callback_query_name_arg and callback_query_name_arg[
                            0] == name:
                        return True
        return False

    def add_radio_group(self,
                        name: str,
                        *options,
                        col: int = 1,
                        emoji=_RADIO_EMOJI):
        # option: (text, value, selected: optional)
        for idx in range(0, len(options), col):
            self._layout.append([
                InlineKeyboardButton(
                    text="{0}{1}".format(
                        emoji[0] if len(option) == 3 and option[2] is True else
                        emoji[1],
                        option[0],
                    ),
                    callback_data=build_callback_data(name, option[1]),
                ) for option in options[idx:idx + col]
            ])

    def delete_radio_group(self, name: str):
        for line_idx, line in enumerate(self._layout):
            for btn_idx, button in enumerate(line):
                # the button is a inlinebutton
                if "callback_data" in button:
                    if button["callback_data"].split("|")[0] == name:
                        del self._layout[line_idx][btn_idx]

    def get_radio_value(self,
                        name: str,
                        emoji=_RADIO_EMOJI) -> Optional[Tuple]:
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == emoji[0]:
                    if button["callback_data"].startswith(name):
                        return button["text"][1:], parse_callback_data(
                            button["callback_data"], name)[0]
        return None, None

    def change_radio_status(self,
                            name: str,
                            option,
                            emoji=_RADIO_EMOJI) -> Optional[str]:
        changed_item_name = None
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
                                    return None
                                changed_item_name = button["text"][1:]
                                button["text"] = "{0}{1}".format(
                                    emoji[0],
                                    button["text"][1:])  # make it select
                            else:
                                # make others be unselected
                                if button["text"][0] == emoji[0]:
                                    button["text"] = "{0}{1}".format(
                                        emoji[1], button["text"][1:])
        return changed_item_name

    @staticmethod
    def auto_radio(
        router: TelegramRouter,
        name: str,
        changed_callback: Optional[Callable] = None,
        emoji=_RADIO_EMOJI,
    ):
        def on_radio_click(bot, callback_query, changed_radio_option):
            keyboard = InlineKeyboard(
                keyboard=callback_query.message.reply_markup.inline_keyboard, )
            changed_radio_text = keyboard.change_radio_status(
                name, changed_radio_option, emoji=emoji)
            if changed_radio_text:
                message_text = changed_callback(
                    bot, callback_query, changed_radio_text,
                    changed_radio_option) if changed_callback else None
                if callback_query.message.text:
                    bot.edit_message_text(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        text=message_text or callback_query.message.text,
                        reply_markup=keyboard.markup(),
                    )
                else:
                    bot.edit_message_reply_markup(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        reply_markup=keyboard.markup(),
                    )

        router.register_callback_query_handler(callback=on_radio_click,
                                               callback_data_name=name)

    def add_select_group(self,
                         name: str,
                         *options,
                         col: int = 1,
                         emoji=_SELECT_EMOJI):
        self.add_radio_group(name, *options, col=col, emoji=emoji)

    def get_select_value(self, name: str, emoji=_SELECT_EMOJI) -> Tuple:
        selected_options = []
        for line in self._layout:
            for button in line:
                if "callback_data" in button and button["text"][0] == emoji[0]:
                    if button["callback_data"].startswith(name):
                        selected_options.append(
                            (button["text"][1:],
                             parse_callback_data(button["callback_data"],
                                                 name=name)[0]))
        return tuple(selected_options)

    def change_select_status(self, name: str, option, emoji=_SELECT_EMOJI):
        toggled_option = build_callback_data(name, option)
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == toggled_option:
                        if button["text"][0] == emoji[0]:  # selected
                            button["text"] = button["text"][
                                1:]  # make it unselect
                            return False, button["text"]
                        # otherwise make it select
                        button["text"] = "{0}{1}".format(
                            emoji[0], button["text"])
                        return True, button["text"][1:]
        raise TelegramBotException(
            "the option: {0} is not found".format(toggled_option))

    @staticmethod
    def auto_select(
        router: TelegramRouter,
        name: str,
        clicked_callback: Optional[Callable] = None,
        emoji=_SELECT_EMOJI,
    ):
        def on_select_click(bot: TelegramBot, callback_query: CallbackQuery,
                            clicked_option):
            keyboard = InlineKeyboard(
                keyboard=callback_query.message.reply_markup.inline_keyboard, )
            selected, clicked_text = keyboard.change_select_status(
                name, clicked_option, emoji)
            message_text = clicked_callback(
                bot, callback_query, clicked_text, clicked_option,
                selected) if clicked_callback else None
            if callback_query.message.text:
                bot.edit_message_text(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    text=message_text or callback_query.message.text,
                    reply_markup=keyboard.markup(),
                )
            else:
                bot.edit_message_reply_markup(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    reply_markup=keyboard.markup(),
                )

        router.register_callback_query_handler(
            callback=on_select_click,
            callback_data_name=name,
        )

    def add_toggler(self,
                    name: str,
                    option=None,
                    toggle_status: bool = True,
                    emoji=_TOGGLER_EMOJI):
        select_emoji = emoji[0] if toggle_status else emoji[1]
        self.add_buttons(
            InlineKeyboardButton(text="{0}{1}".format(select_emoji, name),
                                 callback_data=build_callback_data(
                                     name, option)))

    def toggle(self, name, emoji=_TOGGLER_EMOJI) -> bool:
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"].startswith(name):
                        if button["text"][0] == emoji[0]:  # status is checked
                            # make it be unchecked
                            button["text"] = "{0}{1}".format(emoji[1], name)
                            return False
                        # otherwise make it be checked
                        button["text"] = "{0}{1}".format(emoji[0], name)
                        return True
        raise TelegramBotException(
            "toggler name: {0} is not found".format(name))

    def get_toggler_value(self, name: str, emoji=_TOGGLER_EMOJI):
        for line in self._layout:
            for button in line:
                if "callback_data" in button:
                    callback_data = button["callback_data"]
                    if callback_data.startswith(name):
                        return button["text"][0] == emoji[
                            0], parse_callback_data(callback_data, name)[0]
        raise TelegramBotException(
            "toggler name: {0} is not found".format(name))

    @staticmethod
    def auto_toggle(
        router: TelegramRouter,
        name: str,
        toggled_callback: Optional[Callable] = None,
        emoji=_TOGGLER_EMOJI,
    ):
        def on_toggle_click(bot: TelegramBot, callback_query: CallbackQuery,
                            toggle_option):
            keyboard = InlineKeyboard(
                keyboard=callback_query.message.reply_markup.inline_keyboard, )
            toggle_status = keyboard.toggle(name, emoji)
            message_text = toggled_callback(
                bot, callback_query, toggle_option,
                toggle_status) if toggled_callback else None
            if callback_query.message.text:
                bot.edit_message_text(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    text=message_text or callback_query.message.text,
                    reply_markup=keyboard.markup(),
                )
            else:
                bot.edit_message_reply_markup(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    reply_markup=keyboard.markup(),
                )

        router.register_callback_query_handler(
            callback=on_toggle_click,
            callback_data_name=name,
        )

    def add_confirm_buttons(self,
                            name: str,
                            callback_data,
                            ok_text: str = "OK",
                            cancel_text: str = "Cancel",
                            col: int = 2,
                            auto_cancel: bool = False):
        self.add_buttons(
            InlineKeyboardButton(text=ok_text,
                                 callback_data=build_callback_data(
                                     name, True, callback_data)),
            InlineKeyboardButton(
                text=cancel_text,
                callback_data=build_callback_data(
                    "cancel-{0}".format(name) if auto_cancel else name, False,
                    callback_data)),
            col=col)

    @staticmethod
    def auto_cancel(
        router: TelegramRouter,
        name: str,
        cancel_callback: Optional[Callable] = None,
    ):
        def on_cancel_click(bot: TelegramBot, callback_query: CallbackQuery,
                            confirm: bool, cancel_callback_data):
            if cancel_callback:
                cancel_callback(bot, callback_query, confirm,
                                cancel_callback_data)
            try:
                bot.delete_message(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id)
            except TelegramBotAPIException:
                pass

        router.register_callback_query_handler(
            callback=on_cancel_click,
            callback_data_name="cancel-{0}".format(name),
        )
