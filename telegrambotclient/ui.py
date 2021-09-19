from typing import Callable, List, Tuple

from telegrambotclient.base import (InlineKeyboardButton, InlineKeyboardMarkup,
                                    KeyboardButton, ReplyKeyboardMarkup,
                                    TelegramBotException)
from telegrambotclient.router import TelegramRouter
from telegrambotclient.utils import build_callback_data, parse_callback_data

_RADIO_EMOJI = ("🔘", "⚪")
_SELECT_EMOJI = ("✔️", "")
_SWITCH_EMOJI = ("✔️", "❌")


class Select:
    @classmethod
    def setup(cls,
              router: TelegramRouter,
              name: str,
              callback: Callable = None,
              emoji=_SELECT_EMOJI):
        def on_changed(bot, callback_query, changed_value):
            if callback_query.from_user and callback_query.message:
                changed_data = build_callback_data(name, changed_value)
                selected, changed_text, keyboard_layout = cls.change_keyboard(
                    callback_query.message.reply_markup.inline_keyboard,
                    changed_data,
                    emoji=emoji)
                message_text = callback(bot, callback_query, changed_text,
                                        changed_value,
                                        selected) if callback else None
                if callback_query.message.text:
                    bot.edit_message_text(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        text=message_text or callback_query.message.text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=keyboard_layout),
                    )
                else:
                    bot.edit_message_reply_markup(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=keyboard_layout),
                    )

        router.register_callback_query_handler(
            callback=on_changed,
            callback_data_name=name,
        )

    @classmethod
    def change_keyboard(cls,
                        keyboard_layout,
                        changed_data: str,
                        emoji=_SELECT_EMOJI):
        len_emoji_selected = len(emoji[0])
        len_emoji_unselected = len(emoji[1])
        for line in keyboard_layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == changed_data:
                        # if it is selected
                        if button["text"][:len_emoji_selected] == emoji[0]:
                            button["text"] = "{0}{1}".format(
                                emoji[1], button["text"]
                                [len_emoji_selected:])  # make it unselect
                            return False, button["text"][
                                len_emoji_unselected:], keyboard_layout
                        # otherwise make it select
                        if button["text"][:len_emoji_unselected] == emoji[1]:
                            button["text"] = "{0}{1}".format(
                                emoji[0],
                                button["text"][len_emoji_unselected:])
                            return True, button["text"][
                                len_emoji_selected:], keyboard_layout
        raise TelegramBotException(
            "the option: {0} is not found".format(changed_data))

    @classmethod
    def build_buttons(cls,
                      name: str,
                      *options,
                      emoji=_SELECT_EMOJI) -> List[InlineKeyboardButton]:
        buttons = []
        # option: (text, value, selected: optional)
        for option in options:
            buttons.append(
                InlineKeyboardButton(text="{0}{1}".format(
                    emoji[0] if len(option) == 3 and option[2] is True else
                    emoji[1], option[0]),
                                     callback_data=build_callback_data(
                                         name, option[1])))
        return buttons

    @classmethod
    def lookup(cls, keyboard_layout, name: str, emoji=_SELECT_EMOJI) -> Tuple:
        len_emoji_selected = len(emoji[0])
        selected_options = []
        for line in keyboard_layout:
            for button in line:
                if "callback_data" in button and button[
                        "text"][:len_emoji_selected] == emoji[0]:
                    if button["callback_data"].startswith(name):
                        selected_options.append(
                            (button["text"][len_emoji_selected:],
                             parse_callback_data(button["callback_data"],
                                                 name=name)[0]))
        return tuple(selected_options)


class Radio(Select):
    @classmethod
    def setup(cls,
              router: TelegramRouter,
              name: str,
              callback: Callable = None,
              emoji=_RADIO_EMOJI):
        def on_changed(bot, callback_query, changed_value):
            changed_data = build_callback_data(name, changed_value)
            print(changed_data)
            changed, changed_text, keyboard_layout = cls.change_keyboard(
                callback_query.message.reply_markup.inline_keyboard,
                name,
                changed_data,
                emoji=emoji)
            if changed and callback_query.message and callback_query.from_user:
                message_text = callback(bot, callback_query, changed_text,
                                        changed_value) if callback else None
                if callback_query.message.text:
                    bot.edit_message_text(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        text=message_text or callback_query.message.text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=keyboard_layout),
                    )
                else:
                    bot.edit_message_reply_markup(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=keyboard_layout),
                    )

        router.register_callback_query_handler(callback=on_changed,
                                               callback_data_name=name)

    @classmethod
    def build_buttons(cls,
                      name: str,
                      *options,
                      emoji=_RADIO_EMOJI) -> List[InlineKeyboardButton]:
        return Select.build_buttons(name, *options, emoji=emoji)

    @classmethod
    def change_keyboard(cls,
                        keyboard_layout,
                        name: str,
                        changed_data: str,
                        emoji=_RADIO_EMOJI) -> Tuple:
        len_emoji_selected = len(emoji[0])
        len_emoji_unselected = len(emoji[1])
        changed_text = None
        for line in keyboard_layout:
            for button in line:
                # the button is a inline button
                if "callback_data" in button:
                    # it is a radio I want
                    if button["callback_data"].split("|")[0] == name:
                        # it is the radio I click
                        if button["callback_data"] == changed_data:
                            if button["text"][:len_emoji_selected] == emoji[0]:
                                # click on the same button
                                return None, None, None
                            changed_text = button["text"][
                                len_emoji_unselected:]
                            button["text"] = "{0}{1}".format(
                                emoji[0], button["text"]
                                [len_emoji_unselected:])  # make it select

                        # make others be unselected
                        elif button["text"][:len_emoji_selected] == emoji[0]:
                            button["text"] = "{0}{1}".format(
                                emoji[1], button["text"][len_emoji_selected:])
        return True, changed_text, keyboard_layout

    @classmethod
    def lookup(cls, keyboard_layout, name: str, emoji=_RADIO_EMOJI) -> Tuple:
        len_emoji_selected = len(emoji[0])
        for line in keyboard_layout:
            for button in line:
                if "callback_data" in button and button[
                        "text"][:len_emoji_selected] == emoji[0]:
                    if button["callback_data"].startswith(name):
                        return button["text"][
                            len_emoji_selected:], parse_callback_data(
                                button["callback_data"], name)[0] or None
        return None, None


class Switch(Select):
    @classmethod
    def setup(cls,
              router: TelegramRouter,
              name: str,
              callback: Callable = None,
              emoji=_SWITCH_EMOJI):
        def on_changed(bot, callback_query, value):
            if callback_query.message or callback_query.from_user:
                status, text, keyboard_layout = cls.change_keyboard(
                    callback_query.message.reply_markup.inline_keyboard,
                    name,
                    emoji=emoji)
                message_text = callback(bot, callback_query, value,
                                        status) if callback else None
                if callback_query.message.text:
                    bot.edit_message_text(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        text=message_text or callback_query.message.text,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=keyboard_layout),
                    )
                else:
                    bot.edit_message_reply_markup(
                        chat_id=callback_query.from_user.id,
                        message_id=callback_query.message.message_id,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=keyboard_layout),
                    )

        router.register_callback_query_handler(
            callback=on_changed,
            callback_data_name=name,
        )

    @classmethod
    def change_keyboard(cls,
                        keyboard_layout: List,
                        name: str,
                        emoji=_SWITCH_EMOJI) -> Tuple:
        len_emoji_0 = len(emoji[0])
        for line in keyboard_layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"].startswith(name):
                        value = parse_callback_data(button["callback_data"],
                                                    name)[0]
                        if button["text"][:len_emoji_0] == emoji[
                                0]:  # status is checked
                            # make it be unchecked
                            button["text"] = "{0}{1}".format(
                                emoji[1], button["text"][len_emoji_0:])
                            return False, value or None, keyboard_layout
                        # otherwise make it be checked
                        button["text"] = "{0}{1}".format(
                            emoji[0], button["text"][len(emoji[1]):])
                        return True, value or None, keyboard_layout
        raise TelegramBotException("switch: {0} is not found".format(name))

    @classmethod
    def build_button(cls,
                     name: str,
                     text: str,
                     value=None,
                     status: bool = False,
                     emoji=_SWITCH_EMOJI) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text="{0}{1}".format(emoji[0] if status else emoji[1], text),
            callback_data=build_callback_data(name, value) if value else name)

    @classmethod
    def lookup(cls, keyboard_layout, name: str, emoji=_SWITCH_EMOJI):
        len_emoji_0 = len(emoji[0])
        for line in keyboard_layout:
            for button in line:
                if "callback_data" in button:
                    if button["callback_data"] == name:
                        return button["text"][:len_emoji_0] == emoji[0]
                    if button["callback_data"].startswith(name):
                        return button["text"][:len_emoji_0] == emoji[
                            0], parse_callback_data(button["callback_data"],
                                                    name)[0]

        raise TelegramBotException("switch: {0} is not found".format(name))


class UIHelper:
    @staticmethod
    def setup_select(router: TelegramRouter,
                     name: str,
                     callback: Callable = None,
                     emoji=_SELECT_EMOJI):
        Select.setup(router, name, callback, emoji=emoji)

    @staticmethod
    def build_select_buttons(
            name: str,
            *options,
            emoji=_SELECT_EMOJI) -> List[InlineKeyboardButton]:
        return Select.build_buttons(name, *options, emoji=emoji)

    @staticmethod
    def lookup_select(keyboard_layout: List,
                      name: str,
                      emoji=_SELECT_EMOJI) -> Tuple:
        return Select.lookup(keyboard_layout, name, emoji=emoji)

    @staticmethod
    def setup_radio(router: TelegramRouter,
                    name: str,
                    callback: Callable = None,
                    emoji=_RADIO_EMOJI):
        Radio.setup(router, name, callback, emoji=emoji)

    @staticmethod
    def build_radio_buttons(name: str,
                            *options,
                            emoji=_RADIO_EMOJI) -> List[InlineKeyboardButton]:
        return Radio.build_buttons(name, *options, emoji=emoji)

    @staticmethod
    def lookup_radio(keyboard_layout: List, name: str, emoji=_RADIO_EMOJI):
        return Radio.lookup(keyboard_layout, name, emoji=emoji)

    @staticmethod
    def setup_switch(router: TelegramRouter,
                     name: str,
                     callback: Callable = None,
                     emoji=_SWITCH_EMOJI):
        Switch.setup(router, name, callback, emoji=emoji)

    @staticmethod
    def build_switch_button(name: str,
                            text: str,
                            value=None,
                            status: bool = False,
                            emoji=_SWITCH_EMOJI) -> InlineKeyboardButton:
        return Switch.build_button(name,
                                   text,
                                   value=value,
                                   status=status,
                                   emoji=emoji)

    @staticmethod
    def lookup_switch(keyboard_layout: List, name: str, emoji=_SWITCH_EMOJI):
        return Switch.lookup(keyboard_layout, name, emoji=emoji)


class ReplyKeyboard:
    __slots__ = ("_layout", )

    def __init__(self, *buttons, col=1, layout=None):
        self._layout = layout or []
        self.add_buttons(*buttons, col=col)

    def __add__(self, keyboard):
        return ReplyKeyboard(layout=self._layout + keyboard._layout)

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
    def __add__(self, keyboard):
        return InlineKeyboard(layout=self._layout + keyboard._layout)

    def markup(self):
        return InlineKeyboardMarkup(inline_keyboard=self._layout)
